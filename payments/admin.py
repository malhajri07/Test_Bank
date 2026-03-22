"""
Admin configuration for payments app.

Registers Order, OrderItem, Coupon, CouponProduct, Payment, and Purchase models.
"""

from django.contrib import admin

from .models import Coupon, CouponProduct, Order, OrderItem, Payment, Purchase


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
