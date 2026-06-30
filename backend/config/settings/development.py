"""Development settings - extended from base.

Uses SQLite by default so no external Postgres is needed for local dev.
Override with DATABASE_URL env var if you need to test against a real PG."""

from .base import *  # noqa: F403, F401

DEBUG = True

# ── Database: SQLite for dev (no Postgres dependency) ──────────────────────────
# Override base.py's PostgreSQL default so devs don't need Postgres running.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Allow all origins in dev
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Show emails in console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable Sentry in dev
SENTRY_DSN = ""

# SQL logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.db.backends": {
            "level": "DEBUG" if os.environ.get("SQL_DEBUG") else "WARNING",  # noqa: F405
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
