"""
Payments app models for purchase transactions and payment processing.

This module defines models for:
- Order: Cart/checkout container (status: pending → paid → fulfilled → refunded)
- OrderItem: Line items linking Order to TestBank with quantity and price
- Coupon: Promo codes with usage limits and product applicability
- Payment: Tracks payment transactions with Stripe (or other providers)
- Purchase: Links successful payments to test bank purchases and grants access
"""

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone

from catalog.models import TestBank

User = get_user_model()


class Order(models.Model):
    """
    Order model representing a checkout/cart.

    Status flow: pending → paid → fulfilled → refunded
    Links to OrderItems (line items) and optionally to Payment.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='User',
        help_text='User who placed the order',
    )
    order_number = models.CharField(
        max_length=36,
        unique=True,
        verbose_name='Order Number',
        help_text='UUID for order reference',
    )
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('fulfilled', 'Fulfilled'),
        ('refunded', 'Refunded'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status',
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='Subtotal',
        help_text='Sum of line items before discount',
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='Discount Amount',
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='Tax/VAT Amount',
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name='Total Amount',
    )
    currency = models.CharField(
        max_length=3,
        default='usd',
        verbose_name='Currency',
    )
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        related_name='orders',
        null=True,
        blank=True,
        verbose_name='Coupon',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_number']),
        ]

    def __str__(self):
        return f"Order {self.order_number} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def calculate_totals(self, vat_rate=Decimal('0.15')):
        """Recalculate subtotal, tax, and total from order items and discount."""
        total = sum(
            (item.unit_price * item.quantity for item in self.items.all()),
            Decimal('0'),
        )
        self.subtotal = total
        after_discount = max(Decimal('0'), total - self.discount_amount)
        self.tax_amount = (after_discount * vat_rate).quantize(Decimal('0.01'))
        self.total_amount = (after_discount + self.tax_amount).quantize(Decimal('0.01'))
        self.save(update_fields=['subtotal', 'tax_amount', 'total_amount', 'updated_at'])


class OrderItem(models.Model):
    """Line item linking Order to TestBank with quantity and unit price."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Order',
    )
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='Test Bank',
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantity')
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Unit Price',
    )
    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Line Total',
        help_text='unit_price * quantity',
    )

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'test_bank'],
                name='unique_order_testbank',
            ),
        ]

    def __str__(self):
        return f"{self.order.order_number} - {self.test_bank.title} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.line_total = (self.unit_price * self.quantity).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)


