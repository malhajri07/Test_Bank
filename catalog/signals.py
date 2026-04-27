"""
Catalog signals — push URLs to IndexNow when test banks change.

Hooks post_save on TestBank so newly-published or freshly-edited banks
get notified to participating search engines (Bing, Yandex, etc.) within
seconds instead of waiting for the next sitemap crawl.
"""
from __future__ import annotations

import logging
import threading

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import TestBank

log = logging.getLogger(__name__)


def _ping_async(url: str) -> None:
    """Fire IndexNow in a daemon thread so admin saves return instantly."""
    def _run():
        try:
            from testbank_platform.indexnow import ping_indexnow
            ping_indexnow([url])
        except Exception as exc:  # pragma: no cover
            log.warning('IndexNow ping failed: %s', exc)
    threading.Thread(target=_run, daemon=True, name='indexnow-ping').start()


@receiver(post_save, sender=TestBank)
def testbank_ping_indexnow(sender, instance: TestBank, created: bool, **kwargs):
    """Notify IndexNow when an active TestBank is created or updated.

    Skipped silently when INDEXNOW_KEY is not configured (dev/test envs).
    """
    if not getattr(instance, 'is_active', False):
        return
    try:
        url = reverse('catalog:testbank_detail', kwargs={'slug': instance.slug})
        _ping_async(url)
    except Exception as exc:  # pragma: no cover — never block writes
        log.warning('TestBank IndexNow ping failed: %s', exc)
