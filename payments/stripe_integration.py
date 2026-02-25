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
from django.conf import settings
from django.urls import reverse
from .models import Payment, Purchase
from practice.models import UserTestAccess
from .email_utils import send_payment_invoice


def _ensure_stripe_configured():
    """Lazily configure Stripe API key on first use, avoiding module-level crashes."""
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError('STRIPE_SECRET_KEY is not configured. Please set it in your .env file.')
    stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(test_bank, user, request, ui_mode='hosted'):
    """
    Create a Stripe Checkout session for purchasing a test bank.
    
    This function:
    1. Creates a Payment record with status='created'
    2. Creates a Stripe Checkout session
    3. Updates Payment with Stripe session ID
    4. Returns the checkout session URL or client_secret depending on ui_mode
    
    Args:
        test_bank: TestBank instance to purchase
        user: User instance making the purchase
        request: Django HttpRequest object (for building absolute URLs)
        ui_mode: 'hosted' for redirect-based checkout, 'embedded' for Payment Element
    
    Returns:
        str: Stripe Checkout session URL (hosted) or dict with client_secret (embedded)
    
    Raises:
        stripe.error.StripeError: If Stripe API call fails
    """
    _ensure_stripe_configured()
    
    # Create Payment record with initial status
    payment = Payment.objects.create(
        user=user,
        test_bank=test_bank,
        amount=test_bank.price,
        currency=settings.STRIPE_CURRENCY,
        payment_provider='stripe',
        status='created'
    )
    
    # Build URLs based on checkout mode
    success_url = request.build_absolute_uri(
        reverse('payments:payment_success')
    ) + f'?session_id={{CHECKOUT_SESSION_ID}}'
    
    cancel_url = request.build_absolute_uri(
        reverse('payments:payment_cancel')
    )
    
    try:
        # Validate test bank price
        if test_bank.price <= 0:
            raise ValueError('Test bank price must be greater than 0')
        
        # Validate description (handle None case)
        description = test_bank.description or ''
        if len(description) > 500:
            description = description[:500]
        
        # Create Stripe Checkout session
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
            'client_reference_id': str(payment.id),  # Store payment ID for reference
            'metadata': {
                'payment_id': str(payment.id),
                'test_bank_id': str(test_bank.id),
                'user_id': str(user.id),
            }
        }
        
        # Add ui_mode and URLs based on checkout mode
        if ui_mode == 'embedded' or ui_mode == 'custom':
            # For embedded/custom checkout, use return_url instead of success_url/cancel_url
            session_params['ui_mode'] = 'custom'  # Use 'custom' for Payment Element
            session_params['return_url'] = success_url
        else:
            # For hosted checkout, use success_url and cancel_url
            session_params['success_url'] = success_url
            session_params['cancel_url'] = cancel_url
        
        checkout_session = stripe.checkout.Session.create(**session_params)
        
        # Update Payment with Stripe session ID
        payment.provider_session_id = checkout_session.id
        payment.status = 'pending'
        payment.save()
        
        if ui_mode == 'embedded' or ui_mode == 'custom':
            # Return client_secret for embedded/custom checkout
            return {
                'client_secret': checkout_session.client_secret,
                'session_id': checkout_session.id
            }
        else:
            # Return URL for hosted checkout
            return checkout_session.url
        
    except stripe.error.StripeError as e:
        # Update payment status to failed if Stripe error occurs
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
        stripe.Webhook: Verified webhook event object
    
    Raises:
        ValueError: If signature verification fails
        stripe.error.SignatureVerificationError: If signature is invalid
    """
    _ensure_stripe_configured()
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        raise ValueError('Missing Stripe signature header')
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise ValueError('STRIPE_WEBHOOK_SECRET not configured')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError as e:
        # Invalid payload
        raise ValueError(f'Invalid payload: {e}')
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature - this means the request is NOT from Stripe
        raise ValueError(f'Invalid signature: {e}')


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
        stripe.error.StripeError: If Stripe API call fails
    """
    _ensure_stripe_configured()
    
    try:
        # Retrieve Stripe session to verify payment status
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
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
            
            # Send payment invoice email to customer
            try:
                send_payment_invoice(payment)
            except Exception as e:
                # Log error but don't fail the payment processing
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send payment invoice email: {str(e)}')
            
            return payment, purchase
        else:
            # Payment already processed
            return payment, payment.purchase
        
    except stripe.error.StripeError as e:
        # Handle Stripe API errors
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
                
                # Send payment invoice email to customer
                try:
                    send_payment_invoice(payment)
                except Exception as e:
                    # Log error but don't fail the payment processing
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

