"""
IndexNow integration — push notifications to Bing, Yandex, Naver, Seznam,
and Yep when content changes. Replaces the old "wait for the next crawl"
model with sub-minute indexing latency on supported engines.

How it works
------------
1. Generate a 32-character hex key (use ``python -c "import secrets;
   print(secrets.token_hex(16))"``) and set it as ``INDEXNOW_KEY`` in the
   environment.
2. The /<key>.txt URL serves the key back as plain text — search engines
   fetch this once to verify ownership.
3. On every TestBank/BlogPost/Page save, a post_save signal calls
   ``ping_indexnow(url)`` which POSTs the URL list to api.indexnow.org.
   Failures are logged and never raised — SEO must never block writes.

Reference
---------
- Spec: https://www.indexnow.org/documentation
- Bing endpoint: https://www.bing.com/indexnow
- Yandex endpoint: https://yandex.com/indexnow
- Generic endpoint (recommended): https://api.indexnow.org/IndexNow

We use the generic endpoint because it fans the notification out to every
participating engine in one request.
"""
from __future__ import annotations

import logging
from typing import Iterable
from urllib.parse import urlparse

import httpx
from django.conf import settings
from django.http import Http404, HttpResponse

log = logging.getLogger(__name__)

INDEXNOW_ENDPOINT = 'https://api.indexnow.org/IndexNow'
TIMEOUT_SECONDS = 5


def _key() -> str:
    return getattr(settings, 'INDEXNOW_KEY', '') or ''


def _site_domain() -> str:
    return getattr(settings, 'SITE_DOMAIN', 'https://www.examstellar.com').rstrip('/')


def key_file_view(request, key: str):
    """Serve the IndexNow ownership-verification key at /<key>.txt.

    Returns the key as plain text only when the requested key matches the
    configured INDEXNOW_KEY. Any other path 404s, so attackers can't probe
    for the key value.
    """
    configured = _key()
    if not configured or key != configured:
        raise Http404()
    return HttpResponse(configured, content_type='text/plain')


def ping_indexnow(urls: Iterable[str]) -> bool:
    """Notify IndexNow that the given URLs have changed.

    Returns True on success, False on any failure (network, key missing,
    non-2xx response). Never raises — callers don't have to wrap in try.

    The IndexNow API rejects requests where the URL host doesn't match
    the host of the registered key, so we filter to SITE_DOMAIN's host.
    """
    key = _key()
    if not key:
        log.debug('IndexNow skipped: INDEXNOW_KEY not configured')
        return False

    site = _site_domain()
    host = urlparse(site).hostname
    if not host:
        log.warning('IndexNow skipped: SITE_DOMAIN has no parseable host: %s', site)
        return False

    # Filter and dedupe URLs that belong to our domain.
    valid_urls: list[str] = []
    seen = set()
    for u in urls:
        if not u:
            continue
        # Allow relative URLs by prefixing with site.
        full = u if u.startswith('http') else f"{site}{u}"
        try:
            parsed = urlparse(full)
        except ValueError:
            continue
        if parsed.hostname != host:
            continue
        if full in seen:
            continue
        seen.add(full)
        valid_urls.append(full)

    if not valid_urls:
        return False

    payload = {
        'host': host,
        'key': key,
        'keyLocation': f"{site}/{key}.txt",
        'urlList': valid_urls[:10000],  # IndexNow caps at 10k per request
    }

    try:
        resp = httpx.post(
            INDEXNOW_ENDPOINT,
            json=payload,
            timeout=TIMEOUT_SECONDS,
            headers={'Content-Type': 'application/json'},
        )
        if 200 <= resp.status_code < 300:
            log.info('IndexNow OK: pushed %d URLs (status %d)', len(valid_urls), resp.status_code)
            return True
        log.warning(
            'IndexNow non-2xx: status=%s body=%s urls=%d',
            resp.status_code,
            (resp.text or '')[:200],
            len(valid_urls),
        )
        return False
    except httpx.HTTPError as exc:
        log.warning('IndexNow request failed: %s (urls=%d)', exc, len(valid_urls))
        return False
