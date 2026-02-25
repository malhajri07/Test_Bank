# Gmail SMTP Setup - Quick Guide

## ✅ Configuration Updated

Your `.env` file has been updated to use Gmail SMTP:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=info@examstellar.com
EMAIL_HOST_PASSWORD=YOUR_GMAIL_APP_PASSWORD_HERE  ← NEEDS TO BE UPDATED
DEFAULT_FROM_EMAIL=info@examstellar.com
```

---

## 🔑 Step 1: Get Gmail App Password

**Important:** Gmail requires an **App Password** (not your regular password) for SMTP access.

### If `info@examstellar.com` is a Gmail/Google Workspace account:

1. **Go to Google Account Security:**
   - Visit: https://myaccount.google.com/security
   - Sign in with `info@examstellar.com`

2. **Enable 2-Step Verification** (if not already enabled):
   - Click **2-Step Verification**
   - Follow the setup process

3. **Generate App Password:**
   - Go back to Security page
   - Click **App passwords** (under "Signing in to Google")
   - Select **Mail** as the app
   - Select **Other (Custom name)** as device
   - Enter name: "Exam Stellar Django"
   - Click **Generate**
   - **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

4. **Update `.env` file:**
   ```env
   EMAIL_HOST_PASSWORD=abcdefghijklmnop
   ```
   ⚠️ **Remove all spaces** from the App Password!

---

### If `info@examstellar.com` is NOT a Gmail account:

You have two options:

**Option A: Use a different Gmail account for sending**
1. Use your personal Gmail account (e.g., `yourname@gmail.com`)
2. Generate App Password for that account
3. Update `.env`:
   ```env
   EMAIL_HOST_USER=yourname@gmail.com
   EMAIL_HOST_PASSWORD=[App Password from yourname@gmail.com]
   DEFAULT_FROM_EMAIL=info@examstellar.com  # This can stay the same
   ```

**Option B: Use Google Workspace**
- If `info@examstellar.com` is a Google Workspace account, follow the same steps as Gmail
- Make sure SMTP is enabled in your Google Workspace admin console

---

## 🧪 Step 2: Test Email Configuration

After updating `EMAIL_HOST_PASSWORD` in `.env`, restart your Django server and test:

```bash
# Restart server
python manage.py runserver

# In another terminal, test email:
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail(
    subject='Test Email from Exam Stellar',
    message='This is a test email.',
    from_email='info@examstellar.com',
    recipient_list=['mohasalemhaj@gmail.com'],
    fail_silently=False,
)
```

---

## 📧 Step 3: Resend Welcome Email

Once email is working, you can resend the welcome email to `mohasalemhaj@gmail.com`:

```bash
python manage.py shell
```

```python
from accounts.models import CustomUser
from accounts.email_utils import send_welcome_email

user = CustomUser.objects.get(email='mohasalemhaj@gmail.com')
send_welcome_email(user)
print("Welcome email sent!")
```

---

## ❌ Common Issues

### "Username and Password not accepted"
- ✅ Make sure you're using an **App Password**, not your regular password
- ✅ Remove all spaces from the App Password
- ✅ Verify 2-Step Verification is enabled

### "Less secure app access"
- ✅ Don't enable "Less secure app access" - use App Password instead
- ✅ App Passwords are more secure

### "Connection refused" or "Timeout"
- ✅ Check firewall settings
- ✅ Verify port 587 is not blocked
- ✅ Try port 465 with `EMAIL_USE_SSL=True` instead of `EMAIL_USE_TLS=True`

---

## 🚀 Production Recommendation

For production, consider using:
- **SendGrid** (Free: 100 emails/day)
- **Mailgun** (Free: 5,000 emails/month)
- **Amazon SES** (Pay as you go)

Gmail SMTP is fine for development, but has daily sending limits.

---

*Last Updated: February 23, 2026*
