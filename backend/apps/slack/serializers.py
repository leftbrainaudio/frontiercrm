"""SlackWebhook serializers — CRUD for Slack integration configuration."""

from __future__ import annotations

from rest_framework import serializers

from apps.slack.models import SlackWebhook


class SlackWebhookSerializer(serializers.ModelSerializer):
    """Serializer for SlackWebhook CRUD operations."""

    pipeline_filter_id = serializers.UUIDField(allow_null=True, required=False)
    pipeline_filter = serializers.SerializerMethodField()

    class Meta:
        model = SlackWebhook
        exclude = ()
        read_only_fields = (
            "id",
            "tenant_id",
            "created_at",
            "updated_at",
            "last_triggered_at",
            "failure_count",
        )

    def get_pipeline_filter(self, obj: SlackWebhook) -> dict | None:
        """Return nested {id, name} for the pipeline filter FK."""
        if obj.pipeline_filter_id is None:
            return None
        return {
            "id": str(obj.pipeline_filter_id),
            "name": getattr(obj.pipeline_filter, "name", None),
        }

    def validate_webhook_url(self, value: str) -> str:
        """Validate that the URL is a Slack Incoming Webhook URL."""
        if not value.startswith("https://hooks.slack.com/services/"):
            raise serializers.ValidationError(
                "Must be a valid Slack Incoming Webhook URL starting with "
                "https://hooks.slack.com/services/"
            )
        return value