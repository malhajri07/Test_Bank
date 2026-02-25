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

import stripe
import os
from django.conf import settings
from django.urls import reverse
from .models import Payment, Purchase
from practice.models import UserTestAccess
from .email_utils import send_payment_invoice


# Initialize Stripe with secret key from settings
if not settings.STRIPE_SECRET_KEY:
    raise ValueError('STRIPE_SECRET_KEY is not configured. Please set it in your .env file.')

stripe.api_key = settings.STRIPE_SECRET_KEY

# Configure Stripe to bypass proxy
# Set proxy to None explicitly in Stripe configuration
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


def create_checkout_session(test_bank, user, request, ui_mode='hosted'):
    """
    Create a Stripe Checkout session for purchasing a test bank.
    
    This function:
    1. Creates a Payment record with status='created'
    2. Creates a Stripe Checkout session
    3. Updates Payment with Stripe session ID
    4. Returns the checkout session URL
    
    Args:
        test_bank: TestBank instance to purchase
        user: User instance making the purchase
        request: Django HttpRequest object (for building absolute URLs)
        ui_mode: 'hosted' for redirect-based checkout (only mode currently supported)
    
    Returns:
        str: Stripe Checkout session URL
    
    Raises:
        ValueError: If test bank price is invalid
        stripe.error.StripeError: If Stripe API call fails
    """
    # Validate test bank price
    if test_bank.price <= 0:
        raise ValueError('Test bank price must be greater than 0')
    
    # Create Payment record with initial status
    payment = Payment.objects.create(
        user=user,
        test_bank=test_bank,
        amount=test_bank.price,
        currency=settings.STRIPE_CURRENCY,
        payment_provider='stripe',
        status='created'
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
                'unit_amount': int(test_bank.price * 100),  # Convert to cents
            },
            'quantity': 1,
        }],
        'mode': 'payment',
        'success_url': success_url,
        'cancel_url': cancel_url,
        'client_reference_id': str(payment.id),
        'metadata': {
            'payment_id': str(payment.id),
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
    try:
        # Retrieve Stripe session (with proxy bypass)
        checkout_session = _make_stripe_request(
            stripe.checkout.Session.retrieve,
            session_id
        )
        
        # Find payment record by session ID
        try:
            payment = Payment.objects.get(provider_session_id=session_id)
        except Payment.DoesNotExist:
            raise Payment.DoesNotExist(f'Payment not found for session {session_id}')
        
        # Only process if payment is not already succeeded
        if payment.status != 'succeeded':
            # Update payment status
            payment.status = 'succeeded'
            payment.provider_payment_id = checkout_session.payment_intent
            payment.save()
            
            # Create Purchase record
            purchase, created = Purchase.objects.get_or_create(
                payment=payment,
                defaults={
                    'user': payment.user,
                    'test_bank': payment.test_bank,
                    'is_active': True,
                }
            )
            
            # Create UserTestAccess to grant user access
            if created:
                purchase.create_user_access()
            
            # Send payment invoice email
            try:
                send_payment_invoice(payment)
            except Exception as e:
                # Log error but don't fail payment processing
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send payment invoice email: {str(e)}')
            
            return payment, purchase
        else:
            # Payment already processed
            return payment, payment.purchase
    except Exception as e:
        # Re-raise any exceptions (will be handled by views)
        raise e


def handle_webhook_event(event):
    """
    Handle Stripe webhook events.
    
    This function processes different types of Stripe webhook events:
    - checkout.session.completed: Payment succeeded
    - payment_intent.succeeded: Payment confirmed
    - payment_intent.payment_failed: Payment failed
    
    Args:
        event: Stripe Event object from verified webhook
    
    Returns:
        tuple: (Payment instance, Purchase instance or None)
    """
    event_type = event['type']
    event_data = event['data']['object']
    
    if event_type == 'checkout.session.completed':
        # Payment completed via Checkout
        session_id = event_data['id']
        return handle_payment_success(session_id)
    
    elif event_type == 'payment_intent.succeeded':
        # Payment intent succeeded
        payment_intent_id = event_data['id']
        try:
            payment = Payment.objects.get(provider_payment_id=payment_intent_id)
            if payment.status != 'succeeded':
                payment.status = 'succeeded'
                payment.save()
                
                # Create purchase if not exists
                purchase, created = Purchase.objects.get_or_create(
                    payment=payment,
                    defaults={
                        'user': payment.user,
                        'test_bank': payment.test_bank,
                        'is_active': True,
                    }
                )
                
                if created:
                    purchase.create_user_access()
                
                # Send payment invoice email
                try:
                    send_payment_invoice(payment)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Failed to send payment invoice email: {str(e)}')
                
                return payment, purchase
        except Payment.DoesNotExist:
            pass
    
    elif event_type == 'payment_intent.payment_failed':
        # Payment failed
        payment_intent_id = event_data['id']
        try:
            payment = Payment.objects.get(provider_payment_id=payment_intent_id)
            payment.status = 'failed'
            payment.save()
            return payment, None
        except Payment.DoesNotExist:
            pass
    
    return None, None
