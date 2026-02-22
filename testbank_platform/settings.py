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

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# Using python-decouple to load from .env file
SECRET_KEY = config('SECRET_KEY', default='django-insecure-!0h*3@_zmuva+t7drhoq$vsui0^sf35ksvc@c5&$$sefgo+o#f')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Third-party apps
    "tailwind",  # Django Tailwind integration
    "theme",  # Tailwind theme app
    "ckeditor",  # Rich text editor for CMS
    "ckeditor_uploader",  # File uploads for CKEditor
    
    # Local apps
    "accounts",  # Authentication and user profiles
    "catalog",   # Categories, test banks, and questions
    "payments",  # Purchase and Stripe integration
    "practice",  # User test sessions and results
    "cms",       # Content Management System
    "forum",     # Forum and discussion boards
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # For RTL/LTR language switching
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
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


# Internationalization
# Supporting both English (LTR) and Arabic (RTL)
LANGUAGE_CODE = "en-us"

# Supported languages for RTL/LTR switching
LANGUAGES = [
    ('en', 'English'),
    ('ar', 'Arabic'),
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

# CKEditor Configuration
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
        'toolbar_Full': [
            ['Styles', 'Format', 'Bold', 'Italic', 'Underline', 'Strike', 'SpellChecker', 'Undo', 'Redo'],
            ['Link', 'Unlink', 'Anchor'],
            ['Image', 'Flash', 'Table', 'HorizontalRule'],
            ['TextColor', 'BGColor'],
            ['Smiley', 'SpecialChar'], ['Source'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['NumberedList', 'BulletedList'],
            ['Indent', 'Outdent'],
            ['Maximize'],
        ],
        'extraPlugins': 'justify,liststyle,indent',
    },
}


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


# Stripe Payment Configuration
# Load Stripe keys from environment variables for security
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Stripe currency (default to USD, can be changed per payment)
STRIPE_CURRENCY = 'usd'

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


# Security Settings (for production)
# Uncomment and configure these for production deployment
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
