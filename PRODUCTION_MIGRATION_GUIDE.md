# Production Migration Guide

This guide covers migrating the new email verification feature to production.

## New Features Added

1. **Email Verification System**
   - New `EmailVerificationToken` model
   - Email verification required for new registrations
   - Verification emails sent from `info@examstellar.com`

2. **Payment Invoice Emails**
   - Automatic invoice emails sent after successful payment
   - Sent from `info@examstellar.com`

## Migration Steps

### Step 1: Run Database Migrations

```bash
# Activate your virtual environment
source venv/bin/activate

# Create migration (if not already created)
python manage.py makemigrations accounts

# Apply migrations
python manage.py migrate accounts
```

### Step 2: Update Environment Variables

Update your production `.env` file with email configuration:

```env
# Email Configuration for Production
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=info@examstellar.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=info@examstellar.com
```

**Important:** For Gmail:
1. Enable 2-factor authentication
2. Generate an App Password (not your regular password)
3. Use the App Password in `EMAIL_HOST_PASSWORD`

### Step 3: Verify Email Settings

Test email sending in production:

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

# Test email
send_mail(
    'Test Email',
    'This is a test email from Exam Stellar.',
    settings.DEFAULT_FROM_EMAIL,
    ['your-test-email@example.com'],
    fail_silently=False,
)
```

### Step 4: Update Production Settings

Ensure these settings are configured in production:

1. **DEBUG = False** (in production)
2. **ALLOWED_HOSTS** includes your domain
3. **Email backend** set to SMTP
4. **Stripe keys** are production keys (not test keys)

### Step 5: Test the Flow

1. **Registration Flow:**
   - Register a new user
   - Check email for verification link
   - Click link to activate account
   - Verify account is activated

2. **Payment Flow:**
   - Complete a test payment
   - Verify invoice email is received
   - Check email content and links

## Database Changes

### New Table: `accounts_emailverificationtoken`

```sql
CREATE TABLE accounts_emailverificationtoken (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES accounts_customuser(id),
    token VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE
);
```

## Rollback Plan (if needed)

If you need to rollback:

1. **Disable email verification temporarily:**
   - Comment out `user.is_active = False` in registration view
   - Users will be active immediately upon registration

2. **Keep existing users active:**
   - All existing users remain active
   - Only new registrations require verification

## Production Checklist

- [ ] Database migrations applied
- [ ] Email SMTP configured
- [ ] Email credentials tested
- [ ] Stripe production keys configured
- [ ] Email templates reviewed
- [ ] Registration flow tested
- [ ] Payment invoice flow tested
- [ ] Error handling verified
- [ ] Logging configured

## Support

If you encounter issues:

1. Check Django logs for email sending errors
2. Verify SMTP credentials
3. Check spam folder for verification emails
4. Ensure email domain is not blacklisted
