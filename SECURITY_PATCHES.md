# Security Hardening Patches — Apply in Order

**Target:** Test Bank Platform (Django 4.2+)
**Priority:** Production-blocking security fixes
**Scope:** Audit item 1 (Security + production hardening) from the 2026-04-17 audit
**Audience:** B2C / English / "sell test banks + deliver practice"

These patches are intended to be applied verbatim, in order. Each section has:
- **Why** — the risk being addressed
- **File** — the path to edit
- **Patch** — unified diff or full replacement block
- **Verify** — how to confirm the fix landed

Run `pytest` after applying all patches.

---

## 1. Force `SECRET_KEY` from environment, default `DEBUG=False`

**Why:** [settings.py:25](testbank_platform/settings.py:25) falls back to a hardcoded insecure key. [settings.py:28](testbank_platform/settings.py:28) defaults `DEBUG=True` — a missed env var in production ships debug mode (stack traces, admin hints).

**File:** `testbank_platform/settings.py`

**Patch (replace lines 23–30):**

```python
# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY must come from the environment. No insecure default.
SECRET_KEY = config('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        'SECRET_KEY environment variable is required. '
        'Generate one with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
    )

# SECURITY WARNING: don't run with debug turned on in production!
# Default to False — production-safe by default.
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=lambda v: [s.strip() for s in v.split(',')],
)
```

**Verify:** `unset SECRET_KEY; python manage.py check` — should raise `RuntimeError`.

---

## 2. Add `ProcessedWebhookEvent` model for idempotency

**Why:** Stripe/Tap retry webhooks on timeouts. [handle_webhook_event](payments/stripe_integration.py:403) only checks `payment.status != 'succeeded'`, which doesn't protect against concurrent processing of the same event ID (race) nor against out-of-order event delivery (refund arriving before success).

**File:** `payments/models.py` (append after `Purchase` class)

**Patch (append):**

```python
class ProcessedWebhookEvent(models.Model):
    """
    Tracks webhook events that have been processed, for idempotency.

    Prevents double-fulfillment when payment providers retry webhooks.
    Unique on (provider, event_id).
    """

    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('tap', 'Tap'),
    ]

    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        verbose_name='Provider',
    )
    event_id = models.CharField(
        max_length=255,
        verbose_name='Provider Event ID',
        help_text='e.g. evt_1Xxx for Stripe',
    )
    event_type = models.CharField(
        max_length=100,
        verbose_name='Event Type',
    )
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Processed Webhook Event'
        verbose_name_plural = 'Processed Webhook Events'
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'event_id'],
                name='unique_provider_event',
            ),
        ]
        indexes = [
            models.Index(fields=['provider', 'event_id']),
            models.Index(fields=['received_at']),
        ]

    def __str__(self):
        return f'{self.provider}:{self.event_id} ({self.event_type})'
```

**Generate migration:** `python manage.py makemigrations payments` → commit the generated file.

**Verify:** `python manage.py migrate`; admin lists the new model.

---

## 3. Idempotent Stripe webhook handler + refund support

**Why:** Adds (a) idempotency using the model above, (b) handler for `charge.refunded` / `payment_intent.refunded` that revokes access.

**File:** `payments/stripe_integration.py`

**Patch (replace `handle_webhook_event` function starting around line 403):**

