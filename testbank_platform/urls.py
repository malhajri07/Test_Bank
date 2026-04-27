"""
Main URL configuration for testbank_platform project.

Routes URLs to:
- Admin interface
- Accounts app (authentication, profiles, dashboard)
- Catalog app (browsing categories and test banks)
- Payments app (purchase and payment processing)
- Practice app (test practice sessions)

Also configures media file serving for development.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import index as sitemap_index, sitemap
from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.cache import cache_page
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .health import healthz, readyz
from .indexnow import key_file_view as indexnow_key_file
from .sitemaps import sitemaps


def _site_root() -> str:
    return getattr(settings, 'SITE_DOMAIN', 'https://www.examstellar.com').rstrip('/')


def robots_txt(request):
    """Search-engine crawl rules. Returns text/plain; cached 1h via decorator."""
    site = _site_root()
    lines = [
        '# Exam Stellar — robots.txt',
        '# Full crawl welcome on public surface; sensitive paths blocked.',
        '',
        'User-agent: *',
        'Allow: /',
        '',
        'Disallow: /admin/',
        'Disallow: /accounts/login/',
        'Disallow: /accounts/register/',
        'Disallow: /accounts/password-reset/',
        'Disallow: /accounts/dashboard/',
        'Disallow: /payments/',
        'Disallow: /practice/',
        'Disallow: /api/',
        'Disallow: /ckeditor5/',
        'Disallow: /search/',
        'Disallow: /*?*sort=',
        'Disallow: /*?*page=',
        '',
        '# Allow Google to render JS/CSS for Core Web Vitals',
        'User-agent: Googlebot',
        'Allow: /static/',
        'Allow: /media/',
        'Disallow: /admin/',
        'Disallow: /api/',
        '',
        '# Bingbot — same as Googlebot',
        'User-agent: Bingbot',
        'Allow: /static/',
        'Allow: /media/',
        'Disallow: /admin/',
        'Disallow: /api/',
        '',
        '# AI training crawlers — block by default to protect content investment.',
        '# Remove these blocks if you change strategy and want LLM exposure.',
        'User-agent: GPTBot',
        'Disallow: /',
        '',
        'User-agent: ClaudeBot',
        'Disallow: /',
        '',
        'User-agent: anthropic-ai',
        'Disallow: /',
        '',
        'User-agent: CCBot',
        'Disallow: /',
        '',
        'User-agent: Google-Extended',
        'Disallow: /',
        '',
        'User-agent: PerplexityBot',
        'Disallow: /',
        '',
        f'Sitemap: {site}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')

urlpatterns = [
    # SEO — sitemap index + per-section sitemaps for parallel crawl
    path('robots.txt', cache_page(3600)(robots_txt), name='robots_txt'),
    path(
        'sitemap.xml',
        cache_page(3600)(sitemap_index),
        {'sitemaps': sitemaps, 'sitemap_url_name': 'django.contrib.sitemaps.views.sitemap'},
        name='sitemap_index',
    ),
    path(
        'sitemap-<section>.xml',
        cache_page(3600)(sitemap),
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    # IndexNow ownership verification — serves the configured key as plain text.
    # Path matches `/<key>.txt` so search engines can fetch it during ping.
    path('<str:key>.txt', indexnow_key_file, name='indexnow_key_file'),

    path('healthz/', healthz),
    path('readyz/', readyz),
    # Admin interface
    path('admin/', admin.site.urls),

    # Accounts app URLs (authentication, profiles, dashboard)
    path('accounts/', include('accounts.urls')),
    # django-allauth (social login) - /accounts/ prefix for OAuth callbacks
    path('accounts/', include('allauth.urls')),

    # Catalog app URLs (browsing categories and test banks)
    path('', include('catalog.urls')),  # Root URL goes to catalog index

    # Payments app URLs (purchase and payment processing)
    path('payments/', include('payments.urls')),

    # Practice app URLs (test practice sessions)
    path('practice/', include('practice.urls')),

    # CMS app URLs (content management)
    path('cms/', include('cms.urls')),

    # Forum app URLs (discussion boards)
    path('forum/', include('forum.urls')),

    # CKEditor 5 URLs (image upload endpoint lives under this prefix)
    path('ckeditor5/', include('django_ckeditor_5.urls')),

    # REST API
    path('api/', include('api.urls')),

    # OpenAPI schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# Serve media files in development (not for production)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
