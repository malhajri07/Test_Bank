"""
Admin configuration for payments app.

Registers Order, OrderItem, Coupon, CouponProduct, Payment, Purchase, and
ProcessedWebhookEvent models. Provides a "Refund via Stripe" admin action.
"""

import logging

from django.contrib import admin, messages

from .models import (
    Coupon,
    CouponProduct,
    Order,
    OrderItem,
    Payment,
    ProcessedWebhookEvent,
    Purchase,
)

logger = logging.getLogger(__name__)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'currency', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('order_number', 'user__username')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at')


class CouponProductInline(admin.TabularInline):
    model = CouponProduct
    extra = 0


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'current_uses', 'max_uses', 'is_active', 'valid_until')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)
    inlines = [CouponProductInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""
    list_display = ('user', 'test_bank', 'amount', 'currency', 'payment_provider', 'status', 'created_at')
    list_filter = ('status', 'payment_provider', 'currency', 'created_at')
    search_fields = ('user__username', 'test_bank__title', 'provider_session_id', 'provider_payment_id')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    actions = ('refund_via_stripe',)

    fieldsets = (
        ('Payment Info', {
            'fields': ('user', 'order', 'test_bank', 'amount', 'currency', 'payment_provider')
        }),
        ('Provider Details', {
            'fields': ('provider_session_id', 'provider_payment_id', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.action(description='Refund selected payments via Stripe (full refund)')
    def refund_via_stripe(self, request, queryset):
        """
        Issue a full refund through Stripe for each selected payment.

        Webhook handler (charge.refunded) does the actual access revocation.
        We only kick off the refund here and update local status optimistically.
        """
        from .stripe_integration import _ensure_stripe_configured, _make_stripe_request
        import stripe

        attempted = succeeded = skipped = 0

        for payment in queryset:
            if payment.payment_provider != 'stripe':
                skipped += 1
                self.message_user(
                    request,
                    f'Skipped payment #{payment.id}: not a Stripe payment (provider={payment.payment_provider}).',
                    level=messages.WARNING,
                )
                continue
            if payment.status != 'succeeded':
                skipped += 1
                self.message_user(
                    request,
                    f'Skipped payment #{payment.id}: status is {payment.status}, not succeeded.',
                    level=messages.WARNING,
                )
                continue
            if not payment.provider_payment_id:
                skipped += 1
                self.message_user(
                    request,
                    f'Skipped payment #{payment.id}: no provider_payment_id recorded.',
                    level=messages.WARNING,
                )
                continue

            attempted += 1
            try:
                _ensure_stripe_configured()
                _make_stripe_request(
                    stripe.Refund.create,
                    payment_intent=payment.provider_payment_id,
                )
                succeeded += 1
                logger.info(f'Refund issued for payment {payment.id} (PI {payment.provider_payment_id})')
                # Note: status + access revocation happen via charge.refunded webhook.
            except Exception as e:
                logger.error(f'Refund failed for payment {payment.id}: {e}', exc_info=True)
                self.message_user(
                    request,
                    f'Refund failed for payment #{payment.id}: {e}',
                    level=messages.ERROR,
                )

        self.message_user(
            request,
            f'Refund: {succeeded} of {attempted} attempted succeeded '
            f'(skipped {skipped}). Access revocation will arrive via webhook.',
            level=messages.SUCCESS if succeeded else messages.INFO,
        )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """Admin interface for Purchase model."""
    list_display = ('user', 'test_bank', 'payment', 'purchased_at', 'expires_at', 'is_active')
    list_filter = ('is_active', 'purchased_at', 'expires_at')
    search_fields = ('user__username', 'test_bank__title')
    readonly_fields = ('purchased_at',)
    date_hierarchy = 'purchased_at'

    fieldsets = (
        ('Purchase Info', {
            'fields': ('user', 'test_bank', 'payment')
        }),
        ('Access Details', {
            'fields': ('purchased_at', 'expires_at', 'is_active')
        }),
    )


@admin.register(ProcessedWebhookEvent)
class ProcessedWebhookEventAdmin(admin.ModelAdmin):
    """Read-only view of webhook events processed — useful for idempotency debugging."""
    list_display = ('provider', 'event_id', 'event_type', 'received_at')
    list_filter = ('provider', 'event_type', 'received_at')
    search_fields = ('event_id', 'event_type')
    readonly_fields = ('provider', 'event_id', 'event_type', 'received_at')
    date_hierarchy = 'received_at'

    def has_add_permission(self, request):
        # Only the webhook handler should create these rows.
        return False
