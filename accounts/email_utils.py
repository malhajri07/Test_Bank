"""
Email utilities for account-related emails.

This module provides functions for sending:
- Welcome email with verification code on signup
- Verification-only email (resend)
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


def _get_site_url():
    """Resolve the base site URL for use in email links."""
    try:
        from django.contrib.sites.models import Site
        current_site = Site.objects.get_current()
        domain = current_site.domain
        return f'https://{domain}' if not domain.startswith('http') else domain
    except Exception:
        if settings.ALLOWED_HOSTS:
            host = settings.ALLOWED_HOSTS[0]
            if host.startswith('http'):
                return host
            return f'http://{host}:8000' if settings.DEBUG else f'https://{host}'
        return 'http://localhost:8000' if settings.DEBUG else 'https://examstellar.com'


def send_verification_email(user, verification_token):
    """
    Send email verification email to the user.

    Renders the verification email template with activation link and code.
    """
    try:
        if not user.email:
            logger.warning(f'User {user.id} has no email address, cannot send verification email')
            return False

        site_url = _get_site_url()
        verification_url = f"{site_url}{reverse('accounts:verify_email', kwargs={'token': verification_token.token})}"

        # Extract a short code from the token for display (first 8 chars uppercase)
        verification_code = verification_token.token[:8].upper()

        email_subject = 'Activate Your Exam Stellar Account'
        email_html = render_to_string('accounts/emails/verification_email.html', {
            'user': user,
            'verification_url': verification_url,
            'verification_code': verification_code,
            'site_url': site_url,
            'token': verification_token,
        })

        email_text = (
            f"Activate Your Exam Stellar Account\n\n"
            f"Dear {user.get_full_name() or user.username},\n\n"
            f"Your verification code is: {verification_code}\n\n"
            f"Or click the link below to activate your account:\n{verification_url}\n\n"
            f"This link will expire in 7 days.\n\n"
            f"If you did not create an account, please ignore this email.\n\n"
            f"— Exam Stellar Team\n{site_url}"
        )

        send_mail(
            subject=email_subject,
            message=email_text,
            html_message=email_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f'Verification email sent to {user.email} for user {user.id}')
        return True

    except Exception as e:
        logger.error(f'Error sending verification email: {e}', exc_info=True)
        return False


def send_welcome_email(user):
    """
    Send welcome email to newly registered user.

    This is the primary signup email — it includes the verification code
    prominently so the user can authenticate and proceed with their account.
    """
    try:
        if not user.email:
            logger.warning(f'User {user.id} has no email address, cannot send welcome email')
            return False

        site_url = _get_site_url()

        # Get verification token for this user (created during registration)
        verification_code = None
        verification_url = None
        try:
            token_obj = user.email_verification
            verification_code = token_obj.token[:8].upper()
            verification_url = f"{site_url}{reverse('accounts:verify_email', kwargs={'token': token_obj.token})}"
        except Exception:
            logger.warning(f'No verification token found for user {user.id}')

        email_subject = 'Welcome to Exam Stellar — Verify Your Account'
        email_html = render_to_string('accounts/emails/welcome_email.html', {
            'user': user,
            'site_url': site_url,
            'verification_code': verification_code,
            'verification_url': verification_url,
        })

        email_text = (
            f"Welcome to Exam Stellar!\n\n"
            f"Dear {user.get_full_name() or user.username},\n\n"
            f"Thank you for joining Exam Stellar!\n\n"
        )
        if verification_code:
            email_text += (
                f"Your verification code is: {verification_code}\n\n"
                f"Or click this link to activate: {verification_url}\n\n"
            )
        email_text += (
            f"Once verified, you can:\n"
            f"- Browse and purchase test banks\n"
            f"- Practice exam questions\n"
            f"- Track your progress\n\n"
            f"— The Exam Stellar Team\n{site_url}"
        )

        send_mail(
            subject=email_subject,
            message=email_text,
            html_message=email_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f'Welcome email sent to {user.email} for user {user.id}')
        return True

    except Exception as e:
        logger.error(f'Error sending welcome email: {e}', exc_info=True)
        return False
