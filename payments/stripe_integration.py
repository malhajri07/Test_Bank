"""
Stripe payment integration utilities.

This module provides functions for:
- Creating Stripe Checkout sessions
- Verifying webhook signatures (security critical)
- Processing successful payments
- Handling payment callbacks

Security Considerations:
- Always verify webhook signatures to ensure requests are from Stripe
- Never trust client-only data for payment status
- Use server-side verification for all payment operations
"""

import logging
import os

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.urls import reverse

from .email_utils import send_payment_invoice
from .fulfillment import fulfill_payment
from .models import Coupon, Order, OrderItem, Payment, ProcessedWebhookEvent, Purchase

logger = logging.getLogger(__name__)


def _ensure_stripe_configured():
    """Lazily configure Stripe API key on first use, avoiding module-level crashes."""
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError('STRIPE_SECRET_KEY is not configured. Please set it in your .env file.')
    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.proxy = None


def _make_stripe_request(func, *args, **kwargs):
    """
    Helper function to make Stripe API calls with proxy bypass.
    
    Temporarily disables proxy environment variables and ensures Stripe doesn't use proxy.
    """
    # Save current proxy settings
    original_proxies = {}
    proxy_keys = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    
    for key in proxy_keys:
        if key in os.environ:
            original_proxies[key] = os.environ[key]
            del os.environ[key]
    
    # Set NO_PROXY to include Stripe domains
    original_no_proxy = os.environ.get('NO_PROXY', '')
    os.environ['NO_PROXY'] = f"{original_no_proxy},api.stripe.com,*.stripe.com" if original_no_proxy else 'api.stripe.com,*.stripe.com'
    
    # Ensure Stripe proxy is None
    original_stripe_proxy = getattr(stripe, 'proxy', None)
    stripe.proxy = None
    
    try:
        # Make the Stripe API call
        return func(*args, **kwargs)
    finally:
        # Restore proxy settings
        for key, value in original_proxies.items():
            os.environ[key] = value
        # Restore NO_PROXY
        if original_no_proxy:
            os.environ['NO_PROXY'] = original_no_proxy
        elif 'NO_PROXY' in os.environ and 'stripe.com' in os.environ['NO_PROXY']:
            # Remove Stripe from NO_PROXY if we added it
            no_proxy_list = [x for x in os.environ['NO_PROXY'].split(',') if 'stripe.com' not in x.lower()]
            if no_proxy_list:
                os.environ['NO_PROXY'] = ','.join(no_proxy_list)
            else:
                del os.environ['NO_PROXY']
        # Restore Stripe proxy setting
        stripe.proxy = original_stripe_proxy


def create_checkout_session(test_bank, user, request, order=None, discount_amount=None, coupon=None, ui_mode='hosted'):
    """
    Create a Stripe Checkout session for purchasing a test bank.

    Optionally uses Order for cart-based flow and applies discount from promo code.

    Args:
        test_bank: TestBank instance to purchase
        user: User instance making the purchase
        request: Django HttpRequest object (for building absolute URLs)
        order: Optional Order instance (creates Order+OrderItem if not provided)
        discount_amount: Optional Decimal discount (from promo code)
        ui_mode: 'hosted' for redirect-based checkout

    Returns:
        str: Stripe Checkout session URL
    """
    _ensure_stripe_configured()

    if test_bank.price <= 0:
        raise ValueError('Test bank price must be greater than 0')

    from decimal import Decimal
    discount_amount = discount_amount or Decimal('0')
    amount_after_discount = max(Decimal('0'), test_bank.price - discount_amount)

    if order is None:
        order = Order.objects.create(
            user=user,
            subtotal=test_bank.price,
            discount_amount=discount_amount,
            currency=settings.STRIPE_CURRENCY,
            coupon=coupon,
        )
        OrderItem.objects.create(
            order=order,
            test_bank=test_bank,
            quantity=1,
            unit_price=test_bank.price,
        )
        vat_rate = Decimal(str(getattr(settings, 'VAT_RATE', 0.15)))
        order.tax_amount = (amount_after_discount * vat_rate).quantize(Decimal('0.01'))
        order.total_amount = (amount_after_discount + order.tax_amount).quantize(Decimal('0.01'))
        order.save()

    payment = Payment.objects.create(
        user=user,
        order=order,
        test_bank=test_bank,
        amount=amount_after_discount,
        currency=settings.STRIPE_CURRENCY,
        payment_provider='stripe',
        status='created',
    )
    
    # Build success and cancel URLs
    success_url = request.build_absolute_uri(
        reverse('payments:payment_success')
    ) + f'?session_id={{CHECKOUT_SESSION_ID}}'
    
    cancel_url = request.build_absolute_uri(
        reverse('payments:payment_cancel')
    )
    
    # Prepare description
    description = test_bank.description or ''
    if len(description) > 500:
        description = description[:500]
    
    # Create Stripe Checkout session parameters
    session_params = {
        'payment_method_types': ['card'],
        'line_items': [{
            'price_data': {
                'currency': settings.STRIPE_CURRENCY,
                'product_data': {
                    'name': test_bank.title,
                    'description': description,
                },
                'unit_amount': int(float(amount_after_discount) * 100),  # Convert to cents
            },
            'quantity': 1,
        }],
        'mode': 'payment',
        'success_url': success_url,
        'cancel_url': cancel_url,
        'client_reference_id': str(payment.id),
        'metadata': {
            'payment_id': str(payment.id),
            'order_id': str(order.id),
            'test_bank_id': str(test_bank.id),
            'user_id': str(user.id),
        }
    }
    
    try:
        # Create Stripe Checkout session (with proxy bypass)
        checkout_session = _make_stripe_request(
            stripe.checkout.Session.create,
            **session_params
        )
        
        # Update Payment with Stripe session ID
        payment.provider_session_id = checkout_session.id
        payment.status = 'pending'
        payment.save()
        
        return checkout_session.url
        
    except Exception as e:
        # Check if it's a Stripe error (handle AttributeError from Stripe library)
        error_type = type(e).__name__
        is_stripe_error = (
            'stripe' in str(type(e)).lower() or
            'Stripe' in error_type or
            'APIConnectionError' in error_type or
            hasattr(e, '__class__') and 'stripe' in str(e.__class__.__module__).lower()
        )
        
        # Update payment status to failed if it's a Stripe-related error
        if is_stripe_error:
            payment.status = 'failed'
            payment.save()
        
        raise e


