# 📧 Outlook SMTP Configuration Guide

**Date:** February 25, 2026  
**Email Provider:** Microsoft Outlook/Office 365

---

## Overview

This guide explains how to configure Django to send emails using Outlook/Office 365 SMTP servers.

---

## Outlook SMTP Settings

### For Outlook.com / Hotmail.com / Live.com Accounts:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password-or-app-password
DEFAULT_FROM_EMAIL=your-email@outlook.com
```

### For Office 365 Business/Enterprise Accounts:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yourdomain.com
EMAIL_HOST_PASSWORD=your-password-or-app-password
DEFAULT_FROM_EMAIL=your-email@yourdomain.com
```

---

## Step-by-Step Setup

### Step 1: Enable SMTP AUTH in Outlook

**Important:** Microsoft may disable SMTP AUTH by default. You need to enable it:

1. **For Personal Accounts (Outlook.com):**
   - Go to https://account.microsoft.com/security
   - Sign in with your Outlook account
   - Enable "Two-step verification" (recommended)
   - Generate an "App Password" if 2FA is enabled

2. **For Business/Enterprise Accounts:**
   - Contact your IT administrator
   - SMTP AUTH must be enabled in Exchange Online
   - Admin needs to enable it in Microsoft 365 admin center

### Step 2: Generate App Password (If 2FA is Enabled)

If you have two-factor authentication enabled:

1. Go to https://account.microsoft.com/security
2. Click "Advanced security options"
3. Under "App passwords", click "Create a new app password"
4. Copy the generated password (you'll use this instead of your regular password)

### Step 3: Update `.env` File

Edit `/Users/mohammedalhajri/Test_Bank/.env`:

```env
# Email Configuration (Outlook SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-app-password-or-password
DEFAULT_FROM_EMAIL=your-email@outlook.com
```

**Replace:**
- `your-email@outlook.com` with your actual Outlook email address
- `your-app-password-or-password` with your password or app password

### Step 4: Restart Django Server

After updating `.env`, restart the Django server:

```bash
# Stop current server
lsof -ti:8000 | xargs kill -9

# Start server (changes will be loaded)
source venv/bin/activate
python manage.py runserver
```

---

## Common SMTP Servers

### Outlook.com / Hotmail.com / Live.com:
- **SMTP Server:** `smtp-mail.outlook.com`
- **Port:** `587` (TLS) or `465` (SSL)
- **Security:** TLS (recommended)

### Office 365 Business:
- **SMTP Server:** `smtp.office365.com`
- **Port:** `587` (TLS) or `465` (SSL)
- **Security:** TLS (recommended)

### Alternative Ports:
- **Port 587:** TLS (STARTTLS) - Recommended
- **Port 465:** SSL/TLS - Alternative
- **Port 25:** Usually blocked by ISPs

---

## Configuration Examples

### Example 1: Personal Outlook Account

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=john.doe@outlook.com
EMAIL_HOST_PASSWORD=YourAppPassword123
DEFAULT_FROM_EMAIL=john.doe@outlook.com
```

### Example 2: Office 365 Business Account

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=john.doe@company.com
EMAIL_HOST_PASSWORD=YourAppPassword123
DEFAULT_FROM_EMAIL=john.doe@company.com
```

### Example 3: Using SSL Instead of TLS

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@outlook.com
```

**Note:** Use `EMAIL_USE_SSL=True` with port 465, or `EMAIL_USE_TLS=True` with port 587.

---

## Troubleshooting

### Error: "SMTPAuthenticationError: (535, b'5.7.139 Authentication unsuccessful)"

**Cause:** SMTP AUTH is disabled for your account.

**Solution:**
1. **For Personal Accounts:**
   - Enable "Less secure app access" (if available)
   - Or enable 2FA and use App Password

2. **For Business Accounts:**
   - Contact IT admin to enable SMTP AUTH
   - Admin needs to run: `Set-TransportConfig -SmtpClientAuthenticationDisabled $false`

### Error: "Connection refused" or "Connection timeout"

**Cause:** Port or server address is incorrect.

**Solution:**
- Verify SMTP server: `smtp-mail.outlook.com` or `smtp.office365.com`
- Try port 587 with TLS first
- Check firewall/network settings

### Error: "Authentication failed"

**Cause:** Wrong password or username.

**Solution:**
- Use App Password if 2FA is enabled (not your regular password)
- Verify email address is correct
- Check for extra spaces in `.env` file

### Error: "STARTTLS extension not supported"

**Cause:** Server doesn't support TLS on port 587.

**Solution:**
- Try port 465 with SSL instead
- Change `EMAIL_USE_TLS=True` to `EMAIL_USE_SSL=True`

---

## Testing Email Configuration

### Test in Django Shell:

```bash
source venv/bin/activate
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

# Test email sending
send_mail(
    'Test Subject',
    'This is a test email from Django.',
    settings.DEFAULT_FROM_EMAIL,
    ['recipient@example.com'],
    fail_silently=False,
)
```

### Test with Management Command:

```bash
python manage.py sendtestemail recipient@example.com
```

---

## Security Best Practices

1. **Use App Passwords:** If 2FA is enabled, always use App Passwords
2. **Never Commit `.env`:** Keep `.env` file out of version control
3. **Use Environment Variables:** In production, use secure environment variable management
4. **Enable 2FA:** Always enable two-factor authentication for email accounts
5. **Regular Password Rotation:** Change passwords/app passwords regularly

---

## Current Configuration

Your current `.env` file is configured for **Gmail SMTP**. To switch to Outlook:

1. Update `.env` with Outlook settings (see Step 3 above)
2. Restart Django server
3. Test email sending

---

## Quick Reference

| Setting | Outlook.com | Office 365 |
|---------|-------------|-----------|
| SMTP Server | `smtp-mail.outlook.com` | `smtp.office365.com` |
| Port (TLS) | `587` | `587` |
| Port (SSL) | `465` | `465` |
| TLS/SSL | TLS (port 587) | TLS (port 587) |
| Authentication | Required | Required |
| App Password | Recommended | Recommended |

---

## Additional Resources

- [Microsoft Outlook SMTP Settings](https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-8361e398-8af4-4e97-b147-6c6c4ac95353)
- [Enable SMTP AUTH in Exchange Online](https://learn.microsoft.com/en-us/exchange/clients-and-mobile-in-exchange-online/authenticated-client-smtp-submission)
- [Create App Passwords](https://support.microsoft.com/en-us/account-billing/using-app-passwords-with-apps-that-don-t-support-two-step-verification-5896ed9b-4263-e681-128a-a6f2979a7944)

---

*Last Updated: February 25, 2026*
