"""
Accounts app views for authentication, registration, profile management, and dashboard.

This module provides views for:
- User registration
- Login/logout
- Profile viewing and editing
- User dashboard showing purchased test banks and practice sessions
- Language switching
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
import logging

logger = logging.getLogger(__name__)
from .models import CustomUser, UserProfile, EmailVerificationToken
from .forms import UserRegistrationForm, UserProfileForm
from practice.models import UserTestAccess, UserTestSession
from catalog.models import TestBank
from .email_utils import send_verification_email, send_welcome_email
from payments.models import Payment, Purchase
from django.utils import timezone
from datetime import timedelta


def register(request):
    """
    User registration view.
    
    Handles both GET (show form) and POST (process registration).
    On successful registration:
    - Creates new user account (set as inactive)
    - Creates user profile
    - Creates email verification token
    - Sends verification email
    - Shows message to check email (does NOT log user in)
    """
    if request.user.is_authenticated:
        # Redirect authenticated users to dashboard
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Use transaction to ensure atomicity
            with transaction.atomic():
                # Create user but set as inactive until email is verified
                user = form.save(commit=False)
                user.is_active = False  # User must verify email before account is active
                user.save()
                
                # Create user profile with additional info
                UserProfile.objects.create(
                    user=user,
                    full_name=form.cleaned_data.get('full_name', ''),
                    phone_number=form.cleaned_data.get('phone_number', ''),
                    country=form.cleaned_data.get('country', ''),
                    preferred_language=form.cleaned_data.get('preferred_language', 'en'),
                )
                
                # Create email verification token
                token = EmailVerificationToken.generate_token()
                expires_at = timezone.now() + timedelta(days=7)  # Token expires in 7 days
                
                verification_token = EmailVerificationToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at,
                )
                
                # Send welcome email
                try:
                    send_welcome_email(user)
                except Exception as e:
                    logger.error(f'Error sending welcome email: {str(e)}')
                    # Don't fail registration if welcome email fails
                
                # Send verification email
                try:
                    send_verification_email(user, verification_token)
                    messages.success(
                        request,
                        _('Registration successful! Please check your email to activate your account. The activation link will expire in 7 days.')
                    )
                except Exception as e:
                    logger.error(f'Error sending verification email: {str(e)}')
                    messages.warning(
                        request,
                        _('Account created but verification email failed to send. Please contact support.')
                    )
                
                # Set user's language preference in session (for after activation)
                if form.cleaned_data.get('preferred_language'):
                    request.session['django_language'] = form.cleaned_data.get('preferred_language')
                
                # Redirect to login page with message
                return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def custom_login(request):
    """
    Custom login view that checks if account is activated.
    
    Shows appropriate message if account is not activated.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            # Try to authenticate
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Check if account is active
                if not user.is_active:
                    messages.error(
                        request,
                        _('Your account is not activated. Please check your email and click the activation link to activate your account.')
                    )
                    return render(request, 'accounts/login.html')
                
                # Account is active, log them in
                login(request, user)
                messages.success(request, _('Welcome back!'))
                
                # Redirect to next page or dashboard
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('accounts:dashboard')
            else:
                messages.error(request, _('Invalid username or password.'))
        else:
            messages.error(request, _('Please enter both username and password.'))
    
    return render(request, 'accounts/login.html')


def verify_email(request, token):
    """
    Email verification view.
    
    Activates user account when they click the verification link in their email.
    
    Args:
        token: Verification token from email link
    """
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        
        # Check if token is valid
        if not verification_token.is_valid():
            if verification_token.is_used:
                messages.error(request, _('This verification link has already been used.'))
            else:
                messages.error(request, _('This verification link has expired. Please request a new one.'))
            return redirect('accounts:login')
        
        # Activate user account
        user = verification_token.user
        user.is_active = True
        user.save()
        
        # Mark token as used
        verification_token.is_used = True
        verification_token.save()
        
        # Log user in automatically after verification
        login(request, user)
        
        messages.success(
            request,
            _('Email verified successfully! Your account has been activated. Welcome to Exam Stellar!')
        )
        
        return redirect('accounts:dashboard')
        
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, _('Invalid verification link. Please check your email and try again.'))
        return redirect('accounts:login')
    except Exception as e:
        logger.error(f'Error verifying email: {str(e)}')
        messages.error(request, _('An error occurred while verifying your email. Please try again or contact support.'))
        return redirect('accounts:login')


