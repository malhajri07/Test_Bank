"""
URL configuration for payments app.

Routes for:
- Creating checkout sessions
- Payment success/cancel callbacks
- Stripe webhook endpoint (CSRF exempt)
- Payment and purchase detail pages
"""

from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    # Payment flow
    path('checkout/<slug:testbank_slug>/', views.create_checkout, name='create_checkout'),
    path('checkout-package/<slug:package_slug>/', views.create_checkout_package, name='create_checkout_package'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),

    # Webhook endpoints (CSRF exempt)
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),

    # Tap Payments
    path('tap/create-charge/', views.tap_create_charge_ajax, name='tap_create_charge'),
    path('tap/callback/<int:payment_id>/', views.tap_callback, name='tap_callback'),

    # Payment and purchase details
    path('payment/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('purchases/', views.purchase_list, name='purchase_list'),
]

