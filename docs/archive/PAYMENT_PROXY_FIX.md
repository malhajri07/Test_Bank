# 🔧 Payment Proxy Connection Issue Fix

**Date:** February 23, 2026  
**Issue:** Proxy error preventing Stripe API calls

---

## Problem Identified

The payment checkout page is failing due to a **proxy connection error** when trying to connect to Stripe's API:

```
ProxyError: Unable to connect to proxy
OSError: Tunnel connection failed: 403 Forbidden
```

This prevents the creation of Stripe Checkout sessions.

---

## Root Cause

The system is trying to use a proxy server to connect to Stripe's API (`api.stripe.com`), but:
1. The proxy connection is failing (403 Forbidden)
2. This blocks all Stripe API calls
3. Payment checkout cannot be created

---

## Solutions

### Option 1: Disable Proxy for Stripe (Recommended)

Configure Stripe to bypass proxy settings:

**Add to `.env` file:**
```env
# Disable proxy for Stripe API calls
NO_PROXY=api.stripe.com,*.stripe.com
```

**Or set environment variable:**
```bash
export NO_PROXY=api.stripe.com,*.stripe.com
```

### Option 2: Configure Stripe HTTP Client

Modify `payments/stripe_integration.py` to explicitly disable proxy:

```python
import stripe
import os

# Disable proxy for Stripe
os.environ['NO_PROXY'] = 'api.stripe.com,*.stripe.com'

# Or configure Stripe HTTP client
stripe.default_http_client = stripe.http_client.RequestsClient(
    verify_ssl_certs=True,
    proxy=None  # Explicitly disable proxy
)
```

### Option 3: Fix Proxy Configuration

If you need to use a proxy:

1. **Check proxy settings:**
   ```bash
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   echo $http_proxy
   echo $https_proxy
   ```

2. **Verify proxy credentials** (if required)

3. **Test proxy connection:**
   ```bash
   curl -x $HTTP_PROXY https://api.stripe.com
   ```

### Option 4: Use Direct Connection (Development)

For local development, disable proxy entirely:

```bash
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy
```

Then restart Django server.

---

## Code Fixes Applied

### ✅ Fixed Exception Handling

**Issue:** `stripe.error.StripeError` was not accessible, causing `AttributeError`

**Fix:** Updated imports to use direct error classes:
```python
from stripe.error import StripeError, APIConnectionError, APIError, InvalidRequestError
```

**Files Updated:**
- `payments/stripe_integration.py`
- `payments/views.py`

### ✅ Improved Error Messages

Added user-friendly error messages for connection issues:
- "Unable to connect to payment service. Please check your internet connection and try again."

---

## Testing

After applying the fix:

1. **Test checkout creation:**
   ```bash
   python manage.py shell
   ```
   ```python
   from catalog.models import TestBank
   from payments.stripe_integration import create_checkout_session
   # ... test code
   ```

2. **Check Django logs** for any remaining errors

3. **Test payment flow** in browser:
   - Navigate to test bank detail page
   - Click "Purchase" button
   - Should redirect to Stripe checkout page

---

## Environment Variables

Ensure these are set in `.env`:

```env
# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# Disable proxy for Stripe (if needed)
NO_PROXY=api.stripe.com,*.stripe.com
```

---

## Quick Fix Command

To quickly disable proxy for Django server:

```bash
# In terminal before starting Django
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
python manage.py runserver
```

Or add to your shell profile (`~/.bashrc` or `~/.zshrc`):
```bash
export NO_PROXY=api.stripe.com,*.stripe.com
```

---

## Verification

After applying fixes, verify:

1. ✅ Stripe API calls work without proxy errors
2. ✅ Checkout session creation succeeds
3. ✅ Users can complete payment flow
4. ✅ Error handling works correctly

---

## Additional Notes

- **Production:** Ensure proxy settings are correctly configured for production environment
- **Development:** Proxy is usually not needed for local development
- **Stripe API:** Requires direct HTTPS connection to `api.stripe.com`

---

*Last Updated: February 23, 2026*
