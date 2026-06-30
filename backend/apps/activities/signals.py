"""Signal handlers for Activity model — auto-push MEETING events to Google Calendar."""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.activities.models import Activity
from apps.sync.models import SyncConnection

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Activity)
def push_meeting_to_calendar(sender, instance, created, **kwargs):
    """Automatically push CRM-created meetings to Google Calendar.

    When an Activity with activity_type=MEETING is created (or updated
    and the metadata indicates a CRM origin), enqueue a Celery task
    to push the event to the user's connected Google Calendar.

    Skips:
    - Non-MEETING activities
    - Events synced FROM Google (event_source=google) — prevents push-back
    - Users without an active google_calendar SyncConnection
    """
    if instance.activity_type != Activity.ActivityType.MEETING:
        return

    # Skip Google-sourced events (prevent push-back)
    metadata = instance.metadata or {}
    if metadata.get("event_source") == "google":
        return

    # Find the user's active Google Calendar connection
    connection = SyncConnection.objects.filter(
        tenant_id=instance.tenant_id,
        user_id=instance.actor_id,
        provider="google_calendar",
        is_active=True,
        status="active",
    ).first()

    if not connection:
        # No calendar sync configured — silently skip
        logger.debug(
            "No active google_calendar connection for user %s, skipping push",
            instance.actor_id,
        )
        return

    # Also push on updates that add external_event_id metadata
    # (e.g., when the API proxy creates the Google event and the
    # activity metadata is updated)
    from apps.sync.tasks_calendar import push_crm_event_to_calendar

    push_crm_event_to_calendar.delay(
        activity_id=str(instance.id),
        connection_id=str(connection.id),
    )
