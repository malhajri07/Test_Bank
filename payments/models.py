"""
Payments app models for purchase transactions and payment processing.

This module defines models for:
- Payment: Tracks payment transactions with Stripe (or other providers)
- Purchase: Links successful payments to test bank purchases and grants access
"""

from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from catalog.models import TestBank

User = get_user_model()


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
    
    # ForeignKey to TestBank - tracks which test bank is being purchased
    # Note: In future, this could be changed to support multiple test banks per payment
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Test Bank',
        help_text='Test bank being purchased'
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
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='purchase',
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
        
        # Get or create access, update if exists
        access, created = UserTestAccess.objects.get_or_create(
            user=self.user,
            test_bank=self.test_bank,
            defaults={
                'purchased_at': self.purchased_at,
                'expires_at': self.expires_at,
                'is_active': self.is_active,
            }
        )
        
        # Update if already exists
        if not created:
            access.purchased_at = self.purchased_at
            access.expires_at = self.expires_at
            access.is_active = self.is_active
            access.save()
        
        return access
    
    def get_absolute_url(self):
        """Get URL for purchase detail page."""
        return reverse('payments:purchase_detail', kwargs={'pk': self.pk})
