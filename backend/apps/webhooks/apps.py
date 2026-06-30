"""Django app config for the webhooks app."""

from __future__ import annotations

from django.apps import AppConfig


class WebhooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.webhooks"
    verbose_name = "Webhooks"

    def ready(self):
        import apps.webhooks.signals  # noqa: F401
