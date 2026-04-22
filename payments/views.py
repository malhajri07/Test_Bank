"""
Payments app views for payment processing and purchase management.

This module provides views for:
- Creating Paylink invoices (initiating payment)
- Handling payment callbacks from Paylink
- Payment and purchase detail pages
- Shopping cart (session-based)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
from decimal import Decimal

from catalog.models import ExamPackage, TestBank
from .models import Coupon, Order, OrderItem, Payment, Purchase
from .paylink_integration import create_invoice
from . import reconciliation
import logging

logger = logging.getLogger(__name__)


def _paylink_configured():
    return bool(getattr(settings, 'PAYLINK_APP_ID', '') and getattr(settings, 'PAYLINK_SECRET_KEY', ''))


def grant_free_access(test_bank, user):
    """Grant free access to a test bank (when price is 0)."""
    from practice.models import UserTestAccess

    payment = Payment.objects.create(
        user=user,
        test_bank=test_bank,
        amount=0,
        currency=getattr(settings, 'PAYLINK_CURRENCY', 'SAR'),
        payment_provider='free',
        status='succeeded',
        provider_session_id=f'free_{test_bank.id}_{user.id}',
    )

    purchase, created = Purchase.objects.get_or_create(
        payment=payment,
        test_bank=test_bank,
        defaults={'user': user, 'is_active': True},
    )

    if created:
        purchase.create_user_access()

    return payment, purchase


@login_required
def create_checkout(request, testbank_slug):
    """Start checkout for a test bank via Paylink."""
    test_bank = get_object_or_404(TestBank, slug=testbank_slug, is_active=True)
    user = request.user

    from practice.models import UserTestAccess
    existing_access = UserTestAccess.objects.filter(
        user=user, test_bank=test_bank, is_active=True
    ).first()

    if existing_access and existing_access.is_valid():
        messages.info(request, 'You already have access to this test bank.')
        return redirect('catalog:testbank_detail', slug=testbank_slug)

    # Free items
    if test_bank.price == 0:
        try:
            grant_free_access(test_bank, user)
            messages.success(request, f'You now have free access to {test_bank.title}!')
            return redirect('catalog:testbank_detail', slug=testbank_slug)
        except Exception as e:
            logger.error(f'Error granting free access: {e}')
            messages.error(request, 'An error occurred while granting access. Please try again.')
            return redirect('catalog:testbank_detail', slug=testbank_slug)

    if not _paylink_configured():
        messages.error(request, 'Payment processing is not configured. Please contact support.')
        return redirect('catalog:testbank_detail', slug=testbank_slug)

    # Coupon handling
    discount_amount = Decimal('0')
    coupon = None
    promo_code = request.GET.get('promo', '').strip().upper()
    if promo_code:
        try:
            coupon = Coupon.objects.get(code__iexact=promo_code)
            discount, err = coupon.validate_for_order(
                subtotal=test_bank.price, test_bank_ids=[test_bank.id],
            )
            if err:
                messages.warning(request, err)
            elif discount > 0:
                discount_amount = discount
                messages.success(request, f'Promo code applied: {discount_amount} off.')
        except Coupon.DoesNotExist:
            messages.warning(request, 'Invalid promo code.')

    amount = max(Decimal('0'), test_bank.price - discount_amount)
    # Paylink is a Saudi gateway and only reliably invoices in SAR. Display
    # currencies on the product page are presentation-only — settlement stays
    # in SAR to avoid charging a mismatched amount/currency pair.
    currency = getattr(settings, 'PAYLINK_CURRENCY', 'SAR')

    # Create Payment record
    payment = Payment.objects.create(
        user=user,
        test_bank=test_bank,
        amount=amount,
        currency=currency,
        payment_provider='paylink',
        status='created',
    )

    callback_url = request.build_absolute_uri(
        reverse('payments:paylink_callback', kwargs={'payment_id': payment.id})
    )
    cancel_url = request.build_absolute_uri(
        reverse('catalog:testbank_detail', kwargs={'slug': testbank_slug})
    )

    try:
        invoice = create_invoice(
            order_number=str(payment.id),
            amount=amount,
            callback_url=callback_url,
            cancel_url=cancel_url,
            client_name=user.get_full_name() or user.username,
            client_email=user.email,
            client_mobile=getattr(user, 'phone', '') or '0500000000',
            products=[{
                'title': test_bank.title,
                'price': float(amount),
                'qty': 1,
                'description': test_bank.description[:200] if test_bank.description else '',
                'is_digital': True,
            }],
            currency=currency,
        )

        transaction_no = invoice.get('transactionNo')
        payment_url = invoice.get('url')

        payment.provider_session_id = transaction_no
        payment.status = 'pending'
        payment.save()

        return redirect(payment_url)

    except Exception as e:
        logger.error(f'Paylink create invoice error: {e}', exc_info=True)
        payment.status = 'failed'
        payment.save()
        messages.error(request, 'An error occurred while processing your payment. Please try again.')
        return redirect('catalog:testbank_detail', slug=testbank_slug)


@login_required
def create_checkout_package(request, package_slug):
    """Create Paylink checkout for an exam package."""
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

    if not _paylink_configured():
        messages.error(request, 'Payment processing is not configured. Please contact support.')
        return redirect('catalog:package_detail', slug=package_slug)

    # Coupon handling
    discount_amount = Decimal('0')
    coupon = None
    promo_code = request.GET.get('promo', '').strip().upper()
    if promo_code:
        try:
            coupon = Coupon.objects.get(code__iexact=promo_code)
            discount, err = coupon.validate_for_order(
                subtotal=package.package_price, test_bank_ids=list(tb_ids),
            )
            if not err:
                discount_amount = discount
        except Coupon.DoesNotExist:
            pass

    payable_banks = list(package.test_banks.filter(is_active=True))
    amount = max(Decimal('0'), package.package_price - discount_amount)
    currency = getattr(settings, 'PAYLINK_CURRENCY', 'SAR')

    # Create Order + OrderItems
    vat_rate = Decimal(str(getattr(settings, 'VAT_RATE', 0.15)))
    tax = (amount * vat_rate).quantize(Decimal('0.01'))
    total = (amount + tax).quantize(Decimal('0.01'))

    order = Order.objects.create(
        user=user,
        subtotal=package.package_price,
        discount_amount=discount_amount,
        tax_amount=tax,
        total_amount=total,
        currency=currency,
        coupon=coupon,
    )
    for tb in payable_banks:
        OrderItem.objects.create(order=order, test_bank=tb, quantity=1, unit_price=tb.price)

    payment = Payment.objects.create(
        user=user,
        order=order,
        test_bank=payable_banks[0] if payable_banks else None,
        amount=amount,
        currency=currency,
        payment_provider='paylink',
        status='created',
    )

    callback_url = request.build_absolute_uri(
        reverse('payments:paylink_callback', kwargs={'payment_id': payment.id})
    )
    cancel_url = request.build_absolute_uri(
        reverse('catalog:package_detail', kwargs={'slug': package_slug})
    )

    try:
        invoice = create_invoice(
            order_number=str(payment.id),
            amount=amount,
            callback_url=callback_url,
            cancel_url=cancel_url,
            client_name=user.get_full_name() or user.username,
            client_email=user.email,
            client_mobile=getattr(user, 'phone', '') or '0500000000',
            products=[
                {
                    'title': tb.title,
                    'price': float(tb.price),
                    'qty': 1,
                    'is_digital': True,
                }
                for tb in payable_banks
            ],
            currency=currency,
        )

        payment.provider_session_id = invoice.get('transactionNo')
        payment.status = 'pending'
        payment.save()

        return redirect(invoice.get('url'))

    except Exception as e:
        logger.error(f'Paylink package checkout error: {e}', exc_info=True)
        payment.status = 'failed'
        payment.save()
        messages.error(request, 'An error occurred while processing your payment.')
        return redirect('catalog:package_detail', slug=package_slug)


@login_required
def paylink_callback(request, payment_id):
    """
    Handle return from Paylink after payment.

    Paylink redirects the customer back to callBackUrl after payment.
    We verify the invoice status via getInvoice API.
    """
    payment = get_object_or_404(Payment, pk=payment_id, user=request.user)

    result = reconciliation.reconcile_payment(payment)

    if result == reconciliation.ALREADY_PROCESSED:
        if payment.status == 'succeeded':
            messages.info(request, 'This payment has already been processed.')
            if payment.test_bank:
                return redirect('catalog:testbank_detail', slug=payment.test_bank.slug)
        elif payment.status == 'cancelled':
            messages.info(request, 'Payment was cancelled. You can try again anytime.')
        return redirect('accounts:dashboard')

    if result == reconciliation.MISSING_SESSION:
        messages.error(request, 'Invalid payment session.')
        return redirect('accounts:dashboard')

    if result == reconciliation.PAID:
        if payment.order and payment.order.items.count() > 1:
            messages.success(request, 'Payment successful! You now have access to all exams in your package.')
            return redirect('accounts:dashboard')
        if payment.test_bank:
            messages.success(request, f'Payment successful! You now have access to {payment.test_bank.title}.')
            return redirect('catalog:testbank_detail', slug=payment.test_bank.slug)
        messages.success(request, 'Payment successful!')
        return redirect('accounts:dashboard')

    if result == reconciliation.CANCELLED:
        messages.info(request, 'Payment was cancelled. You can try again anytime.')
        if payment.test_bank:
            return redirect('catalog:testbank_detail', slug=payment.test_bank.slug)
        return redirect('accounts:dashboard')

    if result == reconciliation.PENDING:
        messages.warning(request, 'Payment is still being processed. Please wait a moment and check your dashboard.')
        return redirect('accounts:dashboard')

    # ERROR
    messages.error(request, 'An error occurred while verifying your payment. Please contact support.')
    return redirect('accounts:dashboard')


@login_required
def payment_success(request):
    """Generic payment success page."""
    messages.success(request, 'Payment successful!')
    return redirect('accounts:dashboard')


@login_required
def payment_cancel(request):
    """Handle payment cancellation."""
    messages.info(request, 'Payment was cancelled. You can try again anytime.')
    return redirect('accounts:dashboard')


@login_required
def payment_detail(request, pk):
    """Display payment detail page."""
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    return render(request, 'payments/payment_detail.html', {'payment': payment})


@login_required
def purchase_list(request):
    """Display user's purchase history."""
    purchases = Purchase.objects.filter(
        user=request.user
    ).select_related('test_bank', 'payment').order_by('-purchased_at')
    return render(request, 'payments/purchase_list.html', {'purchases': purchases})


