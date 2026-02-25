# Email Troubleshooting Guide

**Issue:** Emails are not being sent from `info@examstellar.com`

**Error:** `SMTPAuthenticationError: (535, b'5.7.139 Authentication unsuccessful, SmtpClientAuthentication is disabled for the Tenant')`

---

## Problem Identified

Microsoft/Outlook has **disabled SMTP authentication** for your tenant. This is a security feature that Microsoft has enabled by default for many accounts.

---

## Solutions

### Option 1: Enable SMTP AUTH in Microsoft 365 Admin Center (Recommended)

1. **Log in to Microsoft 365 Admin Center:**
   - Go to https://admin.microsoft.com
   - Sign in with your admin account

2. **Navigate to Settings:**
   - Go to **Settings** → **Mail**
   - Or search for "SMTP AUTH"

3. **Enable SMTP AUTH:**
   - Find **Authenticated SMTP** settings
   - Enable **"Enable Authenticated SMTP"** for the tenant
   - Or enable it for specific mailboxes (including `info@examstellar.com`)

4. **Wait for propagation:**
   - Changes may take 15-60 minutes to propagate

5. **Test again:**
   - Try sending an email again

**Reference:** https://aka.ms/smtp_auth_disabled

---

### Option 2: Use App Password (If MFA is enabled)

If your account has Multi-Factor Authentication (MFA) enabled:

1. **Generate App Password:**
   - Go to https://account.microsoft.com/security
   - Sign in with `info@examstellar.com`
   - Go to **Security** → **Advanced security options**
   - Under **App passwords**, create a new app password
   - Copy the generated password

2. **Update .env file:**
   ```env
   EMAIL_HOST_PASSWORD=[App Password Here]
   ```

3. **Restart Django server**

---

### Option 3: Use Gmail SMTP (Alternative)

If you prefer to use Gmail instead:

1. **Enable 2-Step Verification** on Gmail account
2. **Generate App Password:**
   - Go to Google Account → Security → App passwords
   - Generate password for "Mail"

3. **Update .env file:**
   ```env
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=[Gmail App Password]
   DEFAULT_FROM_EMAIL=info@examstellar.com
   ```

---

### Option 4: Use Email Service Provider (Production Recommended)

For production, consider using:
- **SendGrid** (Free tier: 100 emails/day)
- **Mailgun** (Free tier: 5,000 emails/month)
- **Amazon SES** (Pay as you go)
- **Postmark** (Paid, but reliable)

**Example with SendGrid:**
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=[SendGrid API Key]
DEFAULT_FROM_EMAIL=info@examstellar.com
```

---

## Current Email Configuration

**From .env:**
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=info@examstellar.com
EMAIL_HOST_PASSWORD=Mido_5632343
DEFAULT_FROM_EMAIL=info@examstellar.com
```

**Status:** ❌ Not working - SMTP AUTH disabled

---

## Testing Email Configuration

After fixing the configuration, test with:

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail(
    subject='Test Email',
    message='Test message',
    from_email='info@examstellar.com',
    recipient_list=['mohasalemhaj@gmail.com'],
    fail_silently=False,
)
```

---

## Quick Fix: Use Console Backend for Development

For development/testing, you can use console backend to see emails in terminal:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

This will print emails to the console instead of sending them.

---

## Next Steps

1. **Immediate:** Enable SMTP AUTH in Microsoft 365 Admin Center
2. **Alternative:** Switch to Gmail SMTP or email service provider
3. **Development:** Use console backend to test email templates
4. **Production:** Set up proper email service (SendGrid, Mailgun, etc.)

---

*Last Updated: February 22, 2026*
