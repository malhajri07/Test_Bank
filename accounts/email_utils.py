"""
Email utilities for account-related emails.

This module provides functions for sending account verification and notification emails.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def send_verification_email(user, verification_token):
    """
    Send email verification email to the user.
    
    This function:
    1. Renders the verification email template
    2. Sends the email to the user's email address
    3. Uses info@examstellar.com as the sender
    
    Args:
        user: CustomUser instance
        verification_token: EmailVerificationToken instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get user email
        if not user.email:
            logger.warning(f'User {user.id} has no email address, cannot send verification email')
            return False
        
        # Build site URL for links in email
        try:
            from django.contrib.sites.models import Site
            current_site = Site.objects.get_current()
            site_url = f'https://{current_site.domain}'
            if not site_url.startswith('http'):
                site_url = f'https://{site_url}'
        except Exception:
            # Fallback if Site framework not configured
            if settings.ALLOWED_HOSTS:
                host = settings.ALLOWED_HOSTS[0]
                if host.startswith('http'):
                    site_url = host
                else:
                    site_url = f'https://{host}' if not settings.DEBUG else f'http://{host}:8000'
            else:
                site_url = 'http://localhost:8000' if settings.DEBUG else 'https://examstellar.com'
        
        # Build verification URL
        verification_url = f"{site_url}{reverse('accounts:verify_email', kwargs={'token': verification_token.token})}"
        
        # Render email template
        email_subject = 'Activate Your Exam Stellar Account'
        email_html = render_to_string('accounts/emails/verification_email.html', {
            'user': user,
            'verification_url': verification_url,
            'site_url': site_url,
            'token': verification_token,
        })
        
        # Create plain text version
        email_text = f"""
Welcome to Exam Stellar!

Dear {user.get_full_name() or user.username},

Thank you for registering with Exam Stellar!

To complete your registration and activate your account, please click on the link below:

{verification_url}

This link will expire in 7 days.

If you did not create an account with Exam Stellar, please ignore this email.

Once your account is activated, you'll be able to:
- Access all test banks
- Track your practice sessions
- View your progress and scores
- Purchase premium test banks

If you have any questions, please contact our support team.

---
Exam Stellar Team
Visit our website: {site_url}
Contact Support: {site_url}/contact/
"""
        
        # Send email
        from_email = 'info@examstellar.com'
        
        try:
            send_mail(
                subject=email_subject,
                message=email_text,
                html_message=email_html,
                from_email=from_email,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f'Verification email sent successfully to {user.email} for user {user.id}')
            return True
        except Exception as email_error:
            logger.error(f'SMTP error sending verification email: {str(email_error)}')
            # Re-raise to be caught by calling function
            raise
        
    except Exception as e:
        logger.error(f'Error sending verification email: {str(e)}', exc_info=True)
        return False