# ------------------------------------------------------------------
# Shopping cart (session-based)
# ------------------------------------------------------------------

def cart_view(request):
    """Display the user's cart with subtotal and a checkout button."""
    from .cart import Cart
    cart = Cart(request)
    test_banks = list(cart.get_test_banks().select_related('category', 'certification'))
    subtotal = cart.get_subtotal()

    vat_rate = Decimal(str(getattr(settings, 'VAT_RATE', 0.15)))
    tax = (subtotal * vat_rate).quantize(Decimal('0.01'))
    total = (subtotal + tax).quantize(Decimal('0.01'))

    return render(request, 'payments/cart.html', {
        'cart_items': test_banks,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'vat_rate_pct': int(float(vat_rate) * 100),
    })


@require_http_methods(["POST"])
def cart_add(request, testbank_slug):
    """Add a test bank to the cart. Idempotent."""
    from .cart import Cart
    test_bank = get_object_or_404(TestBank, slug=testbank_slug, is_active=True)
    cart = Cart(request)
    added = cart.add(test_bank.id)
    if added:
        messages.success(request, f'"{test_bank.title}" added to cart.')
    else:
        messages.info(request, f'"{test_bank.title}" is already in your cart.')
    next_url = request.POST.get('next') or reverse('payments:cart_view')
    return redirect(next_url)