def create_checkout_session_for_package(exam_package, user, request, discount_amount=None, coupon=None):
    """
    Create Stripe Checkout session for purchasing an exam package.

    Creates Order with one OrderItem per test bank, applies package discount,
    and redirects to Stripe Checkout.
    """
    from decimal import Decimal

    _ensure_stripe_configured()

    test_banks = list(exam_package.test_banks.filter(is_active=True))
    if not test_banks:
        raise ValueError('Package has no active test banks')

    retail = sum(tb.price for tb in test_banks)
    discount_amount = discount_amount or Decimal('0')
    package_discount = max(Decimal('0'), retail - exam_package.package_price)
    total_discount = discount_amount + package_discount
    amount_after_discount = max(Decimal('0'), retail - total_discount)

    order = Order.objects.create(
        user=user,
        subtotal=retail,
        discount_amount=total_discount,
        currency=settings.STRIPE_CURRENCY,
        coupon=coupon,
    )
    for tb in test_banks:
        OrderItem.objects.create(
            order=order,
            test_bank=tb,
            quantity=1,
            unit_price=tb.price,
        )

    vat_rate = Decimal(str(getattr(settings, 'VAT_RATE', 0.15)))
    order.tax_amount = (amount_after_discount * vat_rate).quantize(Decimal('0.01'))
    order.total_amount = (amount_after_discount + order.tax_amount).quantize(Decimal('0.01'))
    order.save()

    payment = Payment.objects.create(
        user=user,
        order=order,
        test_bank=test_banks[0],
        amount=amount_after_discount,
        currency=settings.STRIPE_CURRENCY,
        payment_provider='stripe',
        status='created',
    )

    success_url = request.build_absolute_uri(reverse('payments:payment_success')) + f'?session_id={{CHECKOUT_SESSION_ID}}'
    cancel_url = request.build_absolute_uri(reverse('payments:payment_cancel'))

    desc = exam_package.description or ''
    if len(desc) > 500:
        desc = desc[:500]

    session_params = {
        'payment_method_types': ['card'],
        'line_items': [{
            'price_data': {
                'currency': settings.STRIPE_CURRENCY,
                'product_data': {
                    'name': f'Package: {exam_package.title}',
                    'description': desc,
                },
                'unit_amount': int(float(amount_after_discount) * 100),
            },
            'quantity': 1,
        }],
        'mode': 'payment',
        'success_url': success_url,
        'cancel_url': cancel_url,
        'client_reference_id': str(payment.id),
        'metadata': {
            'payment_id': str(payment.id),
            'order_id': str(order.id),
            'user_id': str(user.id),
        },
    }

    checkout_session = _make_stripe_request(stripe.checkout.Session.create, **session_params)
    payment.provider_session_id = checkout_session.id
    payment.status = 'pending'
    payment.save()
    return checkout_session.url


def verify_webhook_signature(request):
    """
    Verify that a webhook request is actually from Stripe.
    
    This is CRITICAL for security - never process webhooks without verification.
    Stripe signs webhook payloads with a secret, and we verify the signature
    to ensure the request is authentic.
    
    Args:
        request: Django HttpRequest object containing webhook payload
    
    Returns:
        dict: Verified webhook event object
    
    Raises:
        ValueError: If signature verification fails
    """
    _ensure_stripe_configured()

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        raise ValueError('Missing Stripe signature header')
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise ValueError('STRIPE_WEBHOOK_SECRET not configured')
    
    try:
        # Verify webhook signature (no HTTP request needed)
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError as e:
        raise ValueError(f'Invalid webhook payload: {e}')
    except Exception as e:
        # Handle SignatureVerificationError or AttributeError from Stripe
        error_type = type(e).__name__
        if 'SignatureVerificationError' in error_type or 'Signature' in error_type:
            raise ValueError(f'Invalid webhook signature: {e}')
        else:
            raise


