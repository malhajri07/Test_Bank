"""
XML Sitemaps for search engine indexing.

Covers: homepage, categories, certifications, test banks, CMS pages, forum.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from catalog.models import Category, Certification, TestBank
from cms.models import Page


class StaticSitemap(Sitemap):
    """Static pages: homepage, category list, contact."""
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['catalog:index', 'catalog:category_list', 'catalog:contact']

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return reverse('catalog:category_detail', kwargs={'category_slug': obj.slug})


class CertificationSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Certification.objects.select_related('category').all()

    def location(self, obj):
        return reverse('catalog:certification_list_full', kwargs={
            'category_slug': obj.category.slug,
            'certification_slug': obj.slug,
        })


class TestBankSitemap(Sitemap):
    """Test bank detail pages — highest SEO value."""
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return TestBank.objects.filter(is_active=True).select_related('category', 'certification')

    def location(self, obj):
        return reverse('catalog:testbank_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else None


class CMSPageSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return Page.objects.filter(status='published')

    def location(self, obj):
        return reverse('cms:page_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else None


sitemaps = {
    'static': StaticSitemap,
    'categories': CategorySitemap,
    'certifications': CertificationSitemap,
    'testbanks': TestBankSitemap,
    'pages': CMSPageSitemap,
}
