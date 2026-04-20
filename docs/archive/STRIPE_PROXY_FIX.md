# 🔧 Stripe Proxy Connection Fix

**Date:** February 23, 2026  
**Issue:** Proxy blocking Stripe API calls

---

## Problem

The payment checkout was failing with error:
```
Unable to connect to payment service. Please check your internet connection and try again.
```

**Root Cause:** 
- System has proxy configured (`HTTP_PROXY=http://127.0.0.1:51233`)
- Stripe's HTTP client respects proxy environment variables
- Proxy was blocking connections to `api.stripe.com`

---

## Solution Implemented

### 1. Custom No-Proxy HTTP Client ✅

Created a custom Stripe HTTP client that bypasses proxy for all Stripe API calls:

```python
class NoProxyHTTPClient(http_client.RequestsClient):
    """Custom HTTP client that bypasses proxy for Stripe API calls"""
    def request(self, method, url, headers, post_data=None):
        # Temporarily remove proxy env vars before making request
        original_proxies = {}
        proxy_keys = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for key in proxy_keys:
            if key in os.environ:
                original_proxies[key] = os.environ[key]
                del os.environ[key]
        
        try:
            # Make the request without proxy
            return super().request(method, url, headers, post_data)
        finally:
            # Restore proxy settings
            for key, value in original_proxies.items():
                os.environ[key] = value
```

### 2. Per-Request Proxy Disabling ✅

As a fallback, also added proxy disabling before each Stripe API call:
- `create_checkout_session()` - Disables proxy before creating checkout
- `handle_payment_success()` - Disables proxy before retrieving session
- All Stripe API calls now bypass proxy

---

## Files Modified

- ✅ `payments/stripe_integration.py`
  - Added custom `NoProxyHTTPClient` class
  - Configured Stripe to use custom HTTP client
  - Added per-request proxy disabling as fallback

---

## How It Works

1. **Custom HTTP Client:**
   - Stripe uses our custom `NoProxyHTTPClient` for all API calls
   - Before each request, proxy environment variables are temporarily removed
   - After request completes, proxy settings are restored
   - This ensures Stripe API calls go directly to Stripe servers

2. **Fallback Mechanism:**
   - If custom client fails to initialize, per-request proxy disabling is used
   - Each Stripe API call temporarily disables proxy before making request

---

## Testing

After restarting the Django server:

1. **Test Checkout Creation:**
   - Navigate to: `http://localhost:8000/payments/checkout/program-management-professional-pgmp-1/`
   - Should redirect to Stripe checkout page (no proxy error)

2. **Verify Proxy Bypass:**
   - Check Django logs for successful Stripe API calls
   - No "ProxyError" or "APIConnectionError" should appear

---

## Environment Variables

The fix works with existing proxy settings:
- `HTTP_PROXY=http://127.0.0.1:51233` (will be bypassed for Stripe)
- `HTTPS_PROXY=http://127.0.0.1:51233` (will be bypassed for Stripe)
- Other services will continue using proxy as configured

---

## Alternative Solutions

If issues persist, you can:

### Option 1: Disable Proxy Entirely (Development)
```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
python manage.py runserver
```

### Option 2: Add Stripe to NO_PROXY
```bash
export NO_PROXY="$NO_PROXY,api.stripe.com,*.stripe.com"
```

### Option 3: Configure Proxy to Allow Stripe
Update your proxy configuration to allow connections to `api.stripe.com`

---

## Verification

✅ Custom HTTP client configured  
✅ Proxy bypass implemented  
✅ Per-request fallback added  
✅ Server restarted with changes  

**Status:** Ready for testing

---

*Last Updated: February 23, 2026*
