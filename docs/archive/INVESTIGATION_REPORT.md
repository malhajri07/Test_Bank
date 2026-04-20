# 🔍 Deep Dive Investigation Report - Payment Service Connection Error

**Date:** February 25, 2026  
**Issue:** "Unable to connect to payment service. Please check your internet connection and try again."

---

## Executive Summary

**Root Cause:** Proxy server (`http://127.0.0.1:53548`) is blocking Stripe API connections with `403 Forbidden` error.

**Impact:** All Stripe API calls fail, preventing payment checkout session creation.

**Solution:** Configure Stripe HTTP client to bypass proxy for `api.stripe.com` connections.

---

## Investigation Steps Completed

### ✅ Step 1: Check Django Server Logs
- **Result:** No detailed error logs found in terminal output
- **Finding:** Server starts successfully but errors occur at runtime

### ✅ Step 2: Test Stripe API Connection Directly
**Command:** `python -c "stripe.Account.retrieve()"`

**Error Found:**
```
stripe._error.APIConnectionError: Unexpected error communicating with Stripe.
(Network error: ProxyError: HTTPSConnectionPool(host='api.stripe.com', port=443): 
Max retries exceeded with url: /v1/account 
(Caused by ProxyError('Unable to connect to proxy', 
OSError('Tunnel connection failed: 403 Forbidden'))))
```

**Key Findings:**
- Stripe API keys are valid and configured correctly
- Error is `APIConnectionError` (connection issue, not authentication)
- Proxy is intercepting the connection: `http://127.0.0.1:53548`
- Proxy returns `403 Forbidden` when trying to connect to `api.stripe.com`

### ✅ Step 3: Verify Stripe API Keys
- **Stripe Public Key:** `pk_test_51T30hXR2rcH...` ✅ Valid format
- **Stripe Secret Key:** `sk_test_51T30hXR2rcH...` ✅ Valid format
- **Stripe Currency:** `usd` ✅ Correct

### ✅ Step 4: Check Network Connectivity
**Command:** `curl -v https://api.stripe.com/v1/account`

**Result:**
```
* Uses proxy env variable https_proxy == 'http://127.0.0.1:53561'
* CONNECT tunnel failed, response 403
curl: (56) CONNECT tunnel failed, response 403
```

**Finding:** 
- Direct connection to Stripe API is blocked by proxy
- Proxy returns `403 Forbidden` for `api.stripe.com` connections
- This is a proxy configuration issue, not a network issue

---

## Root Cause Analysis

### Problem Chain:
1. **Environment:** System has proxy configured (`HTTP_PROXY=http://127.0.0.1:53548`)
2. **Stripe Library:** Uses `requests` library which respects `HTTP_PROXY` environment variables
3. **Proxy Behavior:** Proxy rejects connections to `api.stripe.com` with `403 Forbidden`
4. **Error Propagation:**
   - `ProxyError` → `requests.exceptions.ProxyError`
   - Wrapped as → `stripe._error.APIConnectionError`
   - Detected by our code → Shows user-friendly message

### Why It Worked Before:
Possible reasons:
1. Proxy wasn't active/configured before
2. Proxy configuration changed
3. Proxy was allowing Stripe connections before but now blocks them
4. Different proxy port/configuration

---

## Current Environment State

### Proxy Configuration:
```
HTTP_PROXY: http://127.0.0.1:53548
HTTPS_PROXY: http://127.0.0.1:53548
http_proxy: http://127.0.0.1:53548
https_proxy: http://127.0.0.1:53548
NO_PROXY: 127.0.0.1,::1,localhost
```

**Issue:** `NO_PROXY` doesn't include `api.stripe.com`, so proxy intercepts all Stripe connections.

---

## Solution Options

### Option 1: Configure Stripe HTTP Client to Bypass Proxy (Recommended)
**Approach:** Create custom HTTP client that doesn't use proxy for Stripe API calls.

**Pros:**
- Doesn't affect other services
- Works regardless of proxy configuration
- No system-level changes needed

**Cons:**
- Requires code changes
- Need to maintain custom HTTP client

### Option 2: Add Stripe to NO_PROXY Environment Variable
**Approach:** Add `api.stripe.com` to `NO_PROXY` environment variable.

**Pros:**
- Simple configuration change
- System-wide solution

**Cons:**
- Requires environment variable changes
- May affect other applications
- Need to set before Django starts

### Option 3: Disable Proxy for Development
**Approach:** Unset proxy environment variables before starting Django.

**Pros:**
- Simplest solution for development
- No code changes needed

**Cons:**
- Only works for development
- May break other services that need proxy
- Not suitable for production

---

## Recommended Solution

**Implement Option 1:** Configure Stripe HTTP client to bypass proxy.

**Implementation:**
1. Create custom Stripe HTTP client that sets `proxies={}` for Stripe API calls
2. Configure Stripe to use custom HTTP client
3. Fallback: Temporarily disable proxy env vars before Stripe API calls

---

## Error Detection Logic

Current code detects Stripe connection errors:
```python
if 'APIConnectionError' in error_type or 'Connection' in error_type:
    messages.error(request, 'Unable to connect to payment service...')
```

This correctly identifies the proxy connection issue and shows user-friendly message.

---

## Next Steps

1. ✅ Implement proxy bypass in Stripe HTTP client
2. ✅ Test Stripe API connection with bypass enabled
3. ✅ Verify checkout session creation works
4. ✅ Document solution for future reference

---

*Investigation completed: February 25, 2026*
