"""
CMS app views for displaying content.

This module provides views for:
- Page detail view (static pages)
- Announcement display
- Content block rendering
"""

from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.utils import timezone
from django.db import models
from .models import Page, Announcement, ContentBlock


def page_detail(request, slug):
    """
    Display a static page.
    
    Args:
        slug: Slug of the page to display
    """
    # Only show published pages to non-staff users
    if request.user.is_staff:
        page = get_object_or_404(Page, slug=slug)
    else:
        page = get_object_or_404(Page, slug=slug, status='published')
    
    return render(request, 'cms/page_detail.html', {
        'page': page,
    })


def get_active_announcements():
    """
    Get currently active announcements.
    
    Returns queryset of active announcements that should be displayed.
    """
    now = timezone.now()
    return Announcement.objects.filter(
        is_active=True
    ).filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
    ).order_by('-created_at')


def get_content_block(slug):
    """
    Get a content block by slug.
    
    Args:
        slug: Slug of the content block
        
    Returns:
        ContentBlock instance or None
    """
    try:
        return ContentBlock.objects.get(slug=slug)
    except ContentBlock.DoesNotExist:
        return None
