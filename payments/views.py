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
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
import stripe
from catalog.models import TestBank
from .models import Payment, Purchase
from .stripe_integration import (
    create_checkout_session,
    verify_webhook_signature,
    handle_webhook_event,
    handle_payment_success,
)
import logging

logger = logging.getLogger(__name__)


def grant_free_access(test_bank, user):
    """
    Grant free access to a test bank (when price is 0).
    
    Args:
        test_bank: TestBank instance (must have price=0)
        user: User instance to grant access to
    
    Returns:
        tuple: (Payment instance, Purchase instance)
    """
    from practice.models import UserTestAccess
    
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
    
    # If price is 0 (free), grant access immediately
    if test_bank.price == 0:
        try:
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
        
        # Create Stripe Checkout session
        checkout_url = create_checkout_session(test_bank, user, request)
        return redirect(checkout_url)
        
    except ValueError as e:
        # Validation errors
        logger.error(f'Validation error: {str(e)}')
        messages.error(request, f'Invalid payment configuration: {str(e)}')
        return redirect('catalog:testbank_detail', slug=testbank_slug)
    except Exception as e:
        # Check if it's a Stripe-related error
        error_type = type(e).__name__
        error_str = str(type(e)).lower()
        is_stripe_error = (
            'stripe' in error_str or
            'Stripe' in error_type or
            'APIConnectionError' in error_type or
            'Connection' in error_type or
            hasattr(e, '__class__') and 'stripe' in str(e.__class__.__module__).lower()
        )
        
        if is_stripe_error:
            error_msg = str(e)
            if hasattr(e, 'user_message'):
                error_msg = e.user_message
            
            logger.error(f'Stripe API error: {error_msg}', exc_info=True)
            
            # Provide user-friendly error messages
            if 'APIConnectionError' in error_type or 'Connection' in error_type or 'Proxy' in error_type:
                messages.error(request, 'Unable to connect to payment service. Please check your internet connection and try again.')
            else:
                messages.error(request, f'Payment processing error: {error_msg}')
            return redirect('catalog:testbank_detail', slug=testbank_slug)
        else:
            # Re-raise non-Stripe errors
            raise
    except Exception as e:
        # Other errors
        logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        messages.error(request, 'An error occurred while processing your payment. Please try again.')
        return redirect('catalog:testbank_detail', slug=testbank_slug)


@login_required
def payment_success(request):
    """
    Handle successful payment return from Stripe Checkout.
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
        # Check if it's a Stripe-related error
        error_type = type(e).__name__
        error_str = str(type(e)).lower()
        is_stripe_error = (
            'stripe' in error_str or
            'Stripe' in error_type or
            hasattr(e, '__class__') and 'stripe' in str(e.__class__.__module__).lower()
        )
        
        if is_stripe_error:
            logger.error(f'Stripe error processing payment success: {str(e)}')
            if 'InvalidRequestError' in error_type or 'Invalid' in error_type:
                messages.error(request, 'Invalid payment session. Please contact support.')
            elif 'APIConnectionError' in error_type or 'Connection' in error_type:
                messages.error(request, 'Payment service temporarily unavailable. Please try again.')
            else:
                messages.error(request, 'Payment processing error. Please contact support.')
            return redirect('accounts:dashboard')
        else:
            # Re-raise non-Stripe errors
            raise
    except Exception as e:
        logger.error(f'Error processing payment success: {str(e)}', exc_info=True)
        messages.error(request, 'An error occurred while processing your payment. Please contact support.')
        return redirect('accounts:dashboard')


@login_required
def payment_cancel(request):
    """
    Handle payment cancellation from Stripe Checkout.
    """
    messages.info(request, 'Payment was cancelled. You can try again anytime.')
    return redirect('accounts:dashboard')


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    
    This is the SECURE endpoint for processing Stripe payment events.
    Webhooks are the source of truth for payment status.
    """
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
    """
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    
    return render(request, 'payments/payment_detail.html', {
        'payment': payment,
    })


@login_required
def purchase_list(request):
    """
    Display user's purchase history.
    """
    purchases = Purchase.objects.filter(
        user=request.user
    ).select_related('test_bank', 'payment').order_by('-purchased_at')
    
    return render(request, 'payments/purchase_list.html', {
        'purchases': purchases,
    })