```python
def handle_webhook_event(event):
    """
    Handle Stripe webhook events with idempotency and refund support.

    Events handled:
    - checkout.session.completed       → fulfill payment
    - payment_intent.succeeded         → fulfill payment
    - payment_intent.payment_failed    → mark payment failed
    - charge.refunded                  → revoke access
    - payment_intent.canceled          → mark payment cancelled

    Returns:
        tuple: (Payment instance or None, Purchase instance or None)
    """
    import logging
    from django.db import IntegrityError
    from .models import ProcessedWebhookEvent

    logger = logging.getLogger(__name__)

    event_id = event.get('id')
    event_type = event['type']
    event_data = event['data']['object']

    # Idempotency guard — record this event; if already seen, no-op.
    if event_id:
        try:
            ProcessedWebhookEvent.objects.create(
                provider='stripe',
                event_id=event_id,
                event_type=event_type,
            )
        except IntegrityError:
            logger.info(f'Duplicate Stripe event {event_id} ignored')
            return None, None

    if event_type == 'checkout.session.completed':
        session_id = event_data['id']
        return handle_payment_success(session_id)

    elif event_type == 'payment_intent.succeeded':
        payment_intent_id = event_data['id']
        try:
            payment = Payment.objects.get(provider_payment_id=payment_intent_id)
            if payment.status != 'succeeded':
                payment.status = 'succeeded'
                payment.save()
                fulfill_payment(payment)
                try:
                    send_payment_invoice(payment)
                except Exception as e:
                    logger.error(f'Failed to send payment invoice email: {e}')
                return payment, payment.purchases.order_by('id').first()
        except Payment.DoesNotExist:
            logger.warning(f'payment_intent.succeeded for unknown PI {payment_intent_id}')

    elif event_type == 'payment_intent.payment_failed':
        payment_intent_id = event_data['id']
        try:
            payment = Payment.objects.get(provider_payment_id=payment_intent_id)
            payment.status = 'failed'
            payment.save()
            return payment, None
        except Payment.DoesNotExist:
            pass

    elif event_type == 'payment_intent.canceled':
        payment_intent_id = event_data['id']
        try:
            payment = Payment.objects.get(provider_payment_id=payment_intent_id)
            payment.status = 'cancelled'
            payment.save()
            return payment, None
        except Payment.DoesNotExist:
            pass

    elif event_type == 'charge.refunded':
        payment_intent_id = event_data.get('payment_intent')
        if payment_intent_id:
            try:
                payment = Payment.objects.get(provider_payment_id=payment_intent_id)
                _handle_refund(payment)
                return payment, None
            except Payment.DoesNotExist:
                logger.warning(f'charge.refunded for unknown PI {payment_intent_id}')

    return None, None


def _handle_refund(payment):
    """
    Process a refund: mark order refunded, deactivate Purchase and UserTestAccess.

    Does NOT delete records — preserves audit trail. Access is revoked by flipping
    is_active=False on Purchase and UserTestAccess rows.
    """
    from django.db import transaction
    from practice.models import UserTestAccess

    with transaction.atomic():
        if payment.order:
            payment.order.status = 'refunded'
            payment.order.save(update_fields=['status', 'updated_at'])

        purchases = payment.purchases.all()
        for purchase in purchases:
            purchase.is_active = False
            purchase.save(update_fields=['is_active'])

            UserTestAccess.objects.filter(
                user=purchase.user,
                test_bank=purchase.test_bank,
            ).update(is_active=False)
```

**Also update `handle_payment_success`** to lock the payment row so concurrent webhooks can't both fulfill. Replace the body starting at `# Only process if payment is not already succeeded` (line ~376):

```python
from django.db import transaction

with transaction.atomic():
    payment = Payment.objects.select_for_update().get(
        provider_session_id=session_id,
    )
    if payment.status == 'succeeded':
        return payment, payment.purchases.order_by('id').first()

    payment.status = 'succeeded'
    pi = checkout_session.payment_intent
    if pi:
        payment.provider_payment_id = pi if isinstance(pi, str) else getattr(pi, 'id', None)
    payment.save()

    fulfill_payment(payment)

try:
    send_payment_invoice(payment)
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f'Failed to send payment invoice email: {e}')

return payment, payment.purchases.order_by('id').first()
```

**Verify:** Send the same webhook twice with `stripe fixtures trigger checkout.session.completed` — second call should log "Duplicate Stripe event ignored".

---

## 4. Idempotent Tap webhook + refund support

**Why:** Same reasoning as Stripe. Also, [tap_callback at payments/views.py:381](payments/views.py:381) fetches the payment with `payment_id` from the URL but only checks ownership *after* fulfillment runs — attacker with a valid Tap `tap_id` could trigger processing on another user's pending payment. Move the ownership check first.

**File:** `payments/views.py` — replace `tap_callback` (line 378–402):

```python
@login_required
def tap_callback(request, payment_id):
    """Handle return from Tap after payment (redirect with tap_id)."""
    tap_id = request.GET.get('tap_id')
    if not tap_id:
        messages.error(request, 'Invalid payment callback.')
        return redirect('accounts:dashboard')

    # Verify payment ownership BEFORE touching external state
    payment = Payment.objects.filter(pk=payment_id, user=request.user).first()
    if not payment:
        messages.error(request, 'Invalid payment.')
        return redirect('accounts:dashboard')

    try:
        payment, purchase = handle_tap_callback(tap_id, payment_id)
        if purchase:
            messages.success(
                request,
                f'Payment successful! You now have access to {payment.test_bank.title}.'
            )
            return redirect('catalog:testbank_detail', slug=payment.test_bank.slug)
        else:
            messages.warning(request, 'Payment was not completed. Please try again.')
            return redirect('catalog:testbank_detail', slug=payment.test_bank.slug)
    except Exception as e:
        logger.error(f'Tap callback error: {e}', exc_info=True)
        messages.error(request, 'An error occurred while processing your payment.')
        return redirect('accounts:dashboard')
```

**File:** `payments/tap_integration.py` — wrap `handle_tap_callback` body with the same idempotency/lock pattern:

