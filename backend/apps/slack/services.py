"""Slack notification service — orchestrates webhook delivery with rate limiting."""

from __future__ import annotations

import time
from typing import Any

import requests
from django.db.models import QuerySet
from django.utils import timezone

from apps.activities.models import Activity
from apps.slack.formatters import SlackMessageFormatter
from apps.slack.models import SlackWebhook

SLACK_RATE_LIMIT_SECONDS = 1.0  # 1 request per second per webhook
MAX_FAILURE_COUNT = 10  # Auto-deactivate after 10 consecutive failures


class SlackNotificationService:
    """Orchestrates Slack webhook delivery for Activity events."""

    _last_send_time: dict[str, float] = {}  # webhook_id -> timestamp

    @classmethod
    def notify(cls, activity: Activity) -> list[dict[str, Any]]:
        """Deliver a notification for a single Activity to all matching webhooks.

        Returns a list of delivery results (one per webhook).
        """
        webhooks: QuerySet[SlackWebhook] = SlackWebhook.objects.filter(
            tenant_id=activity.tenant_id,
            is_active=True,
        )

        results: list[dict[str, Any]] = []
        for wh in webhooks:
            if not cls._should_notify(wh, activity):
                continue
            message = SlackMessageFormatter.format(activity)
            result = cls._send(wh, message)
            results.append(result)

        return results

    @classmethod
    def _should_notify(cls, webhook: SlackWebhook, activity: Activity) -> bool:
        """Check if this webhook should receive this activity type."""
        # If subscribed_events is empty, notify on everything
        if webhook.subscribed_events:
            if activity.activity_type not in webhook.subscribed_events:
                return False

        # If pipeline_filter is set, only notify on deals in that pipeline
        if webhook.pipeline_filter_id and activity.entity_type == "deal":
            deal_pipeline_id = activity.metadata.get("pipeline_id")
            if str(deal_pipeline_id) != str(webhook.pipeline_filter_id):
                return False

        return True

    @classmethod
    def _send(cls, webhook: SlackWebhook, payload: dict[str, Any]) -> dict[str, Any]:
        """POST a Slack message payload to the webhook URL with rate limiting."""
        wh_id = str(webhook.id)

        # Rate limit: enforce 1 request/sec per webhook
        last_sent = cls._last_send_time.get(wh_id, 0.0)
        elapsed = time.time() - last_sent
        if elapsed < SLACK_RATE_LIMIT_SECONDS:
            time.sleep(SLACK_RATE_LIMIT_SECONDS - elapsed)

        try:
            resp = requests.post(
                webhook.webhook_url,
                json=payload,
                timeout=10,
            )
            cls._last_send_time[wh_id] = time.time()

            if resp.status_code == 200:
                webhook.last_triggered_at = timezone.now()
                webhook.failure_count = 0
                webhook.save(
                    update_fields=["last_triggered_at", "failure_count", "updated_at"]
                )
                return {"webhook_id": wh_id, "status": "delivered"}
            else:
                return cls._handle_failure(webhook, resp)

        except requests.RequestException as exc:
            return cls._handle_failure(webhook, exc=exc)

    @classmethod
    def _handle_failure(
        cls,
        webhook: SlackWebhook,
        resp: requests.Response | None = None,
        exc: Exception | None = None,
    ) -> dict[str, Any]:
        webhook.failure_count += 1
        if webhook.failure_count >= MAX_FAILURE_COUNT:
            webhook.is_active = False
        webhook.save(update_fields=["failure_count", "is_active", "updated_at"])

        error = resp.text[:500] if resp is not None else str(exc)
        return {"webhook_id": str(webhook.id), "status": "failed", "error": error}


def send_test_message(webhook: SlackWebhook) -> dict[str, Any]:
    """Send a test message to verify the webhook URL is working."""
    payload = {
        "text": "FrontierCRM Slack integration is working! 🎉",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "✅ *FrontierCRM Slack integration is working!* 🎉\n"
                        "You'll receive notifications when deals change stages, "
                        "deals are won/lost, and new emails arrive from contacts."
                    ),
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Configured at {timezone.now().isoformat()}",
                    }
                ],
            },
        ],
    }
    try:
        resp = requests.post(webhook.webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            return {"status": "delivered"}
        return {"status": "failed", "error": resp.text[:500]}
    except requests.RequestException as exc:
        return {"status": "failed", "error": str(exc)}