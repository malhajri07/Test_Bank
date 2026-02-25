"""
Context processors for CMS app.

Makes CMS content available globally across all templates.
"""

from django.db.models import Q
from django.utils import timezone

from .models import Announcement, HeroSlide, Page, Testimonial


def cms_content(request):
    """
    Context processor to add CMS content to all templates.

    Provides:
    - Active announcements (for homepage and site-wide display)
    - Published pages (for navigation/footer)
    - Content blocks (via template tags)
    """
    now = timezone.now()

    # Get active announcements that should be displayed
    active_announcements = Announcement.objects.filter(
        is_active=True
    ).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now)
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).order_by('-created_at')

    # Get homepage announcements
    homepage_announcements = active_announcements.filter(
        show_on_homepage=True
    )[:5]  # Limit to 5 most recent

    # Get all site-wide announcements (not just homepage)
    site_announcements = active_announcements.exclude(
        show_on_homepage=True
    )[:3]  # Limit to 3 most recent

    # Get published pages for navigation/footer
    published_pages = Page.objects.filter(
        status='published'
    ).order_by('order', 'title')

    # Get featured pages
    featured_pages = published_pages.filter(
        is_featured=True
    )[:5]

    # Get active hero slides
    hero_slides = HeroSlide.objects.filter(
        is_active=True
    ).order_by('order', 'created_at')

    # Get active testimonials
    testimonials = Testimonial.objects.filter(
        is_active=True
    ).order_by('order', 'created_at')

    return {
        'cms_homepage_announcements': homepage_announcements,
        'cms_site_announcements': site_announcements,
        'cms_pages': published_pages,
        'cms_featured_pages': featured_pages,
        'cms_hero_slides': hero_slides,
        'cms_testimonials': testimonials,
    }

