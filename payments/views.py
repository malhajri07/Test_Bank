"""
Payments app views for payment processing and purchase management.

This module provides views for:
- Creating checkout sessions (initiating payment)
- Handling payment success callbacks
- Handling payment cancellation
- Processing Stripe webhooks
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
import stripe
from decimal import Decimal

from catalog.models import ExamPackage, TestBank
from .models import Coupon, Payment, Purchase
from .stripe_integration import (
    create_checkout_session,
    create_checkout_session_for_package,
    verify_webhook_signature,
    handle_webhook_event,
    handle_payment_success,
)
from .tap_integration import create_charge as tap_create_charge, handle_tap_callback
import logging

logger = logging.getLogger(__name__)


def _tap_checkout(request, test_bank, user):
    """Render Tap checkout page with Card SDK v2."""
    publishable_key = getattr(settings, 'TAP_PUBLISHABLE_KEY', '') or ''
    merchant_id = getattr(settings, 'TAP_MERCHANT_ID', '') or ''
    if not publishable_key or not merchant_id:
        messages.error(request, 'Tap payment is not configured.')
        return redirect('catalog:testbank_detail', slug=test_bank.slug)

    amount_after_discount = max(Decimal('0'), test_bank.price)
    currency = getattr(settings, 'TAP_CURRENCY', 'USD')
    amount_smallest = int(float(amount_after_discount) * 100)  # cents/halalas

    payment = Payment.objects.create(
        user=user,
        test_bank=test_bank,
        amount=amount_after_discount,
        currency=currency,
        payment_provider='tap',
        status='created',
    )

    callback_url = request.build_absolute_uri(
        reverse('payments:tap_callback', kwargs={'payment_id': payment.id})
    )

    return render(request, 'payments/tap_checkout.html', {
        'test_bank': test_bank,
        'payment': payment,
        'amount': amount_after_discount,
        'amount_smallest': amount_smallest,
        'currency': currency,
        'publishable_key': publishable_key,
        'merchant_id': merchant_id,
        'callback_url': callback_url,
        'user': user,
    })


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
        test_bank=test_bank,
        defaults={
            'user': user,
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
    Start checkout for a test bank.

    - Default: Stripe Checkout (redirect to hosted payment page).
    - ``?gateway=tap``: Tap Payments (Card SDK + Charge API).

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
    
    # Optional: ?gateway=tap for Tap Payments (MEA cards); default is Stripe Checkout
    gateway = request.GET.get('gateway', '').lower()
    if gateway == 'tap':
        return _tap_checkout(request, test_bank, user)

    # For paid test banks, proceed with Stripe checkout
    try:
        if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PUBLIC_KEY:
            logger.error('Stripe keys not configured')
            messages.error(request, 'Payment processing is not configured. Please contact support.')
            return redirect('catalog:testbank_detail', slug=testbank_slug)

        discount_amount = Decimal('0')
        coupon = None
        promo_code = request.GET.get('promo', '').strip().upper()
        if promo_code:
            try:
                coupon = Coupon.objects.get(code__iexact=promo_code)
                discount, err = coupon.validate_for_order(
                    subtotal=test_bank.price,
                    test_bank_ids=[test_bank.id],
                )
                if err:
                    messages.warning(request, err)
                else:
                    discount_amount = discount
                    if discount_amount > 0:
                        messages.success(request, f'Promo code applied: ${discount_amount} off.')
            except Coupon.DoesNotExist:
                messages.warning(request, 'Invalid promo code.')

        checkout_url = create_checkout_session(
            test_bank, user, request,
            discount_amount=discount_amount,
            coupon=coupon,
        )
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
            if 'APIConnectionError' in error_type or 'Connection' in error_type or 'Proxy' in error_type:
                messages.error(request, 'Unable to connect to payment service. Please check your internet connection and try again.')
            else:
                messages.error(request, f'Payment processing error: {error_msg}')
        else:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            messages.error(request, 'An error occurred while processing your payment. Please try again.')
        return redirect('catalog:testbank_detail', slug=testbank_slug)


@login_required
def create_checkout_package(request, package_slug):
    """Create Stripe Checkout for an exam package."""
    package = get_object_or_404(ExamPackage, slug=package_slug, is_active=True)
    user = request.user

    from practice.models import UserTestAccess
    tb_ids = list(package.test_banks.filter(is_active=True).values_list('id', flat=True))
    access_count = UserTestAccess.objects.filter(
        user=user, test_bank_id__in=tb_ids, is_active=True
    ).count()
    if tb_ids and access_count == len(tb_ids):
        messages.info(request, 'You already have access to all exams in this package.')
        return redirect('catalog:package_detail', slug=package_slug)

    discount_amount = Decimal('0')
    coupon = None
    promo_code = request.GET.get('promo', '').strip().upper()
    if promo_code:
        try:
            coupon = Coupon.objects.get(code__iexact=promo_code)
            discount, err = coupon.validate_for_order(
                subtotal=package.package_price,
                test_bank_ids=list(tb_ids),
            )
            if not err:
                discount_amount = discount
        except Coupon.DoesNotExist:
            pass

    try:
        if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PUBLIC_KEY:
            messages.error(request, 'Payment system is not configured.')
            return redirect('catalog:package_detail', slug=package_slug)

        checkout_url = create_checkout_session_for_package(
            package, user, request, discount_amount=discount_amount, coupon=coupon
        )
        return redirect(checkout_url)
    except Exception as e:
        logger.error(f'Package checkout error: {str(e)}', exc_info=True)
        messages.error(request, 'An error occurred while processing your payment.')
        return redirect('catalog:package_detail', slug=package_slug)


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
            if payment.order and payment.order.items.count() > 1:
                messages.success(
                    request,
                    'Payment successful! You now have access to all exams in your package.'
                )
                return redirect('accounts:dashboard')
            elif payment.test_bank:
                messages.success(
                    request,
                    f'Payment successful! You now have access to {payment.test_bank.title}.'
                )
                return redirect('catalog:testbank_detail', slug=payment.test_bank.slug)
            else:
                messages.success(request, 'Payment successful!')
                return redirect('accounts:dashboard')
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
        
        logger.error(f'Error processing payment success: {str(e)}', exc_info=True)
        if is_stripe_error:
            if 'InvalidRequestError' in error_type or 'Invalid' in error_type:
                messages.error(request, 'Invalid payment session. Please contact support.')
            elif 'APIConnectionError' in error_type or 'Connection' in error_type:
                messages.error(request, 'Payment service temporarily unavailable. Please try again.')
            else:
                messages.error(request, 'Payment processing error. Please contact support.')
        else:
            messages.error(request, 'An error occurred while processing your payment. Please contact support.')
        return redirect('accounts:dashboard')


@login_required
def payment_cancel(request):
    """
    Handle payment cancellation from Stripe Checkout.
    """
    messages.info(request, 'Payment was cancelled. You can try again anytime.')
    return redirect('accounts:dashboard')


@login_required
def tap_create_charge_ajax(request):
    """Create Tap charge from token (called via AJAX from tap checkout)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    token_id = request.POST.get('token') or request.GET.get('token')
    payment_id = request.POST.get('payment_id') or request.GET.get('payment_id')
    if not token_id or not payment_id:
        return JsonResponse({'error': 'Missing token or payment_id'}, status=400)
    payment = Payment.objects.filter(pk=payment_id, user=request.user).first()
    if not payment:
        return JsonResponse({'error': 'Invalid payment'}, status=404)
    if payment.payment_provider != 'tap':
        return JsonResponse({'error': 'Invalid payment provider'}, status=400)
    try:
        callback_url = request.build_absolute_uri(
            reverse('payments:tap_callback', kwargs={'payment_id': payment.id})
        )
        resp = tap_create_charge(payment, token_id, callback_url)
        transaction = resp.get('transaction', {})
        redirect_url = transaction.get('url')
        if redirect_url:
            return JsonResponse({'redirect_url': redirect_url})
        status = resp.get('status', '').upper()
        if status == 'CAPTURED':
            charge_id = resp.get('id')
            if charge_id:
                handle_tap_callback(charge_id, payment.id)
            return JsonResponse({
                'success': True,
                'redirect_url': request.build_absolute_uri(
                    reverse('catalog:testbank_detail', args=[payment.test_bank.slug])
                ),
            })
        return JsonResponse({'error': 'Payment could not be processed'}, status=400)
    except Exception as e:
        logger.error(f'Tap create charge error: {e}', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def tap_callback(request, payment_id):
    """Handle return from Tap after payment (redirect with tap_id)."""
    tap_id = request.GET.get('tap_id')
    if not tap_id:
        messages.error(request, 'Invalid payment callback.')
        return redirect('accounts:dashboard')
    try:
        payment, purchase = handle_tap_callback(tap_id, payment_id)
        if payment.user_id != request.user.id:
            messages.error(request, 'Invalid payment.')
            return redirect('accounts:dashboard')
        if purchase:
            messages.success(
                request,
                f'Payment successful! You now have access to {payment.test_bank.title}.'
            )
            return redirect('catalog:testbank_detail', slug=payment.test_bank.slug)
        else:
            messages.warning(request, 'Payment was not completed. Please try again.')
            return redirect('catalog:testbank_detail', slug=payment.test_bank.slug)
    except Exception as e:
        logger.error(f'Tap callback error: {e}', exc_info=True)
        messages.error(request, 'An error occurred while processing your payment.')
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
