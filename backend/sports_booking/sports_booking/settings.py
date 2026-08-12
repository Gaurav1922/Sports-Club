"""
Django settings for sports_booking project.
"""
from pathlib import Path
import os
from decouple import config, Csv
from datetime import timedelta
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


load_dotenv(BASE_DIR.parent / ".env")

ADMIN_PASSCODE = os.getenv("ADMIN_PASSCODE", "")

# --------------------------------------------------------------------------
# CORE SECURITY SETTINGS
# --------------------------------------------------------------------------

# DEBUG must default to False. Only your local .env should set DEBUG=True.
DEBUG = config('DEBUG', default=False, cast=bool)

# SECRET_KEY: allow an insecure dev fallback ONLY when DEBUG is True.
# In production (DEBUG=False), a missing SECRET_KEY env var will now crash
# the app at startup instead of silently using a public, insecure key.
if DEBUG:
    SECRET_KEY = config(
        'SECRET_KEY',
        default='django-insecure-local-dev-only-key-change-me'
    )
else:
    SECRET_KEY = config('SECRET_KEY')  # raises if missing — this is intentional

# Explicit host allowlist, comma-separated in the env var, e.g.:
# ALLOWED_HOSTS=sports-booking-backend.onrender.com,api.yourdomain.com
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=Csv()
)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_celery_beat',
    'accounts',
    'clubs',
    'bookings',
    'payments',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',        # Must be FIRST
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sports_booking.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sports_booking.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------------------------------------------------------
# CORS Configuration
# --------------------------------------------------------------------------
# NEVER allow all origins, in dev or prod — always drive off an explicit
# allowlist so behavior is identical (and auditable) in every environment.
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000',
    cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# --------------------------------------------------------------------------
# REST Framework configuration
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    # Rate limiting — critical given you have OTP + admin passcode + payment
    # endpoints that are otherwise brute-forceable.
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
        # Apply this scope explicitly on login/OTP/admin-passcode views —
        # see accounts app review (Phase 2) for how to wire it in.
        'auth': '5/minute',
    },
}

# --------------------------------------------------------------------------
# JWT Settings
# --------------------------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# --------------------------------------------------------------------------
# Celery Configuration
# --------------------------------------------------------------------------
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

# Only ever run tasks synchronously (eager) in local dev, when explicitly
# requested. This must NEVER be True in production — it silently turns
# every "background" task into a blocking, in-request call.
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=DEBUG, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-payments': {
        'task': 'payments.tasks.cleanup_expired_payments',
        'schedule': 300.0,
    },
    'security-monitoring': {
        'task': 'payments.tasks.security_monitoring',
        'schedule': 600.0,
    },
}

# --------------------------------------------------------------------------
# Third-party service credentials (loaded once, consistently, via decouple)
# --------------------------------------------------------------------------
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')

STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Admin passcode login (accounts.views.admin_login). Never hardcode this —
# set it as a Render env var, and do NOT ship the same value inside the
# React frontend bundle (see frontend review, Phase 6).
# (Already read once above via os.getenv — no need to read it twice.)

# When True, payment confirmation skips real Stripe charges — useful for a
# live portfolio demo where reviewers shouldn't need a real card. This is
# now an explicit, named setting instead of a hardcoded `if True:` in the
# view, so it's a deliberate, auditable choice rather than something that
# looks like a forgotten bypass. NEVER default this to True.
PAYMENT_DEV_MODE = config('PAYMENT_DEV_MODE', default=False, cast=bool)

# --------------------------------------------------------------------------
# Email Configuration
# --------------------------------------------------------------------------
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Sports Club <noreply@sportsclub.com>')

# Slot Locking Configuration
SLOT_LOCK_DURATION = 600  # 10 minutes in seconds

# --------------------------------------------------------------------------
# Redis / Cache Configuration
# --------------------------------------------------------------------------
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Redis-backed cache everywhere. This matters most in production, where
# multiple gunicorn workers each need to see the SAME slot-lock state —
# LocMemCache is per-process and will NOT prevent double-bookings across
# workers.
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'sports_booking',
        'TIMEOUT': 300,
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------------------------------
# Production-only hardening
# --------------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

    # HSTS: tells browsers to always use HTTPS for this domain. Start with a
    # short value while you confirm nothing breaks, then raise it.
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False  # flip to True only once you're sure

# --------------------------------------------------------------------------
# Logging Configuration
# --------------------------------------------------------------------------
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

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
        'file': {
            # Rotating so a long-lived deploy can't fill the disk.
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'bookings': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'payments': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
    },
}