```python
def handle_tap_callback(tap_id, payment_id):
    from django.db import transaction, IntegrityError
    from .models import ProcessedWebhookEvent, Payment

    # Idempotency — tap_id is the unique charge identifier
    try:
        ProcessedWebhookEvent.objects.create(
            provider='tap',
            event_id=tap_id,
            event_type='charge.captured',
        )
    except IntegrityError:
        import logging
        logging.getLogger(__name__).info(f'Duplicate Tap event {tap_id} ignored')
        payment = Payment.objects.get(pk=payment_id)
        return payment, payment.purchases.order_by('id').first()

    # ... existing logic wrapped in transaction.atomic() with select_for_update on payment
```

---

## 5. JSON body size caps on AJAX endpoints

**Why:** [practice/views.py:282, 316](practice/views.py:282) and the rate endpoint in `catalog/views.py` do `json.loads(request.body)` without a size limit → memory-exhaustion vector. Cap at 10 KB (enough for any legitimate AJAX payload).

**File:** `practice/views.py` — add utility at top, apply in `save_time` and `mark_for_review`:

```python
# Add near the top, after imports
MAX_AJAX_JSON_BYTES = 10 * 1024  # 10 KB


def _parse_json_body(request):
    """Safely parse JSON body with size cap. Returns (data, error_response)."""
    import json
    if len(request.body) > MAX_AJAX_JSON_BYTES:
        return None, JsonResponse({'error': 'Payload too large'}, status=413)
    try:
        return json.loads(request.body), None
    except (ValueError, TypeError):
        return None, JsonResponse({'error': 'Invalid JSON'}, status=400)
```

Replace the `import json; data = json.loads(request.body)` pattern in both `save_time` (line 282) and `mark_for_review` (line 316) with:

```python
data, err = _parse_json_body(request)
if err:
    return err
# then use `data` as before
```

**File:** `catalog/views.py` — same pattern in `rate_test_bank`.

**Verify:** `curl -X POST -d "$(python -c 'print("x"*20000)')" http://localhost:8000/practice/session/1/save-time/` → 413.

---

## 6. Rate limiting

**Why:** No protection against brute-force login, coupon-validation abuse, or AJAX flooding.

**Install:**

```
pip install django-ratelimit>=4.1
```

Append to `requirements.txt`:

```
django-ratelimit>=4.1.0
```

**Apply to auth views** — `accounts/views.py`:

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    ...

@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def register_view(request):
    ...

@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def password_reset_view(request):
    ...
```

**Apply to practice AJAX** — `practice/views.py`:

```python
@login_required
@ratelimit(key='user', rate='120/m', method='POST', block=True)
def save_answer(request, session_id):
    ...

@login_required
@ratelimit(key='user', rate='60/m', method='POST', block=True)
def save_time(request, session_id):
    ...
```

**Apply to coupon/contact** — `payments/views.py`, `catalog/views.py`:

```python
@ratelimit(key='ip', rate='10/m', method='GET', block=True)
def create_checkout(request, testbank_slug):
    ...

@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def contact(request):
    ...
```

**Verify:** Hammer `/accounts/login/` with 10 POSTs in a minute → last 5 return 429.

---

## 7. Enforce `SECURE_*` headers even under `DEBUG=False` correctly

Current [settings.py:277–286](testbank_platform/settings.py:277) is fine, but append CSP and referrer policy:

```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    X_FRAME_OPTIONS = 'DENY'
```

---

## 8. Unify `SECRET_KEY` wizardry for CI

In `env.example` add a commented generator hint:

```
# Generate with:
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=replace-me
DEBUG=False
```

---

## Post-apply checklist

- [ ] `python manage.py check --deploy` — note warnings, address `E` errors
- [ ] `python manage.py makemigrations payments && python manage.py migrate`
- [ ] `pytest -x` — no regressions
- [ ] Trigger `checkout.session.completed` twice via Stripe CLI → second is ignored
- [ ] Trigger `charge.refunded` → `UserTestAccess.is_active=False`, `Order.status='refunded'`
- [ ] Hit `/accounts/login/` 10x in a minute → 429 on last 5
- [ ] POST oversized body to `/practice/session/.../save-time/` → 413

---

## What this does NOT cover (deferred)

Call these out so nobody assumes they're handled:

- **Email verification unification** (allauth vs local `EmailVerificationToken`) — still duplicated
- **Cart / multi-item checkout UI** — model supports it, UI doesn't
- **Per-question domain tagging + weak-area analytics** — needs schema change
- **Question snapshot into UserAnswer** — historical correctness under question edits
- **Sentry / structured logging** — still console-only
- **2FA for staff** — not in scope here
- **CKEditor 4 → CKEditor 5 migration** — security advisory, separate effort
- **Repo noise cleanup** (`=0.25.0` files, 20+ stale audit docs, root-level scripts) — separate patch

Each of those is its own work item from the audit.
