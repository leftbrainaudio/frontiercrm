"""Test settings — overrides base for fast, isolated test runs."""

from .base import *  # noqa: F403, F401

# Use SQLite for tests (fast, no external deps)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable throttling in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
RATE_LIMIT_ENABLED = False

# Disable middleware that isn't testable
MIDDLEWARE = [m for m in MIDDLEWARE if "TenantMiddleware" not in m]  # noqa: F405

# Celery always eager for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# No external services
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable sentry
SENTRY_DSN = ""

# Static files
STORAGES["default"]["BACKEND"] = "django.core.files.storage.InMemoryStorage"  # noqa: F405
