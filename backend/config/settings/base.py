"""Base Django settings for FrontierCRM. Shared by all environments."""

import os
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab

# ── Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS: list[str] = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")

# ── Application definition ───────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # Internal apps
    "apps.core",
    "apps.accounts",
    "apps.contacts",
    "apps.deals",
    "apps.pipelines",
    "apps.activities",
    "apps.email",
    "apps.notes",
    "apps.tasks",
    "apps.teams",
    "apps.webhooks",
    "apps.files",
    "apps.search",
    "apps.imports",
    "apps.reports",
    # Export
    "apps.export",
    # Sync engine
    "apps.sync",
    # Slack notifications
    "apps.slack",
    # API Keys
    "apps.apikeys",
]

MIDDLEWARE = [
    "config.middleware.HealthCheckMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.TenantMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ── Database ─────────────────────────────────────────────────────────────────
# Default is SQLite so the project works out of the box without Postgres.
# Override with DATABASE_URL env var for production (Supabase, Fly Postgres, etc.).
# Development settings (settings/development.py) also set SQLite explicitly.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ── Auth & JWT ───────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.apikeys.auth.APIKeyAuthentication",  # checked first — handles fcrm_ prefix
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("apps.core.permissions.TenantAwarePermission",),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.environ.get("THROTTLE_RATE_ANON", "100/hour"),
        "user": os.environ.get("THROTTLE_RATE_USER", "1000/hour"),
    },
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# ── OpenAPI / Swagger ────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "FrontierCRM API",
    "DESCRIPTION": "API for FrontierCRM — the modern CRM platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "Auth", "description": "Authentication and authorization"},
        {"name": "Accounts", "description": "User accounts and profile management"},
        {"name": "Contacts", "description": "Contact management"},
        {"name": "Deals", "description": "Pipeline deal management"},
        {"name": "Activities", "description": "Activity timeline and logging"},
        {"name": "Email", "description": "Email sync and outbound"},
        {"name": "Notes", "description": "Notes and attachments"},
        {"name": "Tasks", "description": "Task management"},
        {"name": "Teams", "description": "Team and member management"},
        {"name": "Files", "description": "File upload and storage"},
        {"name": "Search", "description": "Global search"},
        {"name": "Reports", "description": "Dashboards and reporting"},
        {"name": "Export", "description": "Data export"},
        {"name": "Sync", "description": "Data sync engine"},
        {"name": "Webhooks", "description": "Webhook subscriptions"},
    ],
}

# ── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
).split(",")
CORS_ALLOW_CREDENTIALS = True

# ── Celery ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_BEAT_SCHEDULE = {
    "retry-stale-webhooks": {
        "task": "apps.webhooks.tasks.retry_stale_webhooks",
        "schedule": 300.0,  # every 5 minutes
        "options": {"expires": 240.0},
    },
    "prune-old-dead-webhook-events": {
        "task": "apps.webhooks.tasks.prune_dead_events",
        "schedule": crontab(hour=3, minute=0),  # daily at 03:00 UTC
        "options": {"expires": 3600},
    },
    # ── Calendar Watch Channel Renewal ─────────────────────────────────────
    "renew-calendar-watch-channels": {
        "task": "apps.sync.tasks_calendar.renew_calendar_watch_channels",
        "schedule": 21600.0,  # every 6 hours
        "options": {"expires": 3600},
    },
}

# ── Redis (cache) ────────────────────────────────────────────────────────────
# Production uses Redis via django-redis. Falls back to LocMem if no REDIS_URL.
_REDIS_URL = os.environ.get("REDIS_URL", "")
if _REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": _REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,  # Degrade gracefully if Redis is down
            },
            "KEY_PREFIX": "frontiercrm",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "frontiercrm-cache",
        }
    }

# ── Channels (WebSocket) ─────────────────────────────────────────────────────
_CHANNEL_REDIS = os.environ.get("CHANNEL_REDIS_URL", _REDIS_URL)
if _CHANNEL_REDIS:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [_CHANNEL_REDIS],
                "symmetric_encryption_keys": [SECRET_KEY],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }

# ── Email ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@frontiercrm.com")

# ── Gmail API ────────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_OAUTH_REDIRECT_URI = os.environ.get(
    "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:5173/auth/callback"
)

# ── Microsoft OAuth (login) ───────────────────────────────────────────────────
MICROSOFT_CLIENT_ID = os.environ.get("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.environ.get("MICROSOFT_CLIENT_SECRET", "")
MICROSOFT_TENANT = os.environ.get("MICROSOFT_TENANT", "common")
MICROSOFT_OAUTH_REDIRECT_URI = os.environ.get(
    "MICROSOFT_OAUTH_REDIRECT_URI", "http://localhost:5173/auth/callback"
)

# ── Google Calendar Event Creation & Push ─────────────────────────────────────
GOOGLE_CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
]
CALENDAR_WEBHOOK_URL = os.environ.get(
    "CALENDAR_WEBHOOK_URL",
    "https://api.frontiercrm.com/api/sync/calendar/webhook/",
)
CALENDAR_WATCH_TTL_SECONDS = int(os.environ.get(
    "CALENDAR_WATCH_TTL_SECONDS",
    7 * 24 * 3600,  # 7 days (max allowed)
))
CALENDAR_WATCH_EXPIRY_GRACE_HOURS = int(os.environ.get(
    "CALENDAR_WATCH_EXPIRY_GRACE_HOURS",
    24,  # Renew channels within 24 hours of expiry
))
CRM_EXTENDED_PROPERTIES_PREFIX = "frontiercrm"
CALENDAR_WRITE_SCOPE_REQUIRED = True

# ── SAML ──────────────────────────────────────────────────────────────────
SAML_BASE_URL = os.environ.get("SAML_BASE_URL", "http://localhost:8000")

# ── Meilisearch ──────────────────────────────────────────────────────────────
MEILISEARCH_URL = os.environ.get("MEILISEARCH_URL", "http://localhost:7700")
MEILISEARCH_API_KEY = os.environ.get("MEILISEARCH_API_KEY", "masterKey")
MEILISEARCH_INDEX_PREFIX = os.environ.get("MEILISEARCH_INDEX_PREFIX", "frontiercrm_")

# ── File Storage (S3/R2) ─────────────────────────────────────────────────────
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "frontiercrm-uploads")
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "")  # Cloudflare R2
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "auto")
AWS_DEFAULT_ACL = "private"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_FILE_OVERWRITE = False
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage" if DEBUG else "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ── Sentry ───────────────────────────────────────────────────────────────────
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# ── Static & Media files ─────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Default primary key ──────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Auth backend overrides ───────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    "apps.accounts.auth.EmailPasswordBackend",
    "apps.accounts.auth.MagicLinkBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# ── Rate limiting ────────────────────────────────────────────────────────────
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "True") == "True"

# ── Max upload size ──────────────────────────────────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_SIZE = 50 * 1024 * 1024  # 50 MB
