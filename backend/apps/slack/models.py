"""SlackWebhook model — stores Slack incoming webhook configuration per tenant."""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantScopedModel


class SlackWebhook(TenantScopedModel):
    """Slack incoming webhook configuration per tenant/workspace."""

    # The webhook URL from Slack (Incoming Webhooks or Slack app)
    webhook_url = models.URLField(max_length=2000)

    # Optional override — which Slack channel to post to.
    # If empty, uses the default channel configured when the webhook was created.
    channel_override = models.CharField(max_length=100, blank=True, default="")

    # Display name shown in UI (e.g. "Sales Team Channel")
    display_name = models.CharField(max_length=255, blank=True, default="")

    # Which event types trigger notifications on this webhook.
    # List of strings matching Activity.ActivityType values.
    # Empty list = all events trigger. Partial list = only those event types.
    subscribed_events = models.JSONField(
        default=list,
        blank=True,
        help_text="List of activity_type values to notify on. Empty = all events.",
    )

    # Optional filters — notify only when deals match a pipeline/stage
    pipeline_filter = models.ForeignKey(
        "pipelines.Pipeline",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If set, only notify on deals in this pipeline",
    )

    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)

    class Meta:
        db_table = "slack_webhook"
        indexes = [
            models.Index(fields=["tenant_id", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.display_name or self.webhook_url[:50]