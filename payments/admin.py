"""
Admin configuration for payments app.

Registers Payment and Purchase models with Django admin.
"""

from django.contrib import admin

from .models import Payment, Purchase


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
            'fields': ('user', 'test_bank', 'amount', 'currency', 'payment_provider')
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
