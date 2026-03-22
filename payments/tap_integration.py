"""
Tap Payments integration for MEA region.

Uses Tap Charge API with Card SDK v2 for tokenization.
Test keys from https://developers.tap.company/reference/testing-keys
"""

from __future__ import annotations

import logging
from decimal import Decimal

import httpx
from django.conf import settings
from django.urls import reverse

from .models import Payment, Purchase
from .fulfillment import fulfill_payment
from .email_utils import send_payment_invoice

logger = logging.getLogger(__name__)

TAP_API_BASE = 'https://api.tap.company/v2'


def _get_secret_key():
    key = getattr(settings, 'TAP_SECRET_KEY', '') or ''
    if not key:
        raise ValueError('TAP_SECRET_KEY is not configured.')
    return key


def _get_merchant_id():
    mid = getattr(settings, 'TAP_MERCHANT_ID', '') or ''
    if not mid:
        raise ValueError('TAP_MERCHANT_ID is not configured.')
    return mid


def create_charge(payment: Payment, token_id: str, redirect_url: str) -> dict:
    """
    Create a Tap charge with card token.

    Args:
        payment: Our Payment record
        token_id: Tap token from Card SDK (tok_xxx)
        redirect_url: URL to redirect after payment (success or 3DS return)

    Returns:
        Charge API response dict with transaction.url for 3DS redirect if needed
    """
    key = _get_secret_key()
    merchant_id = _get_merchant_id()

    # Amount in smallest unit (halalas for SAR/KWD, cents for USD)
    amount = float(payment.amount)
    currency = payment.currency or 'USD'
    amount_smallest = int(amount * 100)  # 100 per unit for USD, SAR, etc.

    payload = {
        'amount': amount_smallest,
        'currency': currency,
        'customer_initiated': True,
        'source': {'id': token_id},
        'redirect': {'url': redirect_url},
        'reference': {'transaction': f'pay-{payment.id}'},
        'metadata': {'payment_id': str(payment.id)},
    }

    if merchant_id:
        payload['merchant'] = {'id': merchant_id}

    resp = httpx.post(
        f'{TAP_API_BASE}/charges/',
        json=payload,
        headers={
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_charge(charge_id: str) -> dict:
    """Fetch charge details from Tap API."""
    key = _get_secret_key()
    resp = httpx.get(
        f'{TAP_API_BASE}/charges/{charge_id}',
        headers={'Authorization': f'Bearer {key}'},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def handle_tap_callback(tap_id: str, our_payment_id: int) -> tuple:
    """
    Handle return from Tap (redirect URL with tap_id).

    Fetches charge from Tap, verifies status, fulfills order.
    Returns (Payment, Purchase or None).
    """
    data = fetch_charge(tap_id)
    status = data.get('status', '').upper()
    transaction = data.get('transaction', {})

    payment = Payment.objects.filter(pk=our_payment_id).first()
    if not payment:
        raise ValueError(f'Payment {our_payment_id} not found')

    payment.provider_payment_id = tap_id
    payment.provider_session_id = tap_id
    payment.save()

    if status == 'CAPTURED' or status == 'DECLINED':
        # CAPTURED = success, DECLINED = failed
        if status == 'CAPTURED':
            payment.status = 'succeeded'
            payment.save()
            purchase = fulfill_payment(payment)
            try:
                send_payment_invoice(payment)
            except Exception as e:
                logger.error(f'Failed to send payment invoice: {e}')
            return payment, purchase
        else:
            payment.status = 'failed'
            payment.save()
            return payment, None

    # Pending/Authorized - check transaction status
    tx_status = transaction.get('status', '').upper()
    if tx_status in ('CAPTURED', 'CAPTURE'):
        payment.status = 'succeeded'
        payment.save()
        purchase = fulfill_payment(payment)
        try:
            send_payment_invoice(payment)
        except Exception as e:
            logger.error(f'Failed to send payment invoice: {e}')
        return payment, purchase

    if tx_status in ('DECLINED', 'FAILED', 'ABORTED'):
        payment.status = 'failed'
        payment.save()
        return payment, None

    return payment, None
