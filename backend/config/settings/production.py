"""Production settings - extended from base."""

from .base import *  # noqa: F403, F401

DEBUG = False

# ── Database ───────────────────────────────────────────────────────────────────
# Base.py uses SQLite by default. Override with DATABASE_URL for
# production (Supabase PostgreSQL, Fly Postgres, etc.).
import dj_database_url  # noqa: F811
_DB_URL = os.environ.get("DATABASE_URL", "")
if _DB_URL:
    DATABASES = {"default": dj_database_url.config(default=_DB_URL, conn_max_age=600)}  # noqa: F405
else:
    raise RuntimeError("DATABASE_URL environment variable is required in production")

# ── SSL / Security headers ────────────────────────────────────────────────────
# Django's SECURE_SSL_REDIRECT would cause a redirect loop because Fly.io
# terminates TLS at the edge and forwards HTTP internally. Fly.io handles
# HTTP→HTTPS redirection natively at the proxy level.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Trust the Fly.io proxy for correct HTTPS detection
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = (
    os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if os.environ.get("CORS_ALLOWED_ORIGINS")
    else []
)

# Production email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")  # noqa: F405
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))  # noqa: F405
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")  # noqa: F405
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")  # noqa: F405
EMAIL_USE_TLS = True

# Production logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
