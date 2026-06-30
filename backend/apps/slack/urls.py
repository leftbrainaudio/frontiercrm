"""Slack webhook URL routing — REST endpoints for Slack integration."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.slack.views import SlackWebhookViewSet

router = DefaultRouter()
router.register(r"webhooks", SlackWebhookViewSet, basename="slack-webhook")

urlpatterns = router.urls