"""
Tests for payments.reconciliation — the shared verify+fulfill helper used by
both the customer-return callback and the poll_pending_payments command.
"""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Category, TestBank
from payments import reconciliation
from payments.models import Payment, Purchase


User = get_user_model()


class ReconcilePaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('u', 'u@t.com', 'p')
        self.category = Category.objects.create(name='Cat', slug='cat')
        self.test_bank = TestBank.objects.create(
            category=self.category,
            title='Bank',
            slug='bank',
            description='d',
            price=Decimal('10.00'),
            is_active=True,
        )

    def _make_pending_payment(self, session='tx123'):
        return Payment.objects.create(
            user=self.user,
            test_bank=self.test_bank,
            amount=Decimal('10.00'),
            currency='SAR',
            payment_provider='paylink',
            status='pending',
            provider_session_id=session,
        )

    @patch('payments.reconciliation.get_invoice')
    def test_paid_invoice_marks_succeeded_and_fulfills(self, mock_get_invoice):
        mock_get_invoice.return_value = {
            'orderStatus': 'Paid',
            'paymentReceipt': {
                'paymentMethod': 'MADA',
                'bankCardNumber': '************1234',
                'receiptUrl': 'https://r.example/abc',
            },
        }
        payment = self._make_pending_payment()

        with patch('payments.email_utils.send_payment_invoice'):
            result = reconciliation.reconcile_payment(payment)

        self.assertEqual(result, reconciliation.PAID)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'succeeded')
        self.assertEqual(payment.card_last_four, '1234')
        self.assertEqual(payment.payment_method, 'MADA')
        self.assertTrue(
            Purchase.objects.filter(payment=payment, test_bank=self.test_bank).exists()
        )

    @patch('payments.reconciliation.get_invoice')
    def test_canceled_invoice_marks_cancelled(self, mock_get_invoice):
        mock_get_invoice.return_value = {'orderStatus': 'Canceled'}
        payment = self._make_pending_payment()

        result = reconciliation.reconcile_payment(payment)

        self.assertEqual(result, reconciliation.CANCELLED)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'cancelled')
        self.assertFalse(Purchase.objects.filter(payment=payment).exists())

    @patch('payments.reconciliation.get_invoice')
    def test_pending_invoice_does_not_mutate(self, mock_get_invoice):
        mock_get_invoice.return_value = {'orderStatus': 'Pending'}
        payment = self._make_pending_payment()

        result = reconciliation.reconcile_payment(payment)

        self.assertEqual(result, reconciliation.PENDING)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'pending')

    @patch('payments.reconciliation.get_invoice')
    def test_already_succeeded_is_idempotent(self, mock_get_invoice):
        payment = self._make_pending_payment()
        payment.status = 'succeeded'
        payment.save()

        result = reconciliation.reconcile_payment(payment)

        self.assertEqual(result, reconciliation.ALREADY_PROCESSED)
        mock_get_invoice.assert_not_called()

    @patch('payments.reconciliation.get_invoice')
    def test_missing_session_short_circuits(self, mock_get_invoice):
        payment = self._make_pending_payment(session='')

        result = reconciliation.reconcile_payment(payment)

        self.assertEqual(result, reconciliation.MISSING_SESSION)
        mock_get_invoice.assert_not_called()

    @patch('payments.reconciliation.get_invoice', side_effect=RuntimeError('boom'))
    def test_gateway_error_returns_error_and_preserves_status(self, _mock):
        payment = self._make_pending_payment()

        result = reconciliation.reconcile_payment(payment)

        self.assertEqual(result, reconciliation.ERROR)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'pending')

    @patch('payments.reconciliation.get_invoice')
    def test_double_reconcile_only_fulfills_once(self, mock_get_invoice):
        mock_get_invoice.return_value = {
            'orderStatus': 'Paid',
            'paymentReceipt': {},
        }
        payment = self._make_pending_payment()

        with patch('payments.email_utils.send_payment_invoice'):
            first = reconciliation.reconcile_payment(payment)
            # Second call simulates the job racing with the customer callback.
            second = reconciliation.reconcile_payment(payment)

        self.assertEqual(first, reconciliation.PAID)
        self.assertEqual(second, reconciliation.ALREADY_PROCESSED)
        self.assertEqual(
            Purchase.objects.filter(payment=payment, test_bank=self.test_bank).count(),
            1,
        )