@login_required
def profile_view(request, pk):
    """
    User profile view and edit page.
    
    Shows user's profile information and allows editing.
    Only the profile owner can view/edit their profile.
    
    Args:
        pk: Primary key of the user whose profile to view
    """
    user = get_object_or_404(CustomUser, pk=pk)
    
    # Ensure user can only edit their own profile
    if request.user != user:
        messages.error(request, _('You do not have permission to view this profile.'))
        return redirect('accounts:dashboard')
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get all invoices (payments) for this user - both free and paid
    invoices = Payment.objects.filter(
        user=user,
        status='succeeded'  # Only show successful payments
    ).select_related('test_bank').order_by('-created_at')
    
    # Calculate totals for invoice summary
    from decimal import Decimal
    total_net = sum(Decimal(str(invoice.get_net_price())) for invoice in invoices)
    total_vat = sum(Decimal(str(invoice.get_vat_amount())) for invoice in invoices)
    total_amount = sum(Decimal(str(invoice.get_total_amount())) for invoice in invoices)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            
            # Update language preference if changed
            if 'preferred_language' in form.cleaned_data:
                new_language = form.cleaned_data['preferred_language']
                translation.activate(new_language)
                request.session['django_language'] = new_language
            
            messages.success(request, _('Profile updated successfully!'))
            return redirect('accounts:profile', pk=user.pk)
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/profile.html', {
        'user': user,
        'profile': profile,
        'form': form,
        'invoices': invoices,
        'total_net': total_net,
        'total_vat': total_vat,
        'total_amount': total_amount,
    })


@login_required
def dashboard(request):
    """
    User dashboard view.
    
    Displays:
    - Test banks user has purchased (from UserTestAccess)
    - Recent practice sessions with scores
    - Quick links to continue practice or view details
    
    This is the main landing page for authenticated users.
    """
    user = request.user
    
    # Get user's purchased test banks (active access only)
    # Optimized with select_related to avoid N+1 queries
    purchased_test_banks = TestBank.objects.filter(
        user_accesses__user=user,
        user_accesses__is_active=True
    ).select_related('category', 'certification').distinct()
    
    # Get recent practice sessions (last 10)
    # Already optimized with select_related
    recent_sessions = UserTestSession.objects.filter(
        user=user
    ).select_related('test_bank', 'test_bank__category', 'test_bank__certification').order_by('-started_at')[:10]
    
    # Calculate statistics
    total_sessions = UserTestSession.objects.filter(user=user).count()
    completed_sessions = UserTestSession.objects.filter(user=user, status='completed').count()
    
    # Calculate average score
    completed_with_scores = UserTestSession.objects.filter(
        user=user,
        status='completed',
        score__isnull=False
    )
    if completed_with_scores.exists():
        avg_score = sum(session.score for session in completed_with_scores) / completed_with_scores.count()
    else:
        avg_score = None
    
    return render(request, 'accounts/dashboard.html', {
        'purchased_test_banks': purchased_test_banks,
        'recent_sessions': recent_sessions,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'avg_score': avg_score,
    })


@require_POST
def set_language(request):
    """
    Language switching view.
    
    Allows users to switch between English and Arabic.
    Updates session language and user profile if authenticated.
    """
    language = request.POST.get('language', 'en')
    
    if language in ['en', 'ar']:
        translation.activate(language)
        request.session['django_language'] = language
        
        # Update user profile if authenticated
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                profile.preferred_language = language
                profile.save()
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(
                    user=request.user,
                    preferred_language=language
                )
        
        messages.success(request, _('Language changed successfully.'))
    
    # Redirect to the previous page or home
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return HttpResponseRedirect(next_url)
