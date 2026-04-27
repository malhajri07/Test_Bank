"""
Context processors for catalog app.

Makes catalog data available globally across all templates.
"""

from django.conf import settings
from django.db.models import Count, Prefetch, Q

from .models import Category, Certification, TestBank


def seo(request):
    """SEO globals: canonical site URL and search-engine verification tokens.

    Exposed in every template so meta tags, OpenGraph URLs, and JSON-LD
    'url' fields can be built from a single source of truth (SITE_DOMAIN).
    Avoids hard-coding 'examstellar.com' in templates.
    """
    return {
        'SITE_DOMAIN': getattr(settings, 'SITE_DOMAIN', 'https://www.examstellar.com').rstrip('/'),
        'GOOGLE_SITE_VERIFICATION': getattr(settings, 'GOOGLE_SITE_VERIFICATION', ''),
        'BING_SITE_VERIFICATION': getattr(settings, 'BING_SITE_VERIFICATION', ''),
        'YANDEX_SITE_VERIFICATION': getattr(settings, 'YANDEX_SITE_VERIFICATION', ''),
    }


def categories(request):
    """
    Context processor to add categories to all templates.

    Provides:
    - Top categories with test bank counts for navigation
    - Test banks prefetched for mega menu (up to 10 per category)
    """
    # Get top categories with test bank counts and prefetch test banks
    top_categories = Category.objects.annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
    ).filter(test_bank_count__gt=0).prefetch_related(
        Prefetch(
            'test_banks',
            queryset=TestBank.objects.filter(is_active=True).order_by('-created_at')
        )
    ).order_by('name')[:10]

    return {
        'categories': top_categories,
    }

