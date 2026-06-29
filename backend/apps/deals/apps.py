"""Django app config for deals (aliased to pipelines app)."""

from __future__ import annotations

from django.apps import AppConfig


class DealsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.deals"
    label = "deals"
    verbose_name = "Deals"
