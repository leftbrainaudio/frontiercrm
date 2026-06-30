"""Signal handlers — fire Slack notifications when Activities are created."""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.activities.models import Activity

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Activity)
def activity_created_handler(sender, instance, created, **kwargs):
    """Fire Slack notifications when a new Activity is created."""
    if not created:
        return
    # Fire async — don't block the HTTP response.
    # Using .delay() so CELERY_TASK_ALWAYS_EAGER works in tests.
    try:
        from apps.slack.tasks import deliver_slack_notifications

        deliver_slack_notifications.delay(str(instance.id))
    except Exception as exc:
        logger.warning(
            "Failed to enqueue Slack notification task for activity %s: %s",
            instance.id,
            exc,
        )