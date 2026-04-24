"""
Django settings for testbank_platform project.

This configuration file includes:
- PostgreSQL database configuration using environment variables
- Tailwind CSS integration via django-tailwind
- RTL (Right-to-Left) support for Arabic and English
- Stripe payment integration settings
- Static and media files configuration
- Custom user model configuration
"""

from datetime import timedelta
from datetime import timedelta
from pathlib import Path

from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY must come from the environment. No insecure default.
# Dev convenience: allow an insecure default only when DEBUG is explicitly True.
_DEBUG_ENV = config('DEBUG', default='False')
DEBUG = str(_DEBUG_ENV).lower() in ('true', '1', 'yes', 'on')

SECRET_KEY = config('SECRET_KEY', default='' if not DEBUG else 'django-insecure-dev-only-do-not-use-in-production')
if not SECRET_KEY:
    raise RuntimeError(
        'SECRET_KEY environment variable is required in production. '
        'Generate one with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
    )

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",

    # Third-party apps
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "tailwind",  # Django Tailwind integration
    "theme",  # Tailwind theme app
    "django_ckeditor_5",  # Rich text editor for CMS (CKEditor 5 — supported branch)

    # Local apps
    "accounts",  # Authentication and user profiles
    "catalog",   # Categories, test banks, and questions
    "payments",  # Purchase and payment processing
    "practice",  # User test sessions and results
    "cms",       # Content Management System
    "forum",     # Forum and discussion boards
    "api",       # REST API
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # LocaleMiddleware removed — the app is English-only. Leaving it in would
    # auto-switch based on the browser's Accept-Language header or a stale
    # `django_language` session key, making the UI render in unexpected
    # languages on non-English devices.
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "testbank_platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Global templates directory
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "accounts.context_processors.user_language",
                "cms.context_processors.cms_content",  # CMS content (announcements, pages)
                "catalog.context_processors.categories",  # Categories for navigation
                "payments.context_processors.cart",  # Cart count badge in nav
            ],
        },
    },
]

WSGI_APPLICATION = "testbank_platform.wsgi.application"


# Database configuration
# Using PostgreSQL with connection string from environment variable
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config('DB_NAME', default='testbank_db'),
        "USER": config('DB_USER', default='postgres'),
        "PASSWORD": config('DB_PASSWORD', default=''),
        "HOST": config('DB_HOST', default='localhost'),
        "PORT": config('DB_PORT', default='5432'),
    }
}

# Alternative: Use DATABASE_URL if provided (for production deployments)
# Uncomment and configure if using DATABASE_URL format:
# import dj_database_url
# if config('DATABASE_URL', default=None):
#     DATABASES['default'] = dj_database_url.parse(config('DATABASE_URL'))


# django-allauth
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
# Email verification is handled by the custom EmailVerificationToken flow
# in accounts/views.py (see register/verify_email). Allauth verification is
# disabled here to avoid duplicate verification emails and token races.
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_METHODS = {"username", "email"}
LOGIN_REDIRECT_URL = "accounts:dashboard"
SOCIALACCOUNT_AUTO_SIGNUP = True
# Social (Google) OAuth: Google already verified the email, so trust it.
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_QUERY_EMAIL = True
# Custom adapter links social login to an existing local user by email
# and guarantees a unique username, so Google sign-in never lands on the
# /accounts/3rdparty/signup/ confirmation form.
SOCIALACCOUNT_ADAPTER = "accounts.adapters.CustomSocialAccountAdapter"
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# Custom User Model
# Using custom user model for better flexibility and future extensions
# This allows us to add custom fields to the user model without migrations later
AUTH_USER_MODEL = "accounts.CustomUser"


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization — English only.
LANGUAGE_CODE = "en-us"

LANGUAGES = [
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = "UTC"

USE_I18N = True  # Enable internationalization

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # For production collectstatic
STATICFILES_DIRS = [
    BASE_DIR / "static",  # Additional static files directory
]

# Media files (user uploads)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# CKEditor 5 Configuration (django-ckeditor-5)
# CKEditor 4 is EOL; CKEditor 5 is the supported branch. See upgrade notes in
# AUDIT_STATUS.md for the migration context.
#
# Config format differs from CKEditor 4 — items are top-level toolbar entries
# (no nested groups), and plugins are implicit based on what's in the toolbar.
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'strikethrough', '|',
            'link', 'bulletedList', 'numberedList', '|',
            'blockQuote', 'code', 'codeBlock', '|',
            'insertTable', 'horizontalLine', '|',
            'undo', 'redo',
        ],
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'},
                {'model': 'heading4', 'view': 'h4', 'title': 'Heading 4', 'class': 'ck-heading_heading4'},
            ],
        },
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft', 'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side'],
            'styles': ['full', 'side', 'alignLeft', 'alignRight', 'alignCenter'],
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells'],
        },
        'language': 'en',
    },
    # A lighter profile for user-facing inputs (forum posts / comments).
    'user': {
        'toolbar': [
            'bold', 'italic', 'link', 'bulletedList', 'numberedList', 'blockQuote', 'code', '|',
            'undo', 'redo',
        ],
        'language': 'en',
    },
}

