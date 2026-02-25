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
USE_GCS = config('USE_GCS', default='True', cast=bool)
GCS_BUCKET_NAME = config('GCS_BUCKET_NAME', default=f'{GCP_PROJECT_ID}-exam-stellar-media')
GCS_STATIC_BUCKET_NAME = config('GCS_STATIC_BUCKET_NAME', default=f'{GCP_PROJECT_ID}-exam-stellar-static')

if USE_GCS:
    # Install django-storages for GCS support
    # Add to requirements: django-storages[google]>=1.14.0

    # Media files (user uploads) - Cloud Storage
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = GCS_BUCKET_NAME
    GS_DEFAULT_ACL = 'publicRead'
    GS_PROJECT_ID = GCP_PROJECT_ID

    # Media URL
    MEDIA_URL = f'https://storage.googleapis.com/{GCS_BUCKET_NAME}/'

    # Static files - Cloud Storage (optional, can use Cloud CDN)
    STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_STATIC_BUCKET_NAME = GCS_STATIC_BUCKET_NAME
    STATIC_URL = f'https://storage.googleapis.com/{GCS_STATIC_BUCKET_NAME}/'

    # GCS credentials (if using service account JSON)
    # GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    #     config('GCS_CREDENTIALS_FILE', default='')
    # )

    # Or use default credentials (Application Default Credentials)
    # Cloud Run automatically provides credentials
else:
    # Fallback to local storage
    MEDIA_ROOT = BASE_DIR / "media"
    STATIC_ROOT = BASE_DIR / "staticfiles"

# Security Settings for Production
DEBUG = config('DEBUG', default=False, cast=bool)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Allowed Hosts - Set via environment variable
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])

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

# Static files serving (if not using Cloud Storage)
if not USE_GCS:
    # Use WhiteNoise for static files in Cloud Run
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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

