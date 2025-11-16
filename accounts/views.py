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
from .models import CustomUser, UserProfile
from .forms import UserRegistrationForm, UserProfileForm
from practice.models import UserTestAccess, UserTestSession
from catalog.models import TestBank


def register(request):
    """
    User registration view.
    
    Handles both GET (show form) and POST (process registration).
    On successful registration:
    - Creates new user account
    - Creates user profile
    - Logs user in automatically
    - Redirects to dashboard
    """
    if request.user.is_authenticated:
        # Redirect authenticated users to dashboard
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Use transaction to ensure atomicity
            with transaction.atomic():
                # Create user
                user = form.save()
                
                # Create user profile with additional info
                UserProfile.objects.create(
                    user=user,
                    full_name=form.cleaned_data.get('full_name', ''),
                    phone_number=form.cleaned_data.get('phone_number', ''),
                    country=form.cleaned_data.get('country', ''),
                    preferred_language=form.cleaned_data.get('preferred_language', 'en'),
                )
                
                # Set user's language preference
                if form.cleaned_data.get('preferred_language'):
                    translation.activate(form.cleaned_data.get('preferred_language'))
                    request.session['django_language'] = form.cleaned_data.get('preferred_language')
                
                # Log user in automatically after registration
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                if user:
                    login(request, user)
                    messages.success(request, _('Registration successful! Welcome to Exam Stellar.'))
                    return redirect('accounts:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


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
    purchased_test_banks = TestBank.objects.filter(
        user_accesses__user=user,
        user_accesses__is_active=True
    ).distinct()
    
    # Get recent practice sessions (last 10)
    recent_sessions = UserTestSession.objects.filter(
        user=user
    ).select_related('test_bank').order_by('-started_at')[:10]
    
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