# Allowed file types for CKEditor 5 image upload (admin-only uploads).
CKEDITOR_5_FILE_STORAGE = config('CKEDITOR_5_FILE_STORAGE', default='django.core.files.storage.FileSystemStorage')
CKEDITOR_5_CUSTOM_CSS = ''


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Tailwind CSS Configuration
# django-tailwind app configuration
TAILWIND_APP_NAME = 'theme'

# Internal IPs for django-browser-reload (development)
INTERNAL_IPS = [
    "127.0.0.1",
]

# NPM Binary Path (for Tailwind compilation)
# Adjust if npm is in a different location
NPM_BIN_PATH = config('NPM_BIN_PATH', default='/opt/homebrew/bin/npm')


# Paylink Payment Gateway
# Testing: https://restpilot.paylink.sa  Production: https://restapi.paylink.sa
PAYLINK_BASE_URL = config('PAYLINK_BASE_URL', default='https://restpilot.paylink.sa')
PAYLINK_APP_ID = config('PAYLINK_APP_ID', default='')
PAYLINK_SECRET_KEY = config('PAYLINK_SECRET_KEY', default='')
PAYLINK_CURRENCY = config('PAYLINK_CURRENCY', default='SAR')

# VAT Configuration
VAT_RATE = 0.15  # 15% VAT rate


# Email Configuration
# For password reset and notifications
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp-mail.outlook.com')  # Microsoft/Outlook SMTP
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='info@examstellar.com')


# Login/Logout URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'catalog:index'


# Security Settings — automatically enabled when DEBUG is False
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    X_FRAME_OPTIONS = 'DENY'


# Content Security Policy (django-csp 4.x)
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'"),
        'style-src': ("'self'", "'unsafe-inline'"),
        'font-src': ("'self'", 'data:'),
        'img-src': ("'self'", 'data:', 'https:'),
        'connect-src': ("'self'", 'https://restpilot.paylink.sa', 'https://restapi.paylink.sa'),
        'frame-src': ('https://payment.paylink.sa', 'https://paymentpilot.paylink.sa'),
        'frame-ancestors': ("'none'",),
        'base-uri': ("'self'",),
        # Includes Google OAuth domains — form-action applies to the
        # entire redirect chain after a form submit. Google's OAuth flow
        # can bounce through accounts.google.com, accounts.youtube.com,
        # and country-specific accounts.google.* subdomains, so we
        # allow-list the parent google.com / youtube.com to keep the
        # consent flow unblocked end-to-end.
        'form-action': (
            "'self'",
            'https://payment.paylink.sa',
            'https://paymentpilot.paylink.sa',
            'https://accounts.google.com',
            'https://accounts.youtube.com',
            'https://*.google.com',
        ),
    },
}


# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

# JWT (simplejwt) - for API/mobile clients
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# drf-spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Exam Stellar API',
    'VERSION': '1.0.0',
}

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Logging Configuration
#
# Format switches between human-readable (dev) and single-line JSON (prod or
# when LOG_JSON=True). JSON output is meant for log aggregators (GCP Cloud
# Logging, Datadog, Loki) that parse structured fields natively.
LOG_JSON = config('LOG_JSON', default=not DEBUG, cast=bool)
_LOG_FORMATTER = 'json' if LOG_JSON else 'verbose'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            '()': 'testbank_platform.logging_config.JSONFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': _LOG_FORMATTER,
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
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'payments': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'catalog': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'practice': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}


# Sentry — opt-in via SENTRY_DSN. No DSN means the SDK is never loaded.
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    from .logging_config import init_sentry
    init_sentry(
        dsn=SENTRY_DSN,
        environment=config('SENTRY_ENVIRONMENT', default='development' if DEBUG else 'production'),
        release=config('SENTRY_RELEASE', default=None),
        traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float),
    )