@require_http_methods(["POST"])
def cart_remove(request, testbank_id):
    """Remove a test bank from the cart by ID. Idempotent."""
    from .cart import Cart
    cart = Cart(request)
    cart.remove(testbank_id)
    messages.success(request, 'Item removed from cart.')
    return redirect('payments:cart_view')


@login_required
@require_http_methods(["POST"])
def cart_checkout(request):
    """Convert the cart to a Paylink invoice and redirect to payment."""
    from .cart import Cart
    cart = Cart(request)
    test_banks = list(cart.get_test_banks())

    if not test_banks:
        messages.error(request, 'Your cart is empty.')
        return redirect('payments:cart_view')

    if not _paylink_configured():
        messages.error(request, 'Payment processing is not configured. Please contact support.')
        return redirect('payments:cart_view')

    user = request.user

    # Skip items the user already owns
    from practice.models import UserTestAccess
    owned_ids = set(
        UserTestAccess.objects.filter(
            user=user, test_bank_id__in=[tb.id for tb in test_banks], is_active=True,
        ).values_list('test_bank_id', flat=True)
    )
    payable = [tb for tb in test_banks if tb.id not in owned_ids]
    for tb in test_banks:
        if tb.id in owned_ids:
            cart.remove(tb.id)

    if not payable:
        messages.info(request, 'You already own every item in your cart.')
        return redirect('payments:cart_view')

    subtotal = sum((tb.price for tb in payable), Decimal('0'))
    SUPPORTED_CURRENCIES = {'SAR', 'USD', 'AED', 'KWD', 'BHD', 'QAR', 'OMR', 'EGP'}
    currency = request.POST.get('currency', '').upper()
    if currency not in SUPPORTED_CURRENCIES:
        currency = getattr(settings, 'PAYLINK_CURRENCY', 'SAR')
    vat_rate = Decimal(str(getattr(settings, 'VAT_RATE', 0.15)))
    tax = (subtotal * vat_rate).quantize(Decimal('0.01'))
    total = (subtotal + tax).quantize(Decimal('0.01'))

    order = Order.objects.create(
        user=user,
        subtotal=subtotal,
        discount_amount=Decimal('0'),
        tax_amount=tax,
        total_amount=total,
        currency=currency,
    )
    for tb in payable:
        OrderItem.objects.create(order=order, test_bank=tb, quantity=1, unit_price=tb.price)

    payment = Payment.objects.create(
        user=user,
        order=order,
        test_bank=payable[0],
        amount=subtotal,
        currency=currency,
        payment_provider='paylink',
        status='created',
    )

    callback_url = request.build_absolute_uri(
        reverse('payments:paylink_callback', kwargs={'payment_id': payment.id})
    )
    cancel_url = request.build_absolute_uri(reverse('payments:cart_view'))

    try:
        invoice = create_invoice(
            order_number=str(payment.id),
            amount=float(subtotal),
            callback_url=callback_url,
            cancel_url=cancel_url,
            client_name=user.get_full_name() or user.username,
            client_email=user.email,
            client_mobile=getattr(user, 'phone', '') or '0500000000',
            products=[
                {
                    'title': tb.title,
                    'price': float(tb.price),
                    'qty': 1,
                    'is_digital': True,
                }
                for tb in payable
            ],
            currency=currency,
        )

        payment.provider_session_id = invoice.get('transactionNo')
        payment.status = 'pending'
        payment.save()

        cart.clear()
        return redirect(invoice.get('url'))

    except Exception as e:
        logger.error(f'Cart checkout Paylink error: {e}', exc_info=True)
        payment.status = 'failed'
        payment.save()
        messages.error(request, 'Unable to start checkout. Please try again.')
        return redirect('payments:cart_view')
