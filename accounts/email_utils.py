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


def send_welcome_email(user):
    """
    Send welcome email to newly registered user.
    
    This function:
    1. Renders the welcome email template
    2. Sends the email to the user's email address
    3. Uses info@examstellar.com as the sender
    
    Args:
        user: CustomUser instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get user email
        if not user.email:
            logger.warning(f'User {user.id} has no email address, cannot send welcome email')
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
        
        # Render email template
        email_subject = 'Welcome to Exam Stellar!'
        email_html = render_to_string('accounts/emails/welcome_email.html', {
            'user': user,
            'site_url': site_url,
        })
        
        # Create plain text version
        email_text = f"""
Welcome to Exam Stellar!

Dear {user.get_full_name() or user.username},

Thank you for joining Exam Stellar! We're thrilled to have you as part of our learning community. Your account has been successfully created and you're now ready to start your journey towards exam success.

What You Can Do Now:

📚 Explore Test Banks
Browse our extensive collection of test banks covering various certifications and subjects.

🎯 Practice Questions
Take practice tests and track your progress with detailed analytics and performance insights.

📊 Track Your Progress
Monitor your improvement over time with comprehensive progress reports and statistics.

💳 Purchase Premium Content
Unlock premium test banks and advanced features to accelerate your learning.

Next Steps:
1. Verify your email address by clicking the activation link we sent you
2. Complete your profile to personalize your experience
3. Browse our test banks and find the ones that match your goals
4. Start practicing and track your progress

Visit our website: {site_url}
Contact Support: {site_url}/contact/

If you have any questions or need assistance, our support team is here to help. Don't hesitate to reach out!

We're excited to be part of your learning journey. Good luck with your studies!

Best regards,
The Exam Stellar Team

---
This email was sent to {user.email}
If you did not create an account, please ignore this email.

© 2026 Exam Stellar. All rights reserved.
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
            
            logger.info(f'Welcome email sent successfully to {user.email} for user {user.id}')
            return True
        except Exception as email_error:
            logger.error(f'SMTP error sending welcome email: {str(email_error)}')
            # Re-raise to be caught by calling function
            raise
        
    except Exception as e:
        logger.error(f'Error sending welcome email: {str(e)}', exc_info=True)
        return False
