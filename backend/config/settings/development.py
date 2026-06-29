"""Development settings - extended from base."""

from .base import *  # noqa: F403, F401

DEBUG = True

# Dev-only apps (install via pip as needed)

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
