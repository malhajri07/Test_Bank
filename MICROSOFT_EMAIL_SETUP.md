# Microsoft/Outlook Email Setup Guide

## SMTP Configuration for Microsoft/Outlook

### Step 1: Update .env File

Your `.env` file should have these settings:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=info@examstellar.com
EMAIL_HOST_PASSWORD=your-password-here
DEFAULT_FROM_EMAIL=info@examstellar.com
```

### Step 2: Microsoft Account Requirements

For Microsoft/Outlook email, you need:

1. **Microsoft Account Password**
   - Use your regular Microsoft account password
   - OR use an App Password if 2FA is enabled

2. **If 2FA is Enabled:**
   - Go to https://account.microsoft.com/security
   - Click "Advanced security options"
   - Under "App passwords", create a new app password
   - Use that app password in `EMAIL_HOST_PASSWORD`

### Step 3: Alternative SMTP Settings

If `smtp-mail.outlook.com` doesn't work, try:

**Option 1: Office 365**
```env
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

**Option 2: Outlook.com**
```env
EMAIL_HOST=smtp.live.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

### Step 4: Test Email Configuration

Run the test script:

```bash
python test_email.py
```

### Common Issues

1. **"Authentication failed"**
   - Make sure you're using the correct password
   - If 2FA is enabled, use an App Password
   - Check that the email address is correct

2. **"Connection timeout"**
   - Check firewall settings
   - Verify port 587 is not blocked
   - Try port 25 as alternative (less secure)

3. **"Relay access denied"**
   - Make sure you're using the correct SMTP server
   - Verify your account allows SMTP access

### Security Note

- Never commit your `.env` file with passwords
- Use App Passwords when 2FA is enabled
- Consider using environment variables in production

### Production Recommendation

For production, consider using:
- **SendGrid** (recommended)
- **Mailgun**
- **Amazon SES**
- **Microsoft Graph API** (for Office 365)

These services are more reliable than SMTP for production applications.
