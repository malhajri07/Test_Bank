"""
Paylink payment gateway integration.

API docs: https://developer.paylink.sa/docs/payment-getting-started

Flow:
1. Authenticate → get id_token
2. Create invoice (addInvoice) → get payment URL + transactionNo
3. Customer pays on Paylink hosted page
4. Customer returns to callBackUrl → verify via getInvoice
"""

import logging
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

# Token cache (in-memory; refreshed every 25 minutes to stay within 30-min window)
_token_cache = {
    'token': None,
    'expires_at': 0,
}


def _get_base_url():
    return getattr(settings, 'PAYLINK_BASE_URL', 'https://restpilot.paylink.sa').rstrip('/')


def authenticate():
    """
    Authenticate with Paylink and return an id_token.

    Uses short-lived tokens (persistToken=false → 30 minutes).
    Caches the token to avoid re-authenticating on every request.
    """
    import time

    now = time.time()
    if _token_cache['token'] and now < _token_cache['expires_at']:
        return _token_cache['token']

    base_url = _get_base_url()
    url = f'{base_url}/api/auth'

    payload = {
        'apiId': settings.PAYLINK_APP_ID,
        'secretKey': settings.PAYLINK_SECRET_KEY,
        'persistToken': False,
    }

    resp = httpx.post(url, json=payload, headers={
        'accept': 'application/json',
        'content-type': 'application/json',
    }, timeout=15)

    resp.raise_for_status()
    data = resp.json()
    token = data.get('id_token')

    if not token:
        raise ValueError('Paylink auth response missing id_token')

    # Cache for 25 minutes (token valid for 30)
    _token_cache['token'] = token
    _token_cache['expires_at'] = now + 25 * 60

    logger.info('Paylink auth token obtained')
    return token


def create_invoice(
    order_number,
    amount,
    callback_url,
    cancel_url,
    client_name,
    client_email,
    client_mobile,
    products,
    currency=None,
    note=None,
):
    """
    Create a Paylink invoice and return the response dict.

    Args:
        order_number: Unique order/payment ID string
        amount: Total amount (float/Decimal)
        callback_url: URL customer returns to after payment
        cancel_url: URL customer returns to if they cancel
        client_name: Customer full name
        client_email: Customer email
        client_mobile: Customer phone (e.g. '0512345678')
        products: List of dicts with keys: title, price, qty
        currency: Currency code (default from settings, usually SAR)
        note: Optional note

    Returns:
        dict with keys: transactionNo, url, orderStatus, checkUrl, etc.
    """
    token = authenticate()
    base_url = _get_base_url()
    url = f'{base_url}/api/addInvoice'

    if currency is None:
        currency = getattr(settings, 'PAYLINK_CURRENCY', 'SAR')

    payload = {
        'orderNumber': str(order_number),
        'amount': float(amount),
        'callBackUrl': callback_url,
        'cancelUrl': cancel_url,
        'clientName': client_name or 'Customer',
        'clientEmail': client_email or '',
        'clientMobile': client_mobile or '0500000000',
        'currency': currency,
        'products': [
            {
                'title': p['title'],
                'price': float(p['price']),
                'qty': int(p.get('qty', 1)),
                'description': p.get('description', ''),
                'isDigital': p.get('is_digital', True),
            }
            for p in products
        ],
        'supportedCardBrands': [
            'mada', 'visaMastercard', 'amex', 'stcpay', 'urpay', 'tabby', 'tamara',
        ],
        'displayPending': True,
    }

    if note:
        payload['note'] = note

    resp = httpx.post(url, json=payload, headers={
        'Authorization': f'Bearer {token}',
        'accept': 'application/json',
        'content-type': 'application/json',
    }, timeout=30)

    if resp.status_code != 200:
        logger.error(
            'Paylink addInvoice failed: status=%s body=%s',
            resp.status_code, resp.text[:500],
        )
        resp.raise_for_status()

    data = resp.json()

    if not data.get('success') and not data.get('transactionNo'):
        error = data.get('paymentErrors') or data.get('message') or 'Unknown error'
        raise ValueError(f'Paylink addInvoice failed: {error}')

    logger.info(
        'Paylink invoice created: transactionNo=%s, status=%s',
        data.get('transactionNo'),
        data.get('orderStatus'),
    )
    return data


def get_invoice(transaction_no):
    """
    Retrieve invoice status from Paylink.

    Args:
        transaction_no: The transactionNo returned by create_invoice

    Returns:
        dict with orderStatus ('Pending', 'Paid', 'Canceled'), amount, paymentReceipt, etc.
    """
    token = authenticate()
    base_url = _get_base_url()
    url = f'{base_url}/api/getInvoice/{transaction_no}'

    resp = httpx.get(url, headers={
        'Authorization': f'Bearer {token}',
        'accept': 'application/json',
        'content-type': 'application/json',
    }, timeout=15)

    resp.raise_for_status()
    return resp.json()
