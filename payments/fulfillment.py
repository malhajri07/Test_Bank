"""
Payment fulfillment logic.

Creates Purchase and UserTestAccess records when payment succeeds.
Supports both single-item and order-based (package) flows.
"""

from .models import Coupon, OrderItem, Payment, Purchase


def fulfill_payment(payment):
    """
    Fulfill a successful payment: create Purchase(s) and grant UserTestAccess.

    - If payment.order exists: create Purchase for each OrderItem
    - Else: create single Purchase from payment.test_bank

    Returns:
        Purchase or None: First purchase created, or None if already fulfilled
    """
    if payment.order:
        payment.order.status = 'paid'
        payment.order.save()
        if payment.order.coupon:
            from django.db.models import F
            Coupon.objects.filter(pk=payment.order.coupon_id).update(
                current_uses=F('current_uses') + 1
            )

        first_purchase = None
        for item in payment.order.items.select_related('test_bank').all():
            purchase, created = Purchase.objects.get_or_create(
                payment=payment,
                test_bank=item.test_bank,
                defaults={
                    'user': payment.user,
                    'is_active': True,
                },
            )
            if created:
                purchase.create_user_access()
                if first_purchase is None:
                    first_purchase = purchase
        return first_purchase or payment.purchases.order_by('id').first()
    else:
        if not payment.test_bank:
            return None
        purchase, created = Purchase.objects.get_or_create(
            payment=payment,
            test_bank=payment.test_bank,
            defaults={
                'user': payment.user,
                'is_active': True,
            },
        )
        if created:
            purchase.create_user_access()
        return purchase
