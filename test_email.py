#!/usr/bin/env python
"""
Test script to verify email configuration is working.

Run this script to test if emails can be sent:
python test_email.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testbank_platform.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Test sending an email."""
    print("=" * 60)
    print("Testing Email Configuration")
    print("=" * 60)
    
    print(f"\nEmail Backend: {settings.EMAIL_BACKEND}")
    print(f"Email Host: {settings.EMAIL_HOST}")
    print(f"Email Port: {settings.EMAIL_PORT}")
    print(f"Email User: {settings.EMAIL_HOST_USER}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Use TLS: {settings.EMAIL_USE_TLS}")
    
    # Get test email from user
    test_email = input("\nEnter your email address to test: ").strip()
    
    if not test_email:
        print("No email provided. Exiting.")
        return
    
    print(f"\nSending test email to {test_email}...")
    
    try:
        send_mail(
            subject='Test Email from Exam Stellar',
            message='This is a test email to verify email configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
        print(f"Please check your inbox (and spam folder) at {test_email}")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        print("\nCommon issues:")
        print("1. Microsoft/Outlook requires correct password or App Password if 2FA enabled")
        print("2. Verify EMAIL_HOST is correct (smtp-mail.outlook.com or smtp.office365.com)")
        print("3. Check firewall/network settings")
        print("4. Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct")
        print("5. If using Office 365, try smtp.office365.com instead")
        print("\nFor Microsoft accounts:")
        print("- Use regular password if 2FA is disabled")
        print("- Use App Password if 2FA is enabled")
        print("- App Password: https://account.microsoft.com/security")

if __name__ == '__main__':
    test_email()
