"""
Admin configuration for accounts app.

Registers CustomUser and UserProfile models with Django admin interface.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, UserProfile, EmailVerificationToken


# Inline admin for UserProfile (shown within User admin page)
class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile, displayed within CustomUser admin."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('full_name', 'phone_number', 'country', 'preferred_language')


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Admin interface for CustomUser model."""
    # Add UserProfile inline to User admin page
    inlines = (UserProfileInline,)
    
    # List display fields in admin list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # Add role field to user edit form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('CMS Role', {
            'fields': ('role',),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    list_display = ('user', 'full_name', 'phone_number', 'country', 'preferred_language', 'created_at')
    list_filter = ('country', 'preferred_language', 'created_at')
    search_fields = ('user__username', 'full_name', 'phone_number', 'country')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin interface for EmailVerificationToken model."""
    list_display = ('user', 'token', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('token', 'created_at')
    
    def has_add_permission(self, request):
        """Prevent manual creation of tokens (they should be created programmatically)."""
        return False
