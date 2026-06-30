"""Django app config for the apikeys app."""

from __future__ import annotations

from django.apps import AppConfig


class ApikeysConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.apikeys"
    verbose_name = "API Keys"
