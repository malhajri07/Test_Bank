# 💳 Payment Processing Error Troubleshooting Guide

**Date:** February 23, 2026  
**Status:** Error Handling Improved

---

## Common Payment Errors & Solutions

### 1. Stripe Keys Not Configured

**Error Message:**
- `"Payment processing is not configured. Please contact support."`
- `"STRIPE_SECRET_KEY is not configured"`

**Solution:**
1. Check `.env` file has Stripe keys:
   ```env
   STRIPE_PUBLIC_KEY=pk_test_...
   STRIPE_SECRET_KEY=sk_test_...
   ```

2. Verify keys are loaded in settings:
   ```python
   # In Django shell
   from django.conf import settings
   print(settings.STRIPE_PUBLIC_KEY)
   print(settings.STRIPE_SECRET_KEY)
   ```

3. Restart Django server after updating `.env`

---

### 2. Invalid Stripe API Key

**Error Message:**
- `"Invalid API Key provided"`
- `"No such API key"`

**Solution:**
- Verify you're using the correct key (test vs live)
- Check key hasn't been revoked in Stripe Dashboard
- Ensure no extra spaces or characters in `.env` file
- Test keys start with `pk_test_` and `sk_test_`

---

### 3. Price Validation Error

**Error Message:**
- `"Test bank price must be greater than 0"`
- `"Invalid price"`

**Solution:**
- Check test bank price is set correctly in admin
- For free test banks, price should be `0.00` (handled separately)
- Ensure price is a valid decimal number

---

### 4. Checkout Session Creation Failed

**Error Message:**
- `"Payment processing error: [Stripe error message]"`
- `"Custom checkout failed, falling back to hosted"`

**Common Causes:**
- Invalid currency code
- Invalid return URLs
- Stripe API connection issues
- Rate limiting

**Solution:**
1. **Check Currency:**
   ```python
   # Verify currency setting
   STRIPE_CURRENCY = 'usd'  # Should be valid ISO code
   ```

2. **Check URLs:**
   - Ensure `ALLOWED_HOSTS` includes your domain
   - Verify `request.build_absolute_uri()` works correctly
   - Check HTTPS vs HTTP (Stripe requires HTTPS in production)

3. **Check Stripe Dashboard:**
   - View logs in Stripe Dashboard → Developers → Logs
   - Check for API errors or rate limits

---

### 5. Webhook Signature Verification Failed

**Error Message:**
- `"Webhook signature verification failed"`
- `"Invalid signature"`

**Solution:**
1. **Set Webhook Secret:**
   ```env
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

2. **Get Webhook Secret from Stripe:**
   - Go to Stripe Dashboard → Developers → Webhooks
   - Click on your webhook endpoint
   - Copy "Signing secret"

3. **Verify Webhook URL:**
   - Must be publicly accessible (not localhost)
   - Use ngrok or similar for local testing
   - Format: `https://yourdomain.com/payments/webhook/`

---

### 6. Payment Already Processed

**Error Message:**
- `"Payment already succeeded"`
- Duplicate purchase attempts

**Solution:**
- This is normal behavior - prevents duplicate charges
- Check if user already has access
- Verify `UserTestAccess` record exists

---

### 7. Custom Checkout Mode Issues

**Error Message:**
- `"Custom checkout failed, falling back to hosted"`

**Solution:**
- System automatically falls back to hosted checkout
- This is expected behavior if custom checkout fails
- Check browser console for JavaScript errors
- Verify Stripe.js is loaded correctly

---

## Debugging Steps

### Step 1: Check Logs

**Django Logs:**
```bash
# Check Django server logs for error messages
# Look for lines starting with "ERROR" or "Stripe API error"
```

**Stripe Dashboard:**
1. Go to https://dashboard.stripe.com/test/logs
2. Filter by your API key
3. Check recent failed requests

### Step 2: Verify Configuration

**Check Settings:**
```python
# In Django shell
python manage.py shell

from django.conf import settings
print("Public Key:", settings.STRIPE_PUBLIC_KEY[:20] + "...")
print("Secret Key:", settings.STRIPE_SECRET_KEY[:20] + "...")
print("Currency:", settings.STRIPE_CURRENCY)
```

### Step 3: Test Payment Flow

1. **Test Free Access:**
   - Create test bank with `price: 0.00`
   - Should grant access immediately without Stripe

2. **Test Paid Access:**
   - Create test bank with `price: 10.00`
   - Use Stripe test card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits

### Step 4: Check Error Messages

**Common Stripe Error Types:**
- `InvalidRequestError` - Invalid parameters
- `AuthenticationError` - Invalid API key
- `APIConnectionError` - Network issues
- `CardError` - Card declined
- `RateLimitError` - Too many requests

---

## Code Fixes Applied

### 1. Fixed Duplicate Exception Handling ✅

**Issue:** Two `except Exception` blocks (unreachable code)

**Fix:** 
- Removed duplicate exception handler
- Added specific `stripe.error.StripeError` handler
- Improved error message extraction

### 2. Improved Fallback Logic ✅

**Issue:** Fallback to hosted checkout could also fail silently

**Fix:**
- Added try-except around fallback
- Better error logging
- User-friendly error messages

---

## Testing Payment Flow

### Test Cards (Stripe Test Mode)

**Success:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., `12/34`)
- CVC: Any 3 digits (e.g., `123`)

**Decline:**
- Card: `4000 0000 0000 0002`
- Expiry: Any future date
- CVC: Any 3 digits

**3D Secure:**
- Card: `4000 0027 6000 3184`
- Requires authentication

---

## Environment Variables Checklist

Ensure these are set in `.env`:

```env
# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...  # Optional for local dev

# Stripe Currency (in settings.py)
STRIPE_CURRENCY=usd
```

---

## Common Issues & Quick Fixes

### Issue: "Payment processing is not configured"

**Fix:** Add Stripe keys to `.env` file

### Issue: "Invalid API Key"

**Fix:** 
- Check key format (starts with `pk_test_` or `sk_test_`)
- Verify no extra spaces
- Check key hasn't been revoked

### Issue: "Custom checkout failed"

**Fix:** 
- System auto-falls back to hosted checkout
- Check browser console for JavaScript errors
- Verify Stripe.js CDN is loading

### Issue: Webhook not working

**Fix:**
- Set `STRIPE_WEBHOOK_SECRET` in `.env`
- Use ngrok for local testing
- Verify webhook URL is publicly accessible

---

## Error Logging

All payment errors are logged with:
- Error message
- Stack trace (`exc_info=True`)
- User-friendly message displayed to user

**Check Logs:**
```python
# Django logs will show:
# ERROR: Stripe API error: [error message]
# ERROR: Error creating checkout session: [error message]
```

---

## Getting Help

If error persists:

1. **Check Django Logs:**
   - Look for full error traceback
   - Note the exact error message

2. **Check Stripe Dashboard:**
   - View API logs
   - Check for rate limits
   - Verify account status

3. **Test with Stripe CLI:**
   ```bash
   stripe listen --forward-to localhost:8000/payments/webhook/
   ```

4. **Provide Error Details:**
   - Full error message
   - When it occurs (checkout creation, payment success, etc.)
   - Test bank details (price, etc.)
   - Browser console errors (if any)

---

## Files Modified

- ✅ `payments/views.py` - Fixed duplicate exception handling
- ✅ `PAYMENT_ERROR_TROUBLESHOOTING.md` - This guide

---

*Last Updated: February 23, 2026*
