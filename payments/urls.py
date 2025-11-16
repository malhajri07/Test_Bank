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
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    
    # Webhook endpoint (CSRF exempt - handled in view decorator)
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    
    # Payment and purchase details
    path('payment/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('purchases/', views.purchase_list, name='purchase_list'),
]

