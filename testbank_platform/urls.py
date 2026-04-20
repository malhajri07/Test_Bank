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
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .health import healthz, readyz

urlpatterns = [
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