class Coupon(models.Model):
    """
    Promo code for discounts.

    Supports percentage or fixed amount. Optional product restriction via CouponProduct.
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Code',
        help_text='Promo code (case-insensitive)',
    )
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPES,
        verbose_name='Discount Type',
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Discount Value',
        help_text='Percentage (e.g. 10) or fixed amount in currency',
    )
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Max Uses',
        help_text='Null = unlimited',
    )
    current_uses = models.PositiveIntegerField(
        default=0,
        verbose_name='Current Uses',
    )
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Valid From',
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Valid Until',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"

    def validate_for_order(self, subtotal, test_bank_ids=None):
        """
        Validate coupon and return discount amount.

        Returns:
            tuple: (discount_amount, error_message)
            If valid: (Decimal, None)
            If invalid: (Decimal('0'), "error message")
        """
        if not self.is_active:
            return Decimal('0'), 'Coupon is not active.'
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return Decimal('0'), 'Coupon is not yet valid.'
        if self.valid_until and now > self.valid_until:
            return Decimal('0'), 'Coupon has expired.'
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return Decimal('0'), 'Coupon usage limit reached.'
        if test_bank_ids is not None:
            products = CouponProduct.objects.filter(coupon=self)
            applies_to_all = products.filter(test_bank__isnull=True).exists()
            if not applies_to_all:
                allowed = set(p for p in products.values_list('test_bank_id', flat=True) if p is not None)
                if allowed and not (set(test_bank_ids) & allowed):
                    return Decimal('0'), 'Coupon does not apply to selected products.'
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value / 100).quantize(Decimal('0.01'))
        else:
            discount = min(self.discount_value, subtotal)
        return discount, None


class CouponProduct(models.Model):
    """Links Coupon to specific TestBank. Null test_bank = applies to all."""

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Coupon',
    )
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='coupon_products',
        verbose_name='Test Bank',
        null=True,
        blank=True,
        help_text='Null = applies to all products',
    )

    class Meta:
        verbose_name = 'Coupon Product'
        verbose_name_plural = 'Coupon Products'
        unique_together = [['coupon', 'test_bank']]


class Payment(models.Model):
    """
    Payment model tracking payment transactions.

    This model stores payment information from payment providers (e.g., Stripe):
    - Payment amount and currency
    - Provider-specific IDs (session ID, payment ID)
    - Payment status (created, pending, succeeded, failed)
    - Timestamps for tracking payment lifecycle

    Security Note: Never trust client-only data. Always verify payment status
    via webhook callbacks from the payment provider.
    """

    # ForeignKey to User - tracks which user made the payment
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='User',
        help_text='User who made the payment'
    )

    # Optional Order link (for Order-based checkout)
    order = models.ForeignKey(
        'Order',
        on_delete=models.SET_NULL,
        related_name='payments',
        verbose_name='Order',
        null=True,
        blank=True,
        help_text='Order this payment fulfills',
    )
    # ForeignKey to TestBank - primary product (kept for single-item backward compat)
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Test Bank',
        help_text='Test bank being purchased',
        null=True,
        blank=True,
    )

    # Payment amount
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Amount',
        help_text='Payment amount'
    )

    # Currency code (e.g., 'usd', 'eur')
    currency = models.CharField(
        max_length=3,
        default='usd',
        verbose_name='Currency',
        help_text='Payment currency code'
    )

    # Payment provider choices
    PAYMENT_PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('moyasar', 'Moyasar (legacy)'),  # historical records only; integration removed
        ('tap', 'Tap'),
        ('paypal', 'PayPal'),
        ('free', 'Free'),
        ('other', 'Other'),
    ]

    payment_provider = models.CharField(
        max_length=20,
        choices=PAYMENT_PROVIDER_CHOICES,
        default='stripe',
        verbose_name='Payment Provider',
        help_text='Payment gateway used'
    )

    # Provider-specific session ID (e.g., Stripe Checkout Session ID)
    provider_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Provider Session ID',
        help_text='Payment provider session ID (e.g., Stripe Checkout Session ID)'
    )

    # Provider-specific payment ID (e.g., Stripe Payment Intent ID)
    provider_payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Provider Payment ID',
        help_text='Payment provider payment ID (e.g., Stripe Payment Intent ID)'
    )

    # Payment status choices
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        verbose_name='Status',
        help_text='Current payment status'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        """Meta options for Payment model."""
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['provider_session_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        """String representation of the payment."""
        return f"{self.user.username} - {self.test_bank.title} - {self.status} - ${self.amount}"

    def is_successful(self):
        """Check if payment was successful."""
        return self.status == 'succeeded'

    def get_vat_rate(self):
        """Get VAT rate (15% default)."""
        from django.conf import settings
        return getattr(settings, 'VAT_RATE', 0.15)  # 15% VAT

    def get_net_price(self):
        """
        Get net price (VAT exclusive).

        The amount stored is the net price (VAT exclusive).
        For free items (amount = 0), returns 0.
        """
        return self.amount

    def get_vat_amount(self):
        """
        Calculate VAT amount (15% of net price).

        Returns 0 for free items (amount = 0).
        Example: Net price $5.00, VAT = $5.00 * 0.15 = $0.75
        """
        if self.amount == 0:
            return 0
        net_price = self.get_net_price()
        vat_rate = self.get_vat_rate()
        from decimal import Decimal
        return (Decimal(str(net_price)) * Decimal(str(vat_rate))).quantize(Decimal('0.01'))

    def get_total_amount(self):
        """
        Calculate total amount (net price + VAT).

        For free items, returns 0.
        Example: Net price $5.00, VAT $0.75, Total = $5.75
        """
        if self.amount == 0:
            return 0
        from decimal import Decimal
        net_price = Decimal(str(self.get_net_price()))
        vat_amount = Decimal(str(self.get_vat_amount()))
        return (net_price + vat_amount).quantize(Decimal('0.01'))

    def get_absolute_url(self):
        """Get URL for payment detail page."""
        return reverse('payments:payment_detail', kwargs={'pk': self.pk})


class Purchase(models.Model):
    """
    Purchase model linking successful payments to test bank purchases.

    This model represents a completed purchase transaction:
    - Links a Payment to a TestBank purchase
    - Creates UserTestAccess when purchase is completed
    - Tracks purchase timestamp and optional expiry

    Relationship:
    - One Payment can result in one Purchase
    - One Purchase grants access to one TestBank
    - Purchase creation triggers UserTestAccess creation
    """

    # ForeignKey to User - tracks which user made the purchase
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name='User',
        help_text='User who made the purchase'
    )

    # ForeignKey to TestBank - tracks which test bank was purchased
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name='Test Bank',
        help_text='Test bank that was purchased'
    )

    # ForeignKey to Payment - links purchase to payment transaction
    # One Payment can have multiple Purchases (e.g., when buying a package)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name='Payment',
        help_text='Payment transaction for this purchase'
    )

    # Timestamp when purchase was completed
    purchased_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Purchased At',
        help_text='When the purchase was completed'
    )

    # Active flag - allows deactivating purchase without deleting
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Whether purchase is active'
    )

    # Optional expiry date for subscription-based purchases
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Expires At',
        help_text='When purchase expires (null for lifetime access)'
    )

    class Meta:
        """Meta options for Purchase model."""
        verbose_name = 'Purchase'
        verbose_name_plural = 'Purchases'
        ordering = ['-purchased_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['test_bank', 'is_active']),
            models.Index(fields=['purchased_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['payment', 'test_bank'],
                name='unique_purchase_per_payment_testbank',
            ),
        ]

    def __str__(self):
        """String representation of the purchase."""
        return f"{self.user.username} - {self.test_bank.title} - {self.purchased_at}"

    def create_user_access(self):
        """
        Create or update UserTestAccess for this purchase.

        This method should be called after a successful purchase to grant
        the user access to the test bank.

        Returns:
            UserTestAccess: The created or updated access object
        """
        from practice.models import UserTestAccess

        attempts_allowed = getattr(self.test_bank, 'attempts_per_purchase', 3) or 3

        access, created = UserTestAccess.objects.get_or_create(
            user=self.user,
            test_bank=self.test_bank,
            defaults={
                'purchased_at': self.purchased_at,
                'expires_at': self.expires_at,
                'is_active': self.is_active,
                'attempts_allowed': attempts_allowed,
            }
        )

        if not created:
            access.purchased_at = self.purchased_at
            access.expires_at = self.expires_at
            access.is_active = self.is_active
            access.attempts_allowed = max(access.attempts_allowed, attempts_allowed)
            access.save()

        return access

    def get_absolute_url(self):
        """Get URL for purchase detail page."""
        return reverse('payments:purchase_detail', kwargs={'pk': self.pk})
