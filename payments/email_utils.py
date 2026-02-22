"""
Email utilities for payment-related emails.

This module provides functions for sending payment invoices and notifications.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def send_payment_invoice(payment):
    """
    Send payment invoice email to the customer.
    
    This function:
    1. Renders the invoice email template
    2. Sends the email to the customer's email address
    3. Uses info@examstellar.com as the sender
    
    Args:
        payment: Payment instance with succeeded status
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get customer email
        customer_email = payment.user.email
        if not customer_email:
            logger.warning(f'User {payment.user.id} has no email address, cannot send invoice')
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
        email_subject = f'Payment Invoice - {payment.test_bank.title}'
        email_html = render_to_string('payments/emails/payment_invoice.html', {
            'payment': payment,
            'site_url': site_url,
        })
        
        # Create plain text version
        email_text = f"""
Payment Invoice - {payment.test_bank.title}

Invoice #{payment.id} | Date: {payment.created_at.strftime('%B %d, %Y')}

Dear {payment.user.get_full_name() or payment.user.username},

Thank you for your purchase! This email confirms your payment and serves as your invoice.

Payment Details:
- Payment ID: #{payment.id}
- Transaction ID: {payment.provider_payment_id or 'N/A'}
- Payment Date: {payment.created_at.strftime('%B %d, %Y %I:%M %p')}
- Payment Method: {payment.get_payment_provider_display()}
- Status: Paid

Test Bank: {payment.test_bank.title}

Total Paid: ${payment.amount:.2f} {payment.currency.upper()}

You now have full access to this test bank. You can start practicing immediately from your dashboard.

Access your test bank: {site_url}/test-bank/{payment.test_bank.slug}/

If you have any questions or need assistance, please don't hesitate to contact our support team.

---
This is an automated invoice from Exam Stellar.
Visit our website: {site_url}
Contact Support: {site_url}/contact/

© {payment.created_at.year} Exam Stellar. All rights reserved.
"""
        
        # Send email
        from_email = 'info@examstellar.com'
        
        send_mail(
            subject=email_subject,
            message=email_text,
            html_message=email_html,
            from_email=from_email,
            recipient_list=[customer_email],
            fail_silently=False,
        )
        
        logger.info(f'Payment invoice email sent to {customer_email} for payment {payment.id}')
        return True
        
    except Exception as e:
        logger.error(f'Error sending payment invoice email: {str(e)}', exc_info=True)
        return False
