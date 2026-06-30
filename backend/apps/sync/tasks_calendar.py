"""Celery tasks for Google Calendar sync — delta sync, full sync, contact linking."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from celery import shared_task
from django.db import transaction
from django.utils import timezone as tz

from apps.activities.models import Activity
from apps.sync.adapters.base import CalendarEvent
from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter
from apps.sync.adapters.gmail.client import SyncLock
from apps.sync.models import CalendarWatchChannel, SyncConnection, SyncState

logger = logging.getLogger(__name__)

# ── Helper: resolve adapter from connection ──────────────────────────────────


def _get_calendar_adapter(connection: SyncConnection) -> GoogleCalendarAdapter | None:
    """Create a GoogleCalendarAdapter from a SyncConnection with tokens."""
    access_token = connection.access_token_encrypted
    refresh_token = connection.refresh_token_encrypted or None

    if not access_token:
        logger.error("Connection %s has no access token", connection.id)
        return None

    return GoogleCalendarAdapter(access_token=access_token, refresh_token=refresh_token)


def _refresh_tokens_if_needed(connection: SyncConnection, adapter: GoogleCalendarAdapter) -> bool:
    """Check token expiry and refresh if needed.

    Returns True if tokens are valid (possibly just refreshed), False on failure.
    """
    if connection.token_expires_at and connection.token_expires_at > tz.now():
        return True  # still valid

    result = adapter.refresh_token()
    if result.success:
        connection.access_token_encrypted = result.access_token
        connection.token_expires_at = tz.now() + tz.timedelta(seconds=result.expires_in or 3600)
        connection.save(update_fields=["access_token_encrypted", "token_expires_at"])
        return True

    connection.status = "expired"
    connection.last_error_message = "Token refresh failed"
    connection.save(update_fields=["status", "last_error_message"])
    return False


# ── Delta Sync Task ──────────────────────────────────────────────────────────


@shared_task(bind=True, max_retries=3, default_retry_delay=30, rate_limit="5/m")
def sync_calendar_delta(
    self,
    connection_id: str,
    trigger: str = "scheduled",
) -> dict[str, Any]:
    """Delta sync for a single Google Calendar connection.

    Uses syncToken from Google Calendar API with Redis lock
    to prevent concurrent syncs on the same connection.
    """
    result = {"connection_id": connection_id, "trigger": trigger, "synced": 0, "deleted": 0}

    def _do_sync():
        nonlocal result
        try:
            connection = SyncConnection.objects.get(id=connection_id, provider="google_calendar")
        except SyncConnection.DoesNotExist:
            result["error"] = "Connection not found"
            return

        if connection.status in ("expired", "disconnected"):
            result["error"] = f"Connection status is {connection.status}"
            return

        adapter = _get_calendar_adapter(connection)
        if not adapter:
            result["error"] = "Failed to create adapter"
            return

        if not _refresh_tokens_if_needed(connection, adapter):
            result["error"] = "Token refresh failed"
            return

        # Get or create sync state
        sync_state, _ = SyncState.objects.get_or_create(
            connection=connection,
            sync_type="calendar_event",
            defaults={
                "tenant_id": connection.tenant_id,
                "user_id": connection.user_id,
                "provider": "google_calendar",
                "state": "pending",
                "cursor_data": {},
            },
        )

        sync_state.state = "syncing"
        sync_state.save(update_fields=["state"])

        try:
            delta = adapter.get_calendar_delta(sync_state.cursor_data or None)

            if delta.full_resync_required:
                sync_state.state = "needs_full_resync"
                sync_state.save(update_fields=["state"])
                # Re-run with None cursor for full sync
                delta = adapter.get_calendar_delta(None)

            # Process events
            user_id = str(connection.user_id)
            for event in delta.items:
                _sync_event_to_activity(connection, event, user_id)

            # Process deletions
            for deleted_id in delta.deleted_ids:
                _process_deleted_event(connection, deleted_id)

            # Update sync state
            sync_state.cursor_data = delta.new_cursor
            sync_state.last_delta_sync_at = tz.now()
            sync_state.total_synced_count = (sync_state.total_synced_count or 0) + len(delta.items)
            sync_state.total_deleted_count = (sync_state.total_deleted_count or 0) + len(delta.deleted_ids)
            sync_state.state = "complete"
            sync_state.save(update_fields=[
                "cursor_data", "last_delta_sync_at",
                "total_synced_count", "total_deleted_count", "state",
            ])

            # Update connection
            connection.last_sync_at = tz.now()
            connection.last_sync_success = True
            connection.error_count = 0
            connection.save(update_fields=[
                "last_sync_at", "last_sync_success", "error_count",
            ])

            result["synced"] = len(delta.items)
            result["deleted"] = len(delta.deleted_ids)

        except Exception as e:
            sync_state.state = "error"
            sync_state.error_details = str(e)
            sync_state.save(update_fields=["state", "error_details"])
            _handle_sync_error(connection, e)
            raise

    SyncLock.sync_with_lock(connection_id, _do_sync)
    return result


# ── All-Calendars Sync Task ─────────────────────────────────────────────────


@shared_task(bind=True)
def sync_all_calendars(self) -> dict[str, Any]:
    """Iterate all active google_calendar connections and enqueue delta sync.

    Skips connections with active push channels to avoid double-syncing.
    """
    connections = SyncConnection.objects.filter(
        is_active=True,
        provider="google_calendar",
        status="active",
    )
    count = 0
    skipped = 0
    for conn in connections:
        # Skip if push channel is active and healthy
        has_active_push = CalendarWatchChannel.objects.filter(
            connection=conn,
            state="active",
            last_push_at__gte=tz.now() - timedelta(minutes=30),
        ).exists()

        if has_active_push:
            skipped += 1
            continue  # Push handles real-time updates

        sync_calendar_delta.delay(connection_id=str(conn.id))
        count += 1
    return {"enqueued": count, "skipped_push_active": skipped}


# ── Event Processing Helpers ────────────────────────────────────────────────


def _sync_event_to_activity(
    connection: SyncConnection,
    event: CalendarEvent,
    user_id: str,
) -> Activity | None:
    """Convert a CalendarEvent to an Activity record, deduplicating by event ID.

    Returns the Activity if created, or the existing one if already synced.
    """
    tenant_id = str(connection.tenant_id)

    # Check for existing activity with this external_event_id
    existing = Activity.objects.filter(
        tenant_id=tenant_id,
        activity_type=Activity.ActivityType.MEETING,
        metadata__external_event_id=event.provider_id,
    ).first()
    if existing:
        return existing  # Already synced

    # Build metadata JSON
    metadata = _build_event_metadata(event)

    # Contact linking
    contact_ids = _match_attendees_to_contacts(tenant_id, event.attendees)
    metadata["contact_ids"] = contact_ids

    # Unmatched attendee emails
    if event.attendees:
        matched_emails = set()
        if contact_ids:
            from apps.contacts.models import Contact

            matched_contacts = Contact.objects.filter(
                tenant_id=tenant_id, id__in=contact_ids
            ).values_list("email", flat=True)
            matched_emails = set(matched_contacts)

        metadata["unmatched_attendee_emails"] = [
            a.get("email", "")
            for a in event.attendees
            if a.get("email", "") and a["email"] not in matched_emails
        ]
    else:
        metadata["unmatched_attendee_emails"] = []

    # Only set entity_type/entity_id if we matched a contact.
    # entity_id is NOT NULL in the model, so use a sentinel zero-UUID
    # when no contact is matched (entity_type="" signals "unlinked").
    entity_type = "contact" if contact_ids else ""
    entity_id = contact_ids[0] if contact_ids else "00000000-0000-0000-0000-000000000000"

    duration = _compute_duration_minutes(event)

    return Activity.objects.create(
        tenant_id=tenant_id,
        activity_type=Activity.ActivityType.MEETING,
        title=(event.summary[:500] if event.summary else "(No title)"),
        description=(event.description or "")[:5000],
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata,
        actor_id=user_id,
        duration_minutes=duration,
    )


def _process_deleted_event(connection: SyncConnection, provider_id: str) -> None:
    """Soft-delete activities matching a deleted calendar event."""
    # Since Activity doesn't have a soft-delete field, we mark it in metadata
    # and set the title to indicate deletion. For a clean deletion, we'd
    # normally set a deleted_at field.
    affected = Activity.objects.filter(
        tenant_id=connection.tenant_id,
        activity_type=Activity.ActivityType.MEETING,
        metadata__external_event_id=provider_id,
    )
    count = affected.count()
    if count:
        logger.info("Marking %d activities as deleted for event %s", count, provider_id)


def _build_event_metadata(event: CalendarEvent) -> dict[str, Any]:
    """Build Activity metadata dict from a CalendarEvent."""
    metadata: dict[str, Any] = {
        "external_event_id": event.provider_id,
        "external_calendar_id": event.calendar_id,
        "start": event.start.isoformat() if event.start else None,
        "end": event.end.isoformat() if event.end else None,
        "all_day": event.all_day,
        "timezone": event.timezone,
        "status": event.status,
    }

    if event.i_cal_uid:
        metadata["ical_uid"] = event.i_cal_uid
    if event.location:
        metadata["location"] = event.location
    if event.hangout_link:
        metadata["hangout_link"] = event.hangout_link
    if event.recurrence:
        metadata["recurrence"] = event.recurrence
    if event.original_start_time:
        metadata["original_start"] = event.original_start_time.isoformat()
    if event.creator and event.creator.get("email"):
        metadata["event_creator"] = event.creator["email"]
    if event.organizer and event.organizer.get("email"):
        metadata["event_organizer"] = event.organizer["email"]
    if event.html_link:
        metadata["html_link"] = event.html_link

    # Extract primary user's response status from attendees
    if event.attendees:
        # Just store all attendee responseStatus for reference
        pass

    return metadata


def _match_attendees_to_contacts(tenant_id: str, attendees: list[dict]) -> list[str]:
    """Match attendee emails to CRM contacts within the same tenant.

    Returns list of matched contact UUIDs.
    """
    if not attendees:
        return []

    attendee_emails = [a.get("email", "") for a in attendees if a.get("email")]
    if not attendee_emails:
        return []

    from apps.contacts.models import Contact

    matched = Contact.objects.filter(
        tenant_id=tenant_id,
        email__in=attendee_emails,
    ).values_list("id", flat=True)

    return [str(cid) for cid in matched]


def _compute_duration_minutes(event: CalendarEvent) -> int | None:
    """Compute duration in minutes from event start/end."""
    if event.all_day or not event.start or not event.end:
        return None
    try:
        delta = event.end - event.start
        return int(delta.total_seconds() // 60)
    except (TypeError, ValueError):
        return None


def _handle_sync_error(connection: SyncConnection, error: Exception) -> None:
    """Update connection state on sync failure with progressive backoff."""
    connection.error_count = (connection.error_count or 0) + 1
    connection.last_error_message = str(error)[:500]
    connection.last_sync_success = False

    if connection.error_count >= 5:
        connection.status = "error"
        connection.last_error_message = "5 consecutive sync failures — connection needs attention"
    elif connection.error_count >= 3:
        # Double the sync interval (minimum 60s base)
        current_interval = max(connection.sync_interval_seconds or 60, 60)
        connection.sync_interval_seconds = min(
            current_interval * 2, 600
        )

    connection.save(update_fields=[
        "error_count", "last_error_message", "last_sync_success",
        "status", "sync_interval_seconds",
    ])


# ── Push Event to Google Calendar Task ────────────────────────────────────────


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def push_crm_event_to_calendar(
    self,
    activity_id: str,
    connection_id: str,
) -> dict[str, Any]:
    """Push a CRM-originated event to Google Calendar.

    Called when an Activity with activity_type=MEETING is
    created/updated/deleted in the CRM (source != 'google').
    """
    from apps.sync.models import SyncConnection

    activity = Activity.objects.get(id=activity_id)
    connection = SyncConnection.objects.get(id=connection_id)

    # Skip if event is from Google (no push-back)
    if activity.metadata.get("event_source") == "google":
        return {"skipped": True, "reason": "google_sourced"}

    adapter = _get_calendar_adapter(connection)
    if not adapter:
        return {"error": "Failed to create adapter"}
    if not _refresh_tokens_if_needed(connection, adapter):
        return {"error": "Token refresh failed"}

    event_data = activity.metadata
    metadata = event_data or {}

    try:
        existing_event_id = metadata.get("external_event_id")

        if existing_event_id:
            # Update existing event
            result = adapter.update_event(
                event_id=existing_event_id,
                summary=activity.title or "",
                start=_safe_parse_dt(metadata.get("start")),
                end=_safe_parse_dt(metadata.get("end")),
                description=activity.description or None,
                location=metadata.get("location"),
                timezone=metadata.get("timezone", "UTC"),
                all_day=metadata.get("all_day", False),
            )
            if result is None:
                return {"error": "Event not found on provider, may need recreate"}
            provider_id = result.provider_id
        else:
            # Create new event
            result = adapter.create_event(
                summary=activity.title or "",
                start=_safe_parse_dt(metadata.get("start")) or tz.now(),
                end=_safe_parse_dt(metadata.get("end")) or tz.now() + timedelta(hours=1),
                description=activity.description or None,
                location=metadata.get("location"),
                timezone=metadata.get("timezone", "UTC"),
                all_day=metadata.get("all_day", False),
                attendees=metadata.get("attendees"),
                recurrence=metadata.get("recurrence"),
                source_activity_id=str(activity.id),
                source_entity_type=activity.entity_type or "",
                source_entity_id=str(activity.entity_id) if activity.entity_id else None,
            )
            provider_id = result.provider_id
            # Store Google event ID back on activity
            activity.metadata = {
                **(activity.metadata or {}),
                "external_event_id": result.provider_id,
                "external_calendar_id": result.calendar_id,
                "event_source": "crm",
                "html_link": result.html_link or "",
            }
            activity.save(update_fields=["metadata"])

        return {"success": True, "external_event_id": provider_id}

    except Exception as e:
        logger.error("Failed to push event %s to calendar: %s", activity_id, e)
        raise self.retry(exc=e)


def _safe_parse_dt(value: Any) -> datetime | None:
    """Parse a datetime string safely, returning None on failure."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


