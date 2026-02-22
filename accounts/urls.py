"""
URL configuration for accounts app.

Routes for:
- User registration
- Login/logout (using Django's built-in views)
- Profile viewing and editing
- User dashboard
"""

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('register/', views.register, name='register'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    
    # Login/Logout (using custom login view to check activation)
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Password reset flow (using Django's built-in views)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('accounts:password_reset_done'),
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete'),
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Profile and dashboard
    path('profile/<int:pk>/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Language switching
    path('set-language/', views.set_language, name='set_language'),
]

