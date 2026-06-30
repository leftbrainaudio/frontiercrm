"""Celery tasks for Slack notification delivery."""

from __future__ import annotations

from celery import shared_task

from apps.activities.models import Activity
from apps.slack.services import SlackNotificationService


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def deliver_slack_notifications(self, activity_id: str) -> dict:
    """Load an Activity and push notifications to all matching Slack webhooks."""
    try:
        activity = Activity.objects.get(id=activity_id)
    except Activity.DoesNotExist:
        return {"error": "Activity not found", "activity_id": activity_id}

    results = SlackNotificationService.notify(activity)
    return {"activity_id": activity_id, "results": results}