def handle_payment_success(session_id):
    """
    Handle successful payment from Stripe Checkout.
    
    This function:
    1. Retrieves Stripe session to verify payment
    2. Finds corresponding Payment record
    3. Updates Payment status to 'succeeded'
    4. Creates Purchase record
    5. Creates UserTestAccess to grant user access
    
    Args:
        session_id: Stripe Checkout Session ID
    
    Returns:
        tuple: (Payment instance, Purchase instance)
    
    Raises:
        Payment.DoesNotExist: If payment record not found
        Exception: If Stripe API call fails (handles AttributeError from network issues)
    """
    _ensure_stripe_configured()

    try:
        # Retrieve Stripe session (with proxy bypass)
        checkout_session = _make_stripe_request(
            stripe.checkout.Session.retrieve,
            session_id
        )

        # Lock the payment row so concurrent webhook/success calls can't race.
        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(
                    provider_session_id=session_id
                )
            except Payment.DoesNotExist:
                raise Payment.DoesNotExist(f'Payment not found for session {session_id}')

            if payment.status == 'succeeded':
                return payment, payment.purchases.order_by('id').first()

            payment.status = 'succeeded'
            pi = checkout_session.payment_intent
            if pi:
                payment.provider_payment_id = pi if isinstance(pi, str) else getattr(pi, 'id', None)
            payment.save()

            fulfill_payment(payment)

        # Email outside the DB transaction — don't hold the lock over network I/O
        try:
            send_payment_invoice(payment)
        except Exception as e:
            logger.error(f'Failed to send payment invoice email: {str(e)}')

        return payment, payment.purchases.order_by('id').first()
    except Exception as e:
        # Re-raise any exceptions (will be handled by views)
        raise e


def handle_webhook_event(event):
    """
    Handle Stripe webhook events with idempotency and refund support.

    Events handled:
    - checkout.session.completed       → fulfill payment
    - payment_intent.succeeded         → fulfill payment
    - payment_intent.payment_failed    → mark failed
    - payment_intent.canceled          → mark cancelled
    - charge.refunded                  → revoke access

    Returns:
        tuple: (Payment or None, Purchase or None)
    """
    event_id = event.get('id')
    event_type = event['type']
    event_data = event['data']['object']

    # Idempotency guard — first-write-wins on (provider, event_id).
    if event_id:
        try:
            ProcessedWebhookEvent.objects.create(
                provider='stripe',
                event_id=event_id,
                event_type=event_type,
            )
        except IntegrityError:
            logger.info(f'Duplicate Stripe event {event_id} ({event_type}) ignored')
            return None, None

    if event_type == 'checkout.session.completed':
        session_id = event_data['id']
        return handle_payment_success(session_id)

    if event_type == 'payment_intent.succeeded':
        payment_intent_id = event_data['id']
        try:
            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(
                    provider_payment_id=payment_intent_id
                )
                if payment.status == 'succeeded':
                    return payment, payment.purchases.order_by('id').first()
                payment.status = 'succeeded'
                payment.save()
                fulfill_payment(payment)
            try:
                send_payment_invoice(payment)
            except Exception as e:
                logger.error(f'Failed to send payment invoice email: {str(e)}')
            return payment, payment.purchases.order_by('id').first()
        except Payment.DoesNotExist:
            logger.warning(f'payment_intent.succeeded for unknown PI {payment_intent_id}')
            return None, None

    if event_type == 'payment_intent.payment_failed':
        payment_intent_id = event_data['id']
        try:
            payment = Payment.objects.get(provider_payment_id=payment_intent_id)
            payment.status = 'failed'
            payment.save()
            return payment, None
        except Payment.DoesNotExist:
            return None, None

    if event_type == 'payment_intent.canceled':
        payment_intent_id = event_data['id']
        try:
            payment = Payment.objects.get(provider_payment_id=payment_intent_id)
            payment.status = 'cancelled'
            payment.save()
            return payment, None
        except Payment.DoesNotExist:
            return None, None

    if event_type == 'charge.refunded':
        payment_intent_id = event_data.get('payment_intent')
        if payment_intent_id:
            try:
                payment = Payment.objects.get(provider_payment_id=payment_intent_id)
                _handle_refund(payment)
                return payment, None
            except Payment.DoesNotExist:
                logger.warning(f'charge.refunded for unknown PI {payment_intent_id}')

    return None, None


def _handle_refund(payment):
    """
    Process a refund: mark order refunded, deactivate Purchase and UserTestAccess.

    Does NOT delete records — preserves audit trail. Access is revoked by flipping
    is_active=False on Purchase and UserTestAccess rows.
    """
    from practice.models import UserTestAccess

    with transaction.atomic():
        if payment.order:
            payment.order.status = 'refunded'
            payment.order.save(update_fields=['status', 'updated_at'])

        for purchase in payment.purchases.all():
            purchase.is_active = False
            purchase.save(update_fields=['is_active'])

            UserTestAccess.objects.filter(
                user=purchase.user,
                test_bank=purchase.test_bank,
            ).update(is_active=False)

    logger.info(f'Refund processed for payment {payment.id} → access revoked')
