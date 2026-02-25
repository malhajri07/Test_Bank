"""
Email utilities for payment-related emails.

Sends invoice emails to customers after successful purchases.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

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


def send_payment_invoice(payment):
    """
    Send payment invoice email to the customer after a successful purchase.

    The invoice includes:
    - Invoice number and date
    - Test bank purchased (line item)
    - Subtotal, VAT breakdown, and total paid
    - Transaction details (payment method, Stripe ID)
    - CTA to start practicing

    Args:
        payment: Payment instance with status='succeeded'

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        customer_email = payment.user.email
        if not customer_email:
            logger.warning(f'User {payment.user.id} has no email, cannot send invoice')
            return False

        site_url = _get_site_url()

        email_subject = f'Invoice #{payment.id} — {payment.test_bank.title}'
        email_html = render_to_string('payments/emails/payment_invoice.html', {
            'payment': payment,
            'site_url': site_url,
        })

        email_text = (
            f"Invoice #{payment.id} — Exam Stellar\n"
            f"{'=' * 40}\n\n"
            f"Dear {payment.user.get_full_name() or payment.user.username},\n\n"
            f"Thank you for your purchase!\n\n"
            f"INVOICE DETAILS\n"
            f"Invoice:       #{payment.id}\n"
            f"Date:          {payment.created_at.strftime('%B %d, %Y')}\n"
            f"Status:        Paid\n\n"
            f"ITEM\n"
            f"{payment.test_bank.title}\n"
            f"Test Bank Access — Lifetime\n\n"
            f"Subtotal:      ${payment.get_net_price():.2f}\n"
            f"VAT ({payment.get_vat_rate_percent()}%):     ${payment.get_vat_amount():.2f}\n"
            f"Total Paid:    ${payment.get_total_amount():.2f} {payment.currency.upper()}\n\n"
            f"PAYMENT\n"
            f"Method:        {payment.get_payment_provider_display()}\n"
            f"Transaction:   {payment.provider_payment_id or 'N/A'}\n\n"
            f"Access your test bank: {site_url}/test-bank/{payment.test_bank.slug}/\n\n"
            f"— Exam Stellar Team\n"
            f"{site_url}\n"
        )

        send_mail(
            subject=email_subject,
            message=email_text,
            html_message=email_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            fail_silently=False,
        )

        logger.info(f'Invoice email sent to {customer_email} for payment #{payment.id}')
        return True

    except Exception as e:
        logger.error(f'Error sending invoice email: {e}', exc_info=True)
        return False
