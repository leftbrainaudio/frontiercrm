"""Slack app config — register signals on ready."""

from __future__ import annotations

from django.apps import AppConfig


class SlackConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.slack"
    verbose_name = "Slack Notifications"

    def ready(self):
        """Import signal handlers so they connect on app load."""
        import apps.slack.signals  # noqa: F401