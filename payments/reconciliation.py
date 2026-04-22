"""
Payment reconciliation — single source of truth for verifying a pending Paylink
payment against the gateway and running fulfillment.

Shared by:
- The customer-return callback view (payments.views.paylink_callback)
- The poll_pending_payments management command (safety net for customers who
  never return to the callback URL)
"""

import logging

from django.db import transaction

from .fulfillment import fulfill_payment
from .models import Payment
from .paylink_integration import get_invoice

logger = logging.getLogger(__name__)


PAID = 'paid'
CANCELLED = 'cancelled'
PENDING = 'pending'
ALREADY_PROCESSED = 'already_processed'
MISSING_SESSION = 'missing_session'
ERROR = 'error'


def reconcile_payment(payment):
    """
    Verify a payment's status with Paylink and fulfill it if paid.

    Safe to call multiple times on the same payment — uses select_for_update
    to serialize concurrent callers and checks terminal status first.

    Returns one of the module-level result constants.
    """
    with transaction.atomic():
        # Re-fetch with a row lock so concurrent callers (customer callback +
        # reconciliation job) don't both try to fulfill the same payment.
        # of=('self',) restricts the row lock to the Payment table so the
        # nullable joins (order, test_bank) don't trip the Postgres rule that
        # FOR UPDATE can't sit on the nullable side of an outer join.
        locked = (
            Payment.objects
            .select_related('order', 'test_bank', 'user')
            .select_for_update(of=('self',))
            .get(pk=payment.pk)
        )

        if locked.status in ('succeeded', 'failed', 'cancelled'):
            return ALREADY_PROCESSED

        if not locked.provider_session_id:
            return MISSING_SESSION

        try:
            invoice_data = get_invoice(locked.provider_session_id)
        except Exception:
            logger.error(
                'Paylink getInvoice failed for payment %s',
                locked.pk,
                exc_info=True,
            )
            return ERROR

        order_status = (invoice_data.get('orderStatus') or '').lower()

        if order_status == 'paid':
            receipt = invoice_data.get('paymentReceipt') or {}
            locked.provider_payment_id = locked.provider_session_id
            locked.status = 'succeeded'
            locked.payment_method = receipt.get('paymentMethod', '')
            locked.card_last_four = (receipt.get('bankCardNumber', '') or '')[-4:]
            locked.receipt_url = receipt.get('receiptUrl', '')
            locked.save()

            purchase = fulfill_payment(locked)

            if purchase:
                # Import locally to avoid a circular import at module load.
                from .email_utils import send_payment_invoice
                try:
                    send_payment_invoice(locked)
                except Exception:
                    logger.warning(
                        'Failed to send invoice email for payment %s',
                        locked.pk,
                        exc_info=True,
                    )

            # Reflect the new state back onto the caller's instance so
            # downstream code (view messages, redirects) sees fresh fields.
            payment.refresh_from_db()
            return PAID

        if order_status == 'canceled':
            locked.status = 'cancelled'
            locked.save()
            payment.refresh_from_db()
            return CANCELLED

        return PENDING
