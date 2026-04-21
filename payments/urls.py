"""
URL configuration for payments app.

Routes for:
- Shopping cart
- Creating Paylink checkout sessions
- Payment callback from Paylink
- Payment and purchase detail pages
"""

from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    # Cart
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<slug:testbank_slug>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:testbank_id>/', views.cart_remove, name='cart_remove'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),

    # Payment flow (single-item and package)
    path('checkout/<slug:testbank_slug>/', views.create_checkout, name='create_checkout'),
    path('checkout-package/<slug:package_slug>/', views.create_checkout_package, name='create_checkout_package'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),

    # Paylink callback (customer returns here after payment)
    path('paylink/callback/<int:payment_id>/', views.paylink_callback, name='paylink_callback'),

    # Payment and purchase details
    path('payment/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('purchases/', views.purchase_list, name='purchase_list'),
]
