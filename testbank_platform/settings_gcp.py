"""
GCP-specific Django settings for Google Cloud Platform deployment.

This file extends base settings with GCP-specific configurations:
- Cloud Storage for media files
- Cloud SQL connection
- Secret Manager integration
- Static file serving via Cloud CDN

Usage:
    Set DJANGO_SETTINGS_MODULE=testbank_platform.settings_gcp in production
    Or import this in settings.py conditionally
"""



import os

from .settings import *

# GCP Project Configuration
GCP_PROJECT_ID = config('GCP_PROJECT_ID', default='')
GCP_REGION = config('GCP_REGION', default='us-central1')

# Cloud SQL Configuration
# Use Cloud SQL Proxy connection format
DB_HOST = config('DB_HOST', default='')
if DB_HOST.startswith('/cloudsql/'):
    # Cloud SQL Unix socket connection
    DATABASES['default']['HOST'] = DB_HOST
    DATABASES['default']['PORT'] = ''
else:
    # Standard TCP connection (for local development)
    DATABASES['default']['HOST'] = config('DB_HOST', default='localhost')
    DATABASES['default']['PORT'] = config('DB_PORT', default='5432')

# Cloud Storage Configuration for Media Files
# Cloud Run's local filesystem is ephemeral, so user uploads (hero slides,
# testimonial avatars, CKEditor embeds) must live in GCS. Static files keep
# shipping inside the container — whitenoise serves them cheaply and there's
# no value to a second bucket for assets that are baked into the image.
USE_GCS = config(
    'USE_GCS',
    default='True',
    cast=lambda v: str(v).lower() in ('true', '1', 'yes', 'on'),
)

if USE_GCS:
    GS_BUCKET_NAME = config('GS_BUCKET_NAME')
    GS_PROJECT_ID = config('GS_PROJECT_ID', default=GCP_PROJECT_ID or 'exam-stellar')
    GS_DEFAULT_ACL = None          # uniform bucket IAM rejects per-object ACLs
    GS_QUERYSTRING_AUTH = False    # public URLs, no signed tokens
    GS_FILE_OVERWRITE = False      # don't clobber same-name uploads

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'

    # CKEditor admin embeds also need to land in the bucket.
    CKEDITOR_5_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
else:
    MEDIA_ROOT = BASE_DIR / "media"
    STATIC_ROOT = BASE_DIR / "staticfiles"

# Security Settings for Production
DEBUG = config('DEBUG', default=False, cast=bool)
# Cloud Run terminates SSL at the load balancer — do NOT redirect internally
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Allowed Hosts
ALLOWED_HOSTS = [
    'examstellar.com',
    'www.examstellar.com',
    'exam-stellar-520164162522.us-central1.run.app',
    '.run.app',
    'localhost',
    '127.0.0.1',
]

# Canonical site URL — used in sitemaps, robots.txt, JSON-LD, OpenGraph,
# canonical <link> tags. Production should always serve www. so canonicals
# never split between apex and www. (apex 301-redirects to www. via
# Cloud Run domain mapping.)
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'https://www.examstellar.com').rstrip('/')

# Search engine verification tokens — set as env vars on the Cloud Run
# service to claim Search Console / Bing Webmaster ownership.
GOOGLE_SITE_VERIFICATION = os.environ.get('GOOGLE_SITE_VERIFICATION', '')
BING_SITE_VERIFICATION = os.environ.get('BING_SITE_VERIFICATION', '')
YANDEX_SITE_VERIFICATION = os.environ.get('YANDEX_SITE_VERIFICATION', '')

# IndexNow key — generate a 32-char hex string and serve at /<key>.txt
# for ownership verification. The push function uses this to notify
# search engines on testbank publish/update.
INDEXNOW_KEY = os.environ.get('INDEXNOW_KEY', '')

# Logging Configuration for Cloud Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Cloud SQL Connection Pooling (optional)
# DATABASES['default']['CONN_MAX_AGE'] = 600

# Static files — always served by WhiteNoise out of the container. Media goes
# to GCS; static assets ship in the image, so whitenoise is the right fit.
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Email Configuration (use SendGrid or Gmail SMTP)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@examstellar.com')

# Secret Manager Integration (optional)
# Uncomment to use Secret Manager instead of environment variables
# from google.cloud import secretmanager
#
# def get_secret(secret_id):
#     """Retrieve secret from Secret Manager."""
#     client = secretmanager.SecretManagerServiceClient()
#     name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_id}/versions/latest"
#     response = client.access_secret_version(request={"name": name})
#     return response.payload.data.decode("UTF-8")
#
# SECRET_KEY = get_secret('django-secret-key')
# DATABASES['default']['PASSWORD'] = get_secret('db-password')

