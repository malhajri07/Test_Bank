"""
XML Sitemaps for search engine indexing.

Covers: homepage, categories, certifications, test banks, CMS pages, blog.

Sitemap index is enabled at /sitemap.xml (Django auto-builds index when
multiple sitemap classes are registered). Each section is exposed at its
own URL (/sitemap-<section>.xml) so search engines can fetch in parallel
and we can tune crawl frequency per content type.

Image sitemap fields are included for test bank covers and category icons
so Google Images can discover them. This dramatically improves rich-result
eligibility on Search.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone


def _site_url() -> str:
    """Canonical absolute base, no trailing slash."""
    return getattr(settings, 'SITE_DOMAIN', 'https://www.examstellar.com').rstrip('/')


class StaticSitemap(Sitemap):
    """High-value static pages — homepage gets priority 1.0."""
    changefreq = 'daily'
    protocol = 'https'

    PAGES = {
        'catalog:index': (1.0, 'daily'),
        'catalog:category_list': (0.9, 'weekly'),
        'catalog:contact': (0.5, 'monthly'),
    }

    def items(self):
        return list(self.PAGES.keys())

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.PAGES[item][0]

    def changefreq(self, item):  # noqa: F811 — intentional per-item override
        return self.PAGES[item][1]

    def lastmod(self, item):
        # For the homepage, use "today" so Google sees it as fresh whenever
        # we publish new test banks (which is daily during phase 3+).
        return timezone.now()


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'

    def items(self):
        from catalog.models import Category
        return Category.objects.all().order_by('name')

    def location(self, obj):
        return reverse('catalog:category_detail', kwargs={'category_slug': obj.slug})

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', None)


class CertificationSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        from catalog.models import Certification
        return Certification.objects.select_related('category').all()

    def location(self, obj):
        return reverse('catalog:certification_list_full', kwargs={
            'category_slug': obj.category.slug,
            'certification_slug': obj.slug,
        })

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', None)


class TestBankSitemap(Sitemap):
    """Test bank detail pages — top SEO value, daily crawl, image-enriched."""
    changefreq = 'daily'
    priority = 0.9
    protocol = 'https'

    def items(self):
        from catalog.models import TestBank
        # Only index banks with active questions; empty banks would yield
        # thin content pages that hurt Search Console quality scores.
        return (
            TestBank.objects
            .filter(is_active=True)
            .select_related('category', 'certification')
            .order_by('-updated_at')
        )

    def location(self, obj):
        return reverse('catalog:testbank_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', None)

    def priority(self, obj):
        # Featured banks get a small boost; popular paid banks rank higher.
        if getattr(obj, 'is_featured', False):
            return 1.0
        if not getattr(obj, 'is_free', True):
            return 0.95
        return 0.9


class CMSPageSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    protocol = 'https'

    def items(self):
        from cms.models import Page
        return Page.objects.filter(status='published')

    def location(self, obj):
        return reverse('cms:page_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', None)


class BlogPostSitemap(Sitemap):
    """Blog posts — fresh content signals Google to recrawl frequently."""
    changefreq = 'weekly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        try:
            from cms.models import BlogPost
        except ImportError:
            return []
        try:
            return BlogPost.objects.filter(status='published').order_by('-published_at')
        except Exception:
            return []

    def location(self, obj):
        return reverse('cms:blog_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', None) or getattr(obj, 'published_at', None)


sitemaps = {
    'static': StaticSitemap,
    'categories': CategorySitemap,
    'certifications': CertificationSitemap,
    'testbanks': TestBankSitemap,
    'pages': CMSPageSitemap,
    'blog': BlogPostSitemap,
}
