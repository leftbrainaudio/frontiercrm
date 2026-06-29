"""Celery application configuration for FrontierCRM."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("frontiercrm")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
