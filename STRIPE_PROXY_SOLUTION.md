# 🔧 Stripe Proxy Issue - Final Solution

**Date:** February 25, 2026  
**Issue:** Proxy blocking all Stripe API calls with 403 Forbidden

---

## Problem Summary

The proxy server (`http://127.0.0.1:53548`) is blocking Stripe API calls:
- Error: `ProxyError: Tunnel connection failed: 403 Forbidden`
- All Stripe API calls fail
- Payment checkout cannot be created

**Root Cause:** urllib3 (used by requests/Stripe) reads proxy environment variables when connection pools are created, not per-request. Simply removing env vars doesn't help because pools are already initialized.

---

## Solution Options

### ✅ Option 1: Disable Proxy for Django Process (RECOMMENDED)

**Best for:** Development environment

**How to do it:**

1. **Before starting Django server, unset proxy:**
   ```bash
   unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
   python manage.py runserver
   ```

2. **Or create a startup script** (`start_server.sh`):
   ```bash
   #!/bin/bash
   unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
   cd /Users/mohammedalhajri/Test_Bank
   source venv/bin/activate
   python manage.py runserver
   ```

3. **Make it executable:**
   ```bash
   chmod +x start_server.sh
   ./start_server.sh
   ```

### ✅ Option 2: Add Stripe to NO_PROXY (System-Wide)

**Best for:** When you need proxy for other services

**How to do it:**

1. **Add to your shell profile** (`~/.zshrc` or `~/.bashrc`):
   ```bash
   export NO_PROXY="$NO_PROXY,api.stripe.com,*.stripe.com"
   ```

2. **Or set before starting Django:**
   ```bash
   export NO_PROXY="$NO_PROXY,api.stripe.com,*.stripe.com"
   python manage.py runserver
   ```

### ✅ Option 3: Configure Proxy to Allow Stripe

**Best for:** When proxy is required for other services

**How to do it:**

1. **Configure your proxy** (depends on proxy software):
   - Allow connections to `api.stripe.com`
   - Allow HTTPS connections on port 443
   - Remove 403 restrictions for Stripe domain

2. **Or use proxy authentication** if required

### ✅ Option 4: Use Environment-Specific Configuration

**Best for:** Different proxy settings for dev/prod

**How to do it:**

1. **Create `.env.dev`** (development - no proxy):
   ```env
   # No proxy settings
   ```

2. **Create `.env.prod`** (production - with proxy):
   ```env
   HTTP_PROXY=http://proxy.example.com:8080
   HTTPS_PROXY=http://proxy.example.com:8080
   NO_PROXY=api.stripe.com,*.stripe.com
   ```

3. **Load appropriate .env file** based on environment

---

## Recommended Immediate Fix

**For Development (Right Now):**

```bash
# Stop current server
lsof -ti:8000 | xargs kill -9

# Start without proxy
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
cd /Users/mohammedalhajri/Test_Bank
source venv/bin/activate
python manage.py runserver
```

This will allow Stripe API calls to work immediately.

---

## Why Code-Based Solutions Don't Work

1. **urllib3 Connection Pools:** Created at import time with proxy settings baked in
2. **Environment Variables:** Read when pools are created, not per-request
3. **Stripe Library:** Uses requests/urllib3 internally, hard to override

**The only reliable solution is to configure the environment before Python/Django starts.**

---

## Code Changes Made

The code has been updated to:
- ✅ Handle errors gracefully (no more AttributeError crashes)
- ✅ Show user-friendly error messages
- ✅ Attempt proxy bypass (though limited by urllib3 behavior)

**But the proxy must be disabled at the system/environment level for it to work.**

---

## Testing After Fix

1. **Start server without proxy** (see Option 1 above)
2. **Test payment checkout:**
   - Navigate to: `http://localhost:8000/payments/checkout/program-management-professional-pgmp-1/`
   - Should redirect to Stripe checkout page
3. **Verify Stripe API calls work:**
   - Check Django logs for successful API calls
   - No proxy errors should appear

---

## Long-Term Solution

For production, configure:
1. **Proxy server** to allow Stripe connections, OR
2. **NO_PROXY environment variable** to exclude Stripe domains, OR  
3. **Separate network path** for Stripe API calls

---

*Last Updated: February 25, 2026*
