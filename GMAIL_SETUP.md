# Gmail SMTP Setup Guide

## Error: "Username and Password not accepted"

This error occurs because Gmail requires **App Passwords** instead of your regular password when 2-Factor Authentication is enabled.

## Solution: Create a Gmail App Password

### Step 1: Enable 2-Factor Authentication

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click **2-Step Verification**
3. Follow the prompts to enable 2FA (if not already enabled)

### Step 2: Generate App Password

1. Go back to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click **App passwords**
   - If you don't see this option, make sure 2FA is enabled first
3. Select **Mail** as the app
4. Select **Other (Custom name)** as the device
5. Enter a name like "Exam Stellar Django"
6. Click **Generate**
7. Copy the 16-character password (it will look like: `abcd efgh ijkl mnop`)

### Step 3: Update .env File

Replace `EMAIL_HOST_PASSWORD` in your `.env` file with the App Password:

```env
EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

**Important:** 
- Remove spaces from the App Password
- Use the 16-character password, NOT your regular Gmail password
- Keep this password secure

### Step 4: Restart Django Server

After updating the `.env` file, restart your Django server:

```bash
# Stop server (Ctrl+C)
python manage.py runserver
```

### Step 5: Test Again

Run the test script:

```bash
python test_email.py
```

## Alternative: Use Different Email Provider

If Gmail continues to cause issues, consider:

1. **SendGrid** (recommended for production)
2. **Mailgun**
3. **Amazon SES**
4. **Office 365**

## Troubleshooting

### Still getting errors?

1. **Verify App Password is correct:**
   - Make sure there are no spaces
   - Copy the entire 16-character password

2. **Check email address:**
   - Make sure `EMAIL_HOST_USER` matches your Gmail address exactly
   - Use the full email: `info@examstellar.com` (if it's a Gmail account)

3. **Try with your personal Gmail first:**
   - Test with your personal Gmail account first
   - Once working, switch to `info@examstellar.com`

4. **Check Gmail account settings:**
   - Make sure "Less secure app access" is NOT needed (use App Password instead)
   - Verify 2FA is enabled

## For Production

For production, consider using:
- **SendGrid** (free tier: 100 emails/day)
- **Mailgun** (free tier: 5,000 emails/month)
- **Amazon SES** (very affordable)

These services are more reliable than Gmail SMTP for production applications.