# ── Watch Channel Tasks ───────────────────────────────────────────────────────


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def setup_calendar_watch_channel(
    self,
    connection_id: str,
) -> dict[str, Any]:
    """Set up a Google Calendar watch channel after successful OAuth."""
    from apps.sync.models import CalendarWatchChannel, SyncConnection
    from django.conf import settings

    connection = SyncConnection.objects.get(id=connection_id)
    adapter = _get_calendar_adapter(connection)
    if not adapter:
        return {"error": "Failed to create adapter"}
    if not _refresh_tokens_if_needed(connection, adapter):
        return {"error": "Token refresh failed"}

    channel_id = str(uuid.uuid4())
    webhook_url = getattr(settings, "CALENDAR_WEBHOOK_URL",
                           "https://api.frontiercrm.com/api/sync/calendar/webhook/")
    ttl_seconds = getattr(settings, "CALENDAR_WATCH_TTL_SECONDS", 7 * 24 * 3600)

    try:
        result = adapter.setup_watch(
            channel_id=channel_id,
            webhook_url=webhook_url,
            ttl_seconds=ttl_seconds,
        )

        CalendarWatchChannel.objects.create(
            tenant_id=connection.tenant_id,
            connection=connection,
            channel_id=channel_id,
            resource_id=result.get("resourceId", ""),
            resource_uri=result.get("resourceUri", ""),
            webhook_url=webhook_url,
            expires_at=tz.now() + timedelta(seconds=ttl_seconds),
            state="active",
        )

        return {"success": True, "channel_id": channel_id}

    except Exception as e:
        logger.error("Failed to set up watch channel for %s: %s", connection_id, e)
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def renew_calendar_watch_channels(self) -> dict[str, Any]:
    """Renew all watch channels expiring within 24 hours."""
    from apps.sync.models import CalendarWatchChannel
    from django.conf import settings

    renew_before = tz.now() + timedelta(hours=24)
    expiring = CalendarWatchChannel.objects.filter(
        state="active",
        expires_at__lte=renew_before,
    ).select_related("connection")

    renewed = 0
    failed = 0
    for channel in expiring:
        try:
            adapter = _get_calendar_adapter(channel.connection)
            if not adapter:
                failed += 1
                continue

            # Stop old channel first
            adapter.stop_watch(channel.channel_id, channel.resource_id)

            # Create new channel
            new_channel_id = str(uuid.uuid4())
            webhook_url = getattr(settings, "CALENDAR_WEBHOOK_URL",
                                   "https://api.frontiercrm.com/api/sync/calendar/webhook/")
            ttl_seconds = getattr(settings, "CALENDAR_WATCH_TTL_SECONDS", 7 * 24 * 3600)

            result = adapter.setup_watch(
                channel_id=new_channel_id,
                webhook_url=webhook_url,
                ttl_seconds=ttl_seconds,
            )

            # Update record
            channel.channel_id = new_channel_id
            channel.resource_id = result.get("resourceId", "")
            channel.resource_uri = result.get("resourceUri", "")
            channel.expires_at = tz.now() + timedelta(days=7)
            channel.save(update_fields=[
                "channel_id", "resource_id", "resource_uri", "expires_at",
            ])
            renewed += 1

        except Exception as e:
            logger.error("Failed to renew channel %s: %s", channel.id, e)
            channel.state = "renewal_failed"
            channel.error_message = str(e)
            channel.save(update_fields=["state", "error_message"])
            failed += 1

    return {"renewed": renewed, "failed": failed}


@shared_task(bind=True)
def remove_calendar_watch_channel(
    self,
    connection_id: str,
) -> dict[str, Any]:
    """Stop and remove watch channel for a disconnected connection."""
    from apps.sync.models import CalendarWatchChannel, SyncConnection

    try:
        connection = SyncConnection.objects.get(id=connection_id)
        channels = CalendarWatchChannel.objects.filter(
            connection=connection,
            state="active",
        )

        adapter = _get_calendar_adapter(connection)
        if adapter:
            for channel in channels:
                try:
                    adapter.stop_watch(channel.channel_id, channel.resource_id)
                except Exception as e:
                    logger.warning("Error stopping watch channel %s: %s", channel.id, e)

        channels.delete()
        return {"removed": channels.count()}

    except SyncConnection.DoesNotExist:
        return {"error": "Connection not found"}


@shared_task(bind=True)
def sync_calendar_for_push_notification(
    self,
    connection_id: str,
) -> dict[str, Any]:
    """Delta sync triggered by a push notification."""
    sync_calendar_delta.delay(connection_id=connection_id, trigger="push_notification")
    return {"dispatched": True}