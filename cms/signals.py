"""
CMS signals — push URLs to IndexNow when blog posts or pages change.
"""
from __future__ import annotations

import logging
import threading

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import BlogPost, Page

log = logging.getLogger(__name__)


def _ping_async(url: str) -> None:
    def _run():
        try:
            from testbank_platform.indexnow import ping_indexnow
            ping_indexnow([url])
        except Exception as exc:  # pragma: no cover
            log.warning('IndexNow ping failed: %s', exc)
    threading.Thread(target=_run, daemon=True, name='indexnow-ping').start()


@receiver(post_save, sender=BlogPost)
def blogpost_ping_indexnow(sender, instance: BlogPost, created: bool, **kwargs):
    """Notify IndexNow when a published BlogPost is created or updated."""
    if getattr(instance, 'status', '') != 'published':
        return
    try:
        url = reverse('cms:blog_detail', kwargs={'slug': instance.slug})
        _ping_async(url)
    except Exception as exc:  # pragma: no cover
        log.warning('BlogPost IndexNow ping failed: %s', exc)


@receiver(post_save, sender=Page)
def page_ping_indexnow(sender, instance: Page, created: bool, **kwargs):
    """Notify IndexNow when a published CMS Page is created or updated."""
    if getattr(instance, 'status', '') != 'published':
        return
    try:
        url = reverse('cms:page_detail', kwargs={'slug': instance.slug})
        _ping_async(url)
    except Exception as exc:  # pragma: no cover
        log.warning('Page IndexNow ping failed: %s', exc)
