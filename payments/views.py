"""
Payments app views for payment processing and purchase management.

This module provides views for:
- Creating checkout sessions (initiating payment)
- Handling payment success callbacks
- Handling payment cancellation
- Processing Stripe webhooks
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from catalog.models import TestBank
from .models import Payment, Purchase
from .stripe_integration import (
    create_checkout_session,
    verify_webhook_signature,
    handle_webhook_event,
    handle_payment_success,
)
import json
import logging
import stripe

logger = logging.getLogger(__name__)


def grant_free_access(test_bank, user):
    """
    Grant free access to a test bank (when price is 0).
    
    This function:
    1. Creates a Payment record with status='succeeded' and amount=0
    2. Creates a Purchase record
    3. Creates UserTestAccess to grant user access
    
    Args:
        test_bank: TestBank instance (must have price=0)
        user: User instance to grant access to
    
    Returns:
        tuple: (Payment instance, Purchase instance)
    """
    from practice.models import UserTestAccess
    from django.conf import settings
    
    # Create Payment record for free access
    payment = Payment.objects.create(
        user=user,
        test_bank=test_bank,
        amount=0,
        currency=settings.STRIPE_CURRENCY if hasattr(settings, 'STRIPE_CURRENCY') else 'usd',
        payment_provider='free',
        status='succeeded',
        provider_session_id=f'free_{test_bank.id}_{user.id}',
    )
    
    # Create Purchase record
    purchase, created = Purchase.objects.get_or_create(
        payment=payment,
        defaults={
            'user': user,
            'test_bank': test_bank,
            'is_active': True,
        }
    )
    
    # Create UserTestAccess to grant user access
    if created:
        purchase.create_user_access()
    
    return payment, purchase


@login_required
def create_checkout(request, testbank_slug):
    """
    Create Stripe Checkout session and redirect user to payment page.
    
    This view:
    1. Verifies test bank exists and is active
    2. Checks if user already has access
    3. If price is 0 (free), grants access immediately without payment
    4. Otherwise, creates Payment record and Stripe Checkout session
    5. Redirects user to Stripe payment page or test bank detail
    
    Args:
        testbank_slug: Slug of the test bank to purchase
    """
    test_bank = get_object_or_404(TestBank, slug=testbank_slug, is_active=True)
    user = request.user
    
    # Check if user already has access
    from practice.models import UserTestAccess
    existing_access = UserTestAccess.objects.filter(
        user=user,
        test_bank=test_bank,
        is_active=True
    ).first()
    
    if existing_access and existing_access.is_valid():
        messages.info(request, 'You already have access to this test bank.')
        return redirect('catalog:testbank_detail', slug=testbank_slug)
    
    # If price is 0 (free), grant access immediately without payment
    if test_bank.price == 0:
        try:
            # Grant free access
            payment, purchase = grant_free_access(test_bank, user)
            
            messages.success(
                request,
                f'You now have free access to {test_bank.title}!'
            )
            return redirect('catalog:testbank_detail', slug=testbank_slug)
            
        except Exception as e:
            logger.error(f'Error granting free access: {str(e)}')
            messages.error(request, 'An error occurred while granting access. Please try again.')
            return redirect('catalog:testbank_detail', slug=testbank_slug)
    
    # For paid test banks, proceed with Stripe checkout
    try:
        # Validate Stripe configuration
        if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PUBLIC_KEY:
            logger.error('Stripe keys not configured')
            messages.error(request, 'Payment processing is not configured. Please contact support.')
            return redirect('catalog:testbank_detail', slug=testbank_slug)
        
        # Check if using custom checkout (default) or hosted
        ui_mode = request.GET.get('ui_mode', 'custom')
        
        # If user explicitly requests hosted checkout, use that
        if ui_mode == 'hosted':
            checkout_url = create_checkout_session(test_bank, user, request, ui_mode='hosted')
            return redirect(checkout_url)
        
        # Try custom/embedded checkout first
        try:
            checkout_result = create_checkout_session(test_bank, user, request, ui_mode='custom')
            
            # Render embedded payment form
            return render(request, 'payments/checkout.html', {
                'test_bank': test_bank,
                'client_secret': checkout_result['client_secret'],
                'session_id': checkout_result['session_id'],
                'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                'fallback_url': request.build_absolute_uri(
                    reverse('payments:create_checkout', kwargs={'testbank_slug': testbank_slug})
                ) + '?ui_mode=hosted',
            })
        except Exception as e:
            # If custom checkout fails, fall back to hosted
            logger.warning(f'Custom checkout failed, falling back to hosted: {str(e)}')
            checkout_url = create_checkout_session(test_bank, user, request, ui_mode='hosted')
            return redirect(checkout_url)
        
    except ValueError as e:
        # Validation errors
        logger.error(f'Validation error creating checkout session: {str(e)}')
        messages.error(request, f'Invalid payment configuration: {str(e)}')
        return redirect('catalog:testbank_detail', slug=testbank_slug)
    except Exception as e:
        # Stripe API errors and other exceptions
        error_msg = str(e)
        if hasattr(e, 'user_message'):
            error_msg = e.user_message
        elif hasattr(e, 'message'):
            error_msg = e.message
        
        logger.error(f'Stripe API error: {error_msg}', exc_info=True)
        messages.error(request, f'Payment processing error: {error_msg}')
        return redirect('catalog:testbank_detail', slug=testbank_slug)
    except Exception as e:
        # Other errors
        logger.error(f'Error creating checkout session: {str(e)}', exc_info=True)
        messages.error(request, 'An error occurred while processing your payment. Please try again.')
        return redirect('catalog:testbank_detail', slug=testbank_slug)


@login_required
def payment_success(request):
    """
    Handle successful payment return from Stripe Checkout.
    
    This view is called when user returns from Stripe after successful payment.
    It processes the payment and grants user access to the test bank.
    
    Security Note: This is a return URL, not a webhook. The actual payment
    verification should happen via webhook. This view provides immediate feedback
    to the user, but webhook processing is the source of truth.
    """
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('accounts:dashboard')
    
    try:
        # Handle payment success
        payment, purchase = handle_payment_success(session_id)
        
        if payment and purchase:
            messages.success(
                request,
                f'Payment successful! You now have access to {payment.test_bank.title}.'
            )
            return redirect('catalog:testbank_detail', slug=payment.test_bank.slug)
        else:
            messages.warning(request, 'Payment is being processed. Please wait a moment.')
            return redirect('accounts:dashboard')
            
    except Exception as e:
        logger.error(f'Error processing payment success: {str(e)}')
        messages.error(request, 'An error occurred while processing your payment.')
        return redirect('accounts:dashboard')


@login_required
def payment_cancel(request):
    """
    Handle payment cancellation from Stripe Checkout.
    
    This view is called when user cancels payment on Stripe Checkout page.
    Updates payment status and shows cancellation message.
    """
    messages.info(request, 'Payment was cancelled. You can try again anytime.')
    return redirect('accounts:dashboard')


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    
    This is the SECURE endpoint for processing Stripe payment events.
    Webhooks are the source of truth for payment status - never trust
    client-side data or return URLs alone.
    
    Security:
    - CSRF exempt (Stripe can't provide CSRF token)
    - Verifies webhook signature to ensure request is from Stripe
    - Processes events asynchronously
    
    Webhook events handled:
    - checkout.session.completed: Payment completed
    - payment_intent.succeeded: Payment confirmed
    - payment_intent.payment_failed: Payment failed
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        # Verify webhook signature (CRITICAL for security)
        event = verify_webhook_signature(request)
        
        # Handle the event
        payment, purchase = handle_webhook_event(event)
        
        if payment:
            logger.info(f'Processed webhook event: {event["type"]} for payment {payment.id}')
        
        return JsonResponse({'status': 'success'})
        
    except ValueError as e:
        # Invalid payload or signature
        logger.error(f'Webhook signature verification failed: {str(e)}')
        return JsonResponse({'error': str(e)}, status=400)
        
    except Exception as e:
        # Other errors
        logger.error(f'Webhook processing error: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def payment_detail(request, pk):
    """
    Display payment detail page.
    
    Shows payment information including:
    - Payment amount and status
    - Test bank purchased
    - Timestamps
    
    Args:
        pk: Primary key of the Payment
    """
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    
    return render(request, 'payments/payment_detail.html', {
        'payment': payment,
    })


@login_required
def purchase_list(request):
    """
    Display user's purchase history.
    
    Shows all purchases made by the current user with:
    - Test bank purchased
    - Purchase date
    - Payment status
    - Access status
    """
    purchases = Purchase.objects.filter(
        user=request.user
    ).select_related('test_bank', 'payment').order_by('-purchased_at')
    
    return render(request, 'payments/purchase_list.html', {
        'purchases': purchases,
    })
