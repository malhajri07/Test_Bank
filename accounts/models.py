"""
Accounts app models for user authentication and profiles.

This module defines:
- CustomUser: Extended user model for better flexibility
- UserProfile: Additional user information (full_name, phone, country, language preference)
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class CustomUser(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Justification for custom user model:
    - Provides flexibility to add custom fields directly to User model in the future
    - Better than using UserProfile FK approach as it avoids extra joins
    - Allows customization of authentication fields if needed
    - Industry best practice for production Django applications
    
    Currently uses all default fields from AbstractUser (username, email, password, etc.)
    Additional user information is stored in UserProfile model via OneToOne relationship.
    """
    
    # Role choices for CMS and content management
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('content_manager', 'Content Manager'),
        ('editor', 'Editor'),
        ('user', 'Regular User'),
    ]
    
    # User role for CMS permissions
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='Role',
        help_text='User role for content management permissions'
    )
    
    # Using default fields from AbstractUser:
    # username, email, password, first_name, last_name, is_staff, is_active, date_joined, etc.
    
    def __str__(self):
        """String representation of the user."""
        return self.username
    
    def get_absolute_url(self):
        """Get URL for user's profile page."""
        return reverse('accounts:profile', kwargs={'pk': self.pk})
    
    def is_cms_admin(self):
        """Check if user is a CMS administrator."""
        return self.role == 'admin' or self.is_superuser
    
    def is_content_manager(self):
        """Check if user can manage content."""
        return self.role in ['admin', 'content_manager'] or self.is_superuser
    
    def is_editor(self):
        """Check if user can edit content."""
        return self.role in ['admin', 'content_manager', 'editor'] or self.is_superuser
    
    def can_publish_content(self):
        """Check if user can publish content."""
        return self.role in ['admin', 'content_manager'] or self.is_superuser


class UserProfile(models.Model):
    """
    Extended user profile information.
    
    Stores additional user data that is not part of the core authentication:
    - Full name (can be different from first_name/last_name)
    - Phone number for contact
    - Country for localization/regional features
    - Preferred language for RTL/LTR support (English/Arabic)
    
    Relationship: OneToOne with CustomUser (one user has one profile)
    """
    
    # OneToOne relationship ensures one profile per user
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='User'
    )
    
    # Full name field - can be different from first_name/last_name
    full_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Full Name',
        help_text='User\'s full name'
    )
    
    # Phone number for contact and verification
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Phone Number',
        help_text='Contact phone number'
    )
    
    # Country for localization and regional features
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Country',
        help_text='User\'s country'
    )
    
    # Language preference for RTL/LTR support
    # 'en' for English (LTR), 'ar' for Arabic (RTL)
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ar', 'Arabic'),
    ]
    
    preferred_language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='en',
        verbose_name='Preferred Language',
        help_text='User\'s preferred language for UI display'
    )
    
    # Timestamps for tracking profile creation and updates
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for UserProfile model."""
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        """String representation of the profile."""
        return f"Profile for {self.user.username}"
    
    def get_absolute_url(self):
        """Get URL for profile detail page."""
        return reverse('accounts:profile', kwargs={'pk': self.user.pk})


class EmailVerificationToken(models.Model):
    """
    Email verification token model.
    
    Stores verification tokens for email activation.
    Each user gets a unique token that expires after a certain time.
    """
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='email_verification',
        verbose_name='User'
    )
    
    token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='Verification Token',
        help_text='Unique token for email verification'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    expires_at = models.DateTimeField(
        verbose_name='Expires At',
        help_text='Token expiration time (default: 7 days)'
    )
    
    is_used = models.BooleanField(
        default=False,
        verbose_name='Is Used',
        help_text='Whether this token has been used'
    )
    
    class Meta:
        """Meta options for EmailVerificationToken model."""
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        """String representation of the token."""
        return f"Verification token for {self.user.username}"
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at
    
    @staticmethod
    def generate_token():
        """Generate a secure random token."""
        import secrets
        return secrets.token_urlsafe(32)
