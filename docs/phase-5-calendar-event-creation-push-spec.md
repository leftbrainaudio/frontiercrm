# Phase 5 — Calendar Event Creation & Push Notifications Specification

**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)
**Status:** Draft for review
**Priority:** P2 (Event Creation) / P2 (Push Notifications)

---

## Table of Contents

1. [ADR-027: Calendar Event Creation (Bidirectional Write)](#1-adr-027-calendar-event-creation-bidirectional-write)
2. [ADR-028: Calendar Push Notifications via Google Cloud Pub/Sub](#2-adr-028-calendar-push-notifications-via-google-cloud-pubsub)
3. [OAuth Scope Extension: Read → Read+Write](#3-oauth-scope-extension-read--readwrite)
4. [Adapter Contract Extension](#4-adapter-contract-extension)
5. [REST API Contracts](#5-rest-api-contracts)
6. [Push Notification Architecture](#6-push-notification-architecture)
7. [Frontend Integration Points](#7-frontend-integration-points)
8. [Celery Tasks & Schedule Changes](#8-celery-tasks--schedule-changes)
9. [Configuration & Environment Variables](#9-configuration--environment-variables)
10. [Implementation Order](#10-implementation-order)
11. [Acceptance Criteria](#11-acceptance-criteria)
12. [Appendix: Conflict Resolution Strategies](#12-appendix-conflict-resolution-strategies)

---

## 1. ADR-027: Calendar Event Creation (Bidirectional Write)

**Status:** Proposed
**Date:** 2026-06-30
**Supersedes:** ADR-024 Decision #4 (read-only scope)

### Context

FrontierCRM currently syncs Google Calendar events **into** the CRM as Activity records (read-only). Users need to create CRM activities (meetings, tasks) and push them **out** to Google Calendar, with bidirectional updates — changes made on either side sync to the other.

The existing architecture provides:
- `CalendarSyncAdapter` base class with read-only delta sync (`get_calendar_delta`)
- `GoogleCalendarAdapter` implementing the read-only contract
- `Activity` model with `MEETING` type and `metadata.external_event_id` for dedup
- `SyncConflict` model for logging conflicts (currently unused)
- OAuth token infrastructure with `include_granted_scopes=true`

### Decision

1. **Extend OAuth scope** from `calendar.events.readonly` to `calendar.events`. Google's additive scope model means existing tokens remain valid; re-auth prompts users once for the new scope via `include_granted_scopes=true`. Existing `SyncConnection` records with the old scope need an `is_missing_write_scope` flag.

2. **New adapter methods on `CalendarSyncAdapter`** — not overloaded onto `get_calendar_delta`. Three explicit methods: `create_event()`, `update_event()`, `delete_event()`.

3. **CRM → Google immediate push.** When an Activity with `activity_type=MEETING` is created/updated/deleted in the CRM (and a `SyncConnection` for `google_calendar` exists for the actor), a Celery task pushes the change to Google Calendar synchronously (fire-and-forget). The Actor commits the Google event ID (`external_event_id`) back into the Activity's metadata.

4. **Last-write-wins conflict resolution** for the initial build. The last modification timestamp wins in both directions. Log conflicts to `SyncConflict` for audit but do not block. See Appendix for future strategies.

5. **No changes to the read sync direction.** `get_calendar_delta` continues to import Google-side changes as before. When a Google-synced event is later updated in the CRM, the reverse direction applies.

6. **Update existing synced events in place.** When `get_calendar_delta` returns an event whose `external_event_id` already exists in an Activity, update the Activity fields from the Google Calendar data (overwriting CRM changes). This is "Google side wins" for the pull direction.

7. **New `metadata.event_source` convention.** Distinguish CRM-originated events from Google-originated:
   - `"google"` — synced from Google Calendar
   - `"crm"` — created in CRM, pushed to Google
   This enables: skipping push-back for Google-originated events; showing correct source in UI.

### Rejected Alternatives

1. **Bidirectional sync as a single operation** — rejected. The read direction (Google→CRM) is delta-based with sync tokens. The write direction (CRM→Google) is an immediate push. Merging them into a single method creates coupling between two different sync primitives.

2. **Polling for CRM→Google push** — rejected. Creates (event, push new event to Google) should be near-instant. Users who create a meeting in the CRM expect it to appear in their calendar within seconds, not minutes.

3. **Generic "create external event" hook on Activity save** — rejected. Too broad: note/email/file_upload activities should not trigger calendar pushes. Explicit method call from the create-task API is safer.

4. **Manual conflict resolution UI** — rejected for initial build. Last-write-wins is sufficient for team of <50 users per tenant. Add manual conflict resolution if users report data loss.

---

## 2. ADR-028: Calendar Push Notifications via Google Cloud Pub/Sub

**Status:** Proposed
**Date:** 2026-06-30
**Supersedes:** ADR-024 Decision #3 (polling-only)

### Context

The current calendar sync uses Celery Beat polling every 15 minutes. This introduces a 15-minute latency between a user changing their Google Calendar and seeing the change in FrontierCRM. For a CRM that shows upcoming meetings on deal timelines and dashboards, 15-minute latency is too slow for user trust.

Google Calendar supports push notifications via a **watch channel** pattern:
1. The app calls `POST /calendars/{calendarId}/events/watch` with a webhook URL and a unique channel ID.
2. Google sends a POST to that webhook URL whenever events change on the calendar.
3. The app then performs a delta sync (using syncToken) for that user.

### Decision

1. **Use Google Calendar Watch API** (not Cloud Pub/Sub directly). Google Calendar v3's `events.watch` endpoint sends notifications to any public HTTPS endpoint. It does not require Google Cloud Pub/Sub — we register a webhook URL directly.

2. **New public webhook endpoint:** `POST /api/sync/calendar/webhook/` — publicly reachable, authenticated by `X-Goog-Channel-ID` and `X-Goog-Resource-ID` headers (Google's own verification). Returns `200 OK` or `202 Accepted` within 30 seconds (Google's timeout). No Django authentication required.

3. **Channel lifecycle managed by Celery Beat:**
   - **Setup:** After initial OAuth + full sync, register a watch channel. Store channel metadata in a new `CalendarWatchChannel` model (or Redis).
   - **Renewal:** Google watch channels expire after 1 hour (minimum) to 7 days (maximum). We use a 7-day TTL. A daily Celery Beat task checks channels expiring in <24 hours and renews them.
   - **Teardown:** When a user disconnects calendar sync, call `POST /channels/stop` to stop the watch channel.

4. **Fallback to polling** when push is unavailable. If the webhook endpoint is unreachable by Google, or if `events.watch` returns an error (e.g., user is over the watch limit of ~200 channels), fall back to the existing 15-minute polling. The `CalendarWatchChannel.state` field tracks this.

5. **Watch channel per user, per calendar.** One watch channel per `SyncConnection` with `provider="google_calendar"`. Only the primary calendar for now — multi-calendar support is future work.

6. **No dependency on Google Cloud Pub/Sub.** The Calendar Watch API sends directly to a public HTTPS endpoint. We do not need GCP Pub/Sub topics or subscriptions. (Note: the task description mentions "Google Cloud Pub/Sub" but the Calendar API's native watch mechanism achieves the same result with less infrastructure.)

### Rejected Alternatives

1. **Google Cloud Pub/Sub topics + subscriptions** — rejected. Requires a GCP project, Pub/Sub API enablement, a push subscription endpoint, and additional IAM permissions. The Calendar Watch API already provides the push-to-endpoint pattern natively.

2. **WebSocket/SSE for real-time calendar updates** — rejected. The notification we receive from Google is "something changed, please sync" — not the actual event data. We still need to call the delta sync API. A notification → delta sync pattern is better served by a webhook endpoint than a persistent connection.

3. **Reduce polling interval to 1 minute instead of push** — rejected. Google Calendar API has a per-user quota of ~100 queries per 100 seconds. Dropping from 15-minute polling to 1-minute would consume 10x the quota with no architectural improvement over the existing polling.

### Consequences

- The public webhook endpoint must be reachable from Google's servers. For local dev, use a tunneling service (ngrok, serveo) or a staging URL.
- Channel renewal is critical — if a channel expires and is not renewed, updates go undetected until the next polling cycle. The daily renewal task with 24-hour grace window mitigates this.
- Google imposes a maximum of ~200 watch channels per project. This is adequate for most FrontierCRM tenants but should be monitored.

---

## 3. OAuth Scope Extension: Read → Read+Write

### Current Scopes

| Scope | Current | New |
|-------|---------|-----|
| `calendar.events.readonly` | ✅ Existing | Replaced |
| `calendar.events` | ❌ | ✅ Added |

### Migration Strategy

Existing `SyncConnection` records with `provider="google_calendar"` and scope `calendar.events.readonly` need to be upgraded. Two approaches:

**Option A (Recommended): Detect and re-auth**
1. When a user tries to create a calendar event from the CRM, check if their `SyncConnection.scopes` includes `calendar.events`.
2. If not, return an error with `"requires_upgrade": True` and a new OAuth URL that requests `calendar.events` with `include_granted_scopes=true`.
3. The frontend shows a "Grant write access" prompt with one click.

**Option B: Batch scope upgrade**
1. Add a new action: `POST /api/sync/connections/{id}/calendar/upgrade-scope/`.
2. Calls `generate_calendar_oauth_url()` with `calendar.events` scope.
3. User authorizes, callback updates the existing connection's scopes.

**Recommendation:** Use Option B for the initial rollout. The frontend shows a one-time banner: "Calendar sync needs write access to create events" with a "Grant access" button.

### Scope change in code

```python
# apps/sync/oauth.py — updated
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
```

This single scope covers both read and write operations on a user's calendar events. It replaces `calendar.events.readonly` for all users.

### Verify granted scope

After callback, verify the granted scope includes write access:

```python
def _verify_calendar_scopes(access_token: str) -> list[str]:
    """Fetch granted scopes from tokeninfo and verify write access."""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/tokeninfo",
        headers=headers,
        timeout=10,
    )
    if resp.status_code == 200:
        scope_str = resp.json().get("scope", "")
        return scope_str.split()
    return []
```

---

## 4. Adapter Contract Extension

### CalendarSyncAdapter — new methods

Add to `apps/sync/adapters/base.py`:

```python
class CalendarSyncAdapter(ABC):
    # ── Existing read methods ─────────────────────────────────────────
    @abstractmethod
    def get_calendar_delta(self, cursor: dict | None) -> CalendarDeltaResult:
        ...

    @abstractmethod
    def get_initial_cursor(self) -> dict:
        ...

    # ── New write methods ─────────────────────────────────────────────

    @abstractmethod
    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        *,
        description: str | None = None,
        location: str | None = None,
        timezone: str = "UTC",
        all_day: bool = False,
        attendees: list[dict] | None = None,
        recurrence: list[str] | None = None,
        hangout_link: str | None = None,
        source_activity_id: str | None = None,
        source_entity_type: str | None = None,
        source_entity_id: str | None = None,
    ) -> CalendarEvent:
        """Create a new calendar event on the provider.
        
        Returns the full CalendarEvent as created by the provider
        (including the provider-assigned event ID).
        """
        ...

    @abstractmethod
    def update_event(
        self,
        event_id: str,
        *,
        summary: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        description: str | None = None,
        location: str | None = None,
        timezone: str | None = None,
        all_day: bool | None = None,
        attendees: list[dict] | None = None,
        recurrence: list[str] | None = None,
    ) -> CalendarEvent | None:
        """Update an existing calendar event on the provider.
        
        Returns the updated CalendarEvent, or None if the event
        was deleted on the provider side.
        """
        ...

    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event on the provider.
        
        Returns True if deletion succeeded, False if the event
        was already deleted or not found.
        """
        ...
```

### GoogleCalendarAdapter — write implementation

New methods on `GoogleCalendarAdapter` in `apps/sync/adapters/google_calendar/adapter.py`:

```python
class GoogleCalendarAdapter(CalendarSyncAdapter):
    # ... existing methods ...

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        *,
        description: str | None = None,
        location: str | None = None,
        timezone: str = "UTC",
        all_day: bool = False,
        attendees: list[dict] | None = None,
        recurrence: list[str] | None = None,
        hangout_link: str | None = None,
        source_activity_id: str | None = None,
        source_entity_type: str | None = None,
        source_entity_id: str | None = None,
    ) -> CalendarEvent:
        """Create a Google Calendar event via POST."""
        body = self._build_event_body(
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location,
            timezone=timezone,
            all_day=all_day,
            attendees=attendees,
            recurrence=recurrence,
        )
        
        # Add extended properties to track CRM origin
        body["extendedProperties"] = {
            "private": {
                "frontiercrm_activity_id": source_activity_id or "",
                "frontiercrm_entity_type": source_entity_type or "",
                "frontiercrm_entity_id": source_entity_id or "",
                "frontiercrm_source": "crm",
            }
        }

        response = self._client.post("calendars/primary/events", body=body)
        return _parse_google_event(response)

    def update_event(
        self,
        event_id: str,
        *,
        summary: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        description: str | None = None,
        location: str | None = None,
        timezone: str | None = None,
        all_day: bool | None = None,
        attendees: list[dict] | None = None,
        recurrence: list[str] | None = None,
    ) -> CalendarEvent | None:
        """Update a Google Calendar event via PATCH."""
        body: dict[str, Any] = {}
        if summary is not None:
            body["summary"] = summary
        if description is not None:
            body["description"] = description
        # ... build body from kwargs ...
        
        try:
            response = self._client.patch(
                f"calendars/primary/events/{event_id}",
                body=body,
            )
            return _parse_google_event(response)
        except CalendarNotFoundError:
            return None

    def delete_event(self, event_id: str) -> bool:
        """Delete a Google Calendar event via DELETE."""
        try:
            self._client.delete(f"calendars/primary/events/{event_id}")
            return True
        except CalendarNotFoundError:
            return False
```

### GoogleCalendarApiClient — new HTTP methods

```python
class GoogleCalendarApiClient:
    # ... existing get/post ...

    def patch(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated PATCH request."""
        return self._request("PATCH", path, json=body)

    def delete(self, path: str) -> dict[str, Any]:
        """Make an authenticated DELETE request."""
        return self._request("DELETE", path)

    # Extended properties helper
    def _build_event_body(self, ...) -> dict:
        """Build the Google Calendar event JSON body."""
        ...
```

### Event body builder

```python
def _build_event_body(
    summary: str,
    start: datetime,
    end: datetime,
    *,
    description: str | None = None,
    location: str | None = None,
    timezone: str = "UTC",
    all_day: bool = False,
    attendees: list[dict] | None = None,
    recurrence: list[str] | None = None,
) -> dict[str, Any]:
    """Build Google Calendar API event body from normalized parameters."""
    body: dict[str, Any] = {
        "summary": summary[:500],
    }

    if all_day:
        body["start"] = {"date": start.date().isoformat(), "timeZone": timezone}
        body["end"] = {"date": end.date().isoformat(), "timeZone": timezone}
    else:
        body["start"] = {"dateTime": start.isoformat(), "timeZone": timezone}
        body["end"] = {"dateTime": end.isoformat(), "timeZone": timezone}

    if description:
        body["description"] = description[:5000]
    if location:
        body["location"] = location
    if attendees:
        body["attendees"] = [
            {
                "email": a.get("email"),
                "displayName": a.get("displayName"),
                # Do not set responseStatus — that's the attendee's choice
            }
            for a in attendees
            if a.get("email")
        ]
    if recurrence:
        body["recurrence"] = recurrence[:10]  # Cap at 10 RRULEs
        body["singleEvents"] = False

    return body
```

### metadata.event_source distinction

When an Activity originates from a CRM user (not synced from Google):

```python
CRM_EVENT_METADATA = {
    "event_source": "crm",
    "external_event_id": "...",       # Set after Google create succeeds
    "external_calendar_id": "primary",
    "start": "...",
    "end": "...",
    "all_day": False,
    "timezone": "UTC",
    "location": "...",
    "status": "confirmed",
    "contact_ids": [...],
    "deal_ids": [...],   # NEW — more general than entity_id
    "created_from_entity_type": "deal",  # Link back to CRM entity
    "created_from_entity_id": "uuid",
}
```

---

## 5. REST API Contracts

### Calendar Event CRUD

```
POST   /api/sync/calendar/events/         → Create event (CRM → Google)
PUT    /api/sync/calendar/events/{id}/     → Update event
DELETE /api/sync/calendar/events/{id}/     → Delete event
```

These are **proxy endpoints** — they create/update/delete on Google Calendar via the user's sync connection, then update the corresponding Activity record in the CRM.

#### Create Calendar Event

```
POST /api/sync/calendar/events/
```

**Request Body:**
```json
{
  "summary": "Q3 Review with Alice",
  "start": "2026-07-15T14:00:00Z",
  "end": "2026-07-15T15:00:00Z",
  "description": "Quarterly business review",
  "location": "Conference Room A",
  "timezone": "America/New_York",
  "all_day": false,
  "attendees": [
    {"email": "alice@company.com", "displayName": "Alice"}
  ],
  "source_entity_type": "deal",
  "source_entity_id": "deal-uuid-123",
  "link_to_contacts": ["contact-uuid-1"],
  "link_to_deal": "deal-uuid-123",
  "remind_before_minutes": 15
}
```

**Response 201:**
```json
{
  "id": "activity-uuid",
  "external_event_id": "google-event-id",
  "html_link": "https://www.google.com/calendar/event?eid=...",
  "summary": "Q3 Review with Alice",
  "start": "2026-07-15T14:00:00Z",
  "end": "2026-07-15T15:00:00Z",
  "status": "confirmed"
}
```

#### Update Calendar Event

```
PUT /api/sync/calendar/events/{activity_id}/
```

**Request Body** (partial update — only send changed fields):
```json
{
  "summary": "Q3 Review Rescheduled",
  "start": "2026-07-16T10:00:00Z",
  "end": "2026-07-16T11:00:00Z"
}
```

**Response 200:**
```json
{
  "id": "activity-uuid",
  "external_event_id": "google-event-id",
  "summary": "Q3 Review Rescheduled",
  "start": "2026-07-16T10:00:00Z",
  "end": "2026-07-16T11:00:00Z",
  "status": "confirmed"
}
```

**Response 404:** If the Google Calendar event was deleted externally.

#### Delete Calendar Event

```
DELETE /api/sync/calendar/events/{activity_id}/
```

**Response 204:** No content.

**Response 409:** If the event was already deleted on Google Calendar (soft-delete the Activity instead).

#### Calendar OAuth Scope Upgrade

```
POST /api/sync/connections/{id}/calendar/upgrade-scope/
```

**Response 200:**
```json
{
  "url": "https://accounts.google.com/o/oauth2/auth?scope=calendar.events...",
  "state": "random-state-token",
  "connection_id": "conn-uuid"
}
```

The frontend opens this URL in a popup. The callback (same as `calendar/callback/`) updates the existing connection's scopes.

### New: Calendar Watch Channel Status

```
GET /api/sync/calendar/watch-status/
```

**Response 200:**
```json
{
  "connected": true,
  "push_enabled": true,
  "watch_channel_id": "channel-uuid",
  "watch_expires_at": "2026-07-07T10:00:00Z",
  "last_push_received_at": "2026-06-30T09:15:00Z",
  "fallback_polling_active": false
}
```

### New: Calendar Webhook Receiver (Public)

```
POST /api/sync/calendar/webhook/  (no auth — public endpoint)
```

Webhook payload from Google Calendar notification channel. Not a user-facing endpoint.

---

## 6. Push Notification Architecture

### Architecture Overview

```
┌──────────────┐     POST (notification)      ┌──────────────────────────┐
│              │──────────────────────────────→│  FrontierCRM             │
│ Google       │   /api/sync/calendar/webhook/ │                          │
│ Calendar     │                               │  1. Verify channel ID    │
│ Watch API    │                               │  2. Look up SyncConnect  │
│              │       Headers:                │  3. Enqueue delta sync   │
│              │  X-Goog-Channel-ID            │  4. Return 202           │
│              │  X-Goog-Resource-ID           └──────────────────────────┘
│              │  X-Goog-Resource-State               │
│              │  X-Goog-Message-Number                │ dispatch
└──────────────┘                                     ▼
                                            ┌──────────────────┐
                                            │ sync_calendar_    │
                                            │ delta (celery)    │
                                            └──────────────────┘
                                                     │
                                                     ▼
                                            ┌──────────────────┐
                                            │ Google Calendar  │
                                            │ API (syncToken)  │
                                            └──────────────────┘
```

### Watch Channel Setup

After OAuth callback + initial full sync completes successfully:

```python
def setup_watch_channel(connection_id: str) -> dict[str, Any]:
    """Register a Google Calendar watch channel for push notifications.
    
    Called after successful initial sync.
    Returns channel metadata or raises if push setup fails.
    """
    connection = SyncConnection.objects.get(id=connection_id)
    adapter = create_adapter(connection)
    
    channel_id = str(uuid.uuid4())
    webhook_url = _get_calendar_webhook_url()
    ttl_seconds = 7 * 24 * 3600  # 7 days
    
    result = adapter.setup_watch(
        channel_id=channel_id,
        webhook_url=webhook_url,
        ttl_seconds=ttl_seconds,
    )
    
    # Store channel in CalendarWatchChannel
    CalendarWatchChannel.objects.create(
        tenant_id=connection.tenant_id,
        connection=connection,
        channel_id=channel_id,
        resource_id=result["resourceId"],
        resource_uri=result.get("resourceUri", ""),
        webhook_url=webhook_url,
        expires_at=timezone.now() + timedelta(seconds=ttl_seconds),
        state="active",
    )
    
    return result
```

### Watch Channel Renewal

```python
@shared_task
def renew_expiring_watch_channels() -> dict[str, Any]:
    """Renew calendar watch channels expiring within 24 hours.
    
    Runs daily via Celery Beat.
    """
    renew_before = timezone.now() + timedelta(hours=24)
    expiring = CalendarWatchChannel.objects.filter(
        state="active",
        expires_at__lte=renew_before,
    ).select_related("connection")
    
    renewed = 0
    failed = 0
    for channel in expiring:
        try:
            # Stop old channel first
            adapter = create_adapter(channel.connection)
            adapter.stop_watch(channel.channel_id, channel.resource_id)
            
            # Create new channel
            new_channel_id = str(uuid.uuid4())
            result = adapter.setup_watch(
                channel_id=new_channel_id,
                webhook_url=channel.webhook_url,
                ttl_seconds=7 * 24 * 3600,
            )
            
            # Update record
            channel.channel_id = new_channel_id
            channel.resource_id = result["resourceId"]
            channel.resource_uri = result.get("resourceUri", "")
            channel.expires_at = timezone.now() + timedelta(days=7)
            channel.save(update_fields=["channel_id", "resource_id",
                                         "resource_uri", "expires_at"])
            renewed += 1
        except Exception as e:
            logger.error(f"Failed to renew channel {channel.id}: {e}")
            # Don't mark failed — polling fallback catches changes
            channel.state = "renewal_failed"
            channel.error_message = str(e)
            channel.save(update_fields=["state", "error_message"])
            failed += 1
    
    return {"renewed": renewed, "failed": failed}
```

### Webhook Receiver

```python
@api_view(["POST"])
@permission_classes([AllowAny])
@method_decorator(csrf_exempt)
def calendar_webhook_receiver(request: Request) -> Response:
    """Receive Google Calendar push notifications.
    
    Google sends POST requests with verification headers:
    - X-Goog-Channel-ID: UUID matching our watch channel
    - X-Goog-Resource-ID: Calendar resource UUID
    - X-Goog-Resource-State: "sync" (initial) or "exists" (change)
    - X-Goog-Message-Number: monotonically increasing
    
    We respond synchronously within 30 seconds (Google timeout).
    Actual work is dispatched to a Celery task.
    """
    channel_id = request.headers.get("X-Goog-Channel-ID", "")
    resource_id = request.headers.get("X-Goog-Resource-ID", "")
    resource_state = request.headers.get("X-Goog-Resource-State", "")
    message_number = request.headers.get("X-Goog-Message-Number", "")
    
    # Handle Google's channel verification request
    # Google sends a "sync" notification when the channel is created
    if resource_state == "sync":
        return Response({"status": "channel_verified"}, status=status.HTTP_200_OK)
    
    # Find the matching watch channel
    try:
        channel = CalendarWatchChannel.objects.get(
            channel_id=channel_id,
            resource_id=resource_id,
            state="active",
        )
        channel.last_push_at = timezone.now()
        channel.last_message_number = message_number
        channel.save(update_fields=["last_push_at", "last_message_number"])
        
        # Enqueue delta sync for this connection
        sync_calendar_delta.delay(
            connection_id=str(channel.connection_id),
            trigger="push_notification",
        )
        
        return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)
        
    except CalendarWatchChannel.DoesNotExist:
        logger.warning(f"Received notification for unknown channel {channel_id}")
        return Response({"status": "unknown_channel"}, status=status.HTTP_200_OK)
```

### CalendarWatchChannel Model

```python
class CalendarWatchChannel(TenantScopedModel):
    """Tracks active Google Calendar watch channels for push notifications.
    
    One channel per SyncConnection (primary calendar).
    Channels expire after 7 days and must be renewed.
    """
    
    connection = models.ForeignKey(
        SyncConnection, on_delete=models.CASCADE,
        related_name="watch_channels",
    )
    
    channel_id = models.CharField(max_length=255, unique=True)
    resource_id = models.CharField(max_length=512)
    resource_uri = models.CharField(max_length=1024, blank=True, default="")
    webhook_url = models.CharField(max_length=1024)
    
    expires_at = models.DateTimeField()
    last_push_at = models.DateTimeField(null=True, blank=True)
    last_message_number = models.BigIntegerField(null=True, blank=True)
    
    STATE_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("renewal_failed", "Renewal Failed"),
        ("stopped", "Stopped"),
    ]
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default="active")
    error_message = models.TextField(blank=True, default="")
    
    class Meta:
        db_table = "sync_calendar_watch_channels"
        indexes = [
            models.Index(fields=["channel_id"]),
            models.Index(fields=["state", "expires_at"]),
            models.Index(fields=["connection"]),
        ]
```

### Fallback Logic

```python
def sync_calendar_for_user(connection_id: str, trigger: str = "scheduled") -> None:
    """Sync calendar events, preferring push but falling back to polling.
    
    If a watch channel is active and push was received recently (< 30 min ago),
    this is a delta sync. Otherwise, fall back to the polling schedule.
    """
    connection = SyncConnection.objects.get(id=connection_id)
    
    # Check if push is working
    push_healthy = CalendarWatchChannel.objects.filter(
        connection=connection,
        state="active",
        last_push_at__gte=timezone.now() - timedelta(minutes=30),
    ).exists()
    
    if not push_healthy:
        # Push is down — use polling schedule (15 min)
        _execute_delta_sync(connection_id, trigger)
    else:
        # Push is healthy — this is a push-triggered sync
        _execute_delta_sync(connection_id, trigger)
```

---

## 7. Frontend Integration Points

### New Calendar Event Button

**Location:** Activity compose bar, Deal timeline header, Contact detail page.

```
[Activity Compose Bar]
┌──────────────────────────────────────────────────┐
│ [Meeting] [Note] [Call] [Email] [Task] [Calendar]│ ← New button
└──────────────────────────────────────────────────┘
```

### Meeting Creation Form

When "Calendar" is clicked, show a meeting creation form:

```
┌─ Create Calendar Event ──────────────────────────┐
│                                                    │
│  Title:     [____________________________]         │
│  Date:      [____] Time: [____] Duration: [____]  │
│  All day:   [ ]                                    │
│  Location:  [____________________________]         │
│  Attendees: [Add people...]                       │
│             • alice@company.com  [Remove]          │
│             • bob@company.com    [Remove]          │
│  Description:                                      │
│  [________________________________]               │
│                                                    │
│  Link to: [Deal ▼] [Select deal...]               │
│                                                    │
│  Reminder: 15 minutes before ▼                     │
│                                                    │
│  [Create Event]  [Cancel]                          │
└────────────────────────────────────────────────────┘
```

### Deal Timeline Integration

In the deal timeline, synced Google Calendar events and CRM-created events appear together. CRM-created events have a visual indicator showing they were created in FrontierCRM:

```
Deal Timeline
┌──────────────────────────────────────────────────┐
│ [Calendar icon] Q3 Review with Alice              │
│  Today 2:00 PM - 3:00 PM · Conference Room A     │
│  Created in FrontierCRM [Edit] [Delete]           │
├──────────────────────────────────────────────────┤
│ [Calendar icon] Alice Onboarding Call             │
│  Yesterday 10:00 AM - 11:00 AM · Google Meet     │
│  Synced from Google Calendar                      │
└──────────────────────────────────────────────────┘
```

### Scope Upgrade Banner

When a user tries to create a calendar event but hasn't granted write scope:

```
┌─ ⚠ Calendar Write Access Required ────────────────┐
│                                                    │
│  To create events on your Google Calendar, you     │
│  need to grant write access.                       │
│                                                    │
│  [Grant Access] [Learn More]                       │
└────────────────────────────────────────────────────┘
```

### Push Notification Status

Settings → Calendar Sync → Push Status:

```
Push Notifications: ✅ Active
Channel expires: July 7, 2026 (renews automatically)
Last notification: 2 minutes ago

[Disconnect Calendar]
```

---

## 8. Celery Tasks & Schedule Changes

### New Tasks

```python
# apps/sync/tasks_calendar.py — additions

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def push_crm_event_to_calendar(
    self,
    activity_id: str,
    connection_id: str,
) -> dict[str, Any]:
    """Push a CRM-originated event to Google Calendar.
    
    Called when an Activity with activity_type=MEETING is
    created/updated/deleted in the CRM (source != "google").
    """
    from apps.activities.models import Activity
    from apps.sync.models import SyncConnection
    
    activity = Activity.objects.get(id=activity_id)
    connection = SyncConnection.objects.get(id=connection_id)
    
    # Skip if event is from Google (no push-back)
    if activity.metadata.get("event_source") == "google":
        return {"skipped": True, "reason": "google_sourced"}
    
    adapter = _create_calendar_adapter(connection)
    event_data = activity.metadata
    
    try:
        if event_data.get("external_event_id"):
            # Update existing event
            result = adapter.update_event(
                event_id=event_data["external_event_id"],
                summary=activity.title,
                start=datetime.fromisoformat(event_data["start"]),
                end=datetime.fromisoformat(event_data["end"]),
                ...
            )
        else:
            # Create new event
            result = adapter.create_event(...)
            
            # Store Google event ID back on activity
            activity.metadata["external_event_id"] = result.provider_id
            activity.metadata["external_calendar_id"] = result.calendar_id
            activity.metadata["event_source"] = "crm"
            activity.metadata["html_link"] = result.html_link
            activity.save(update_fields=["metadata"])
        
        return {"success": True, "external_event_id": result.provider_id}
        
    except Exception as e:
        logger.error(f"Failed to push event {activity_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def setup_calendar_watch_channel(
    self,
    connection_id: str,
) -> dict[str, Any]:
    """Set up a Google Calendar watch channel after successful OAuth."""
    # ... implementation per section 6 ...


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def renew_calendar_watch_channels(self) -> dict[str, Any]:
    """Renew all watch channels expiring within 24 hours."""
    # ... implementation per section 6 ...


@shared_task(bind=True)
def remove_calendar_watch_channel(
    self,
    connection_id: str,
) -> dict[str, Any]:
    """Stop and remove watch channel for a disconnected connection."""
    # ... implementation ...


@shared_task(bind=True)
def sync_calendar_for_push_notification(
    self,
    connection_id: str,
) -> dict[str, Any]:
    """Delta sync triggered by a push notification.
    
    Same logic as sync_calendar_delta but marks the sync as
    push-triggered for monitoring.
    """
    # Calls existing sync_calendar_delta logic with trigger="push_notification"
```

### Beat Schedule Changes

```python
# config/beat_schedule.py — additions

CALENDAR_WATCH_RENEWAL = {
    "renew-calendar-watch-channels": {
        "task": "apps.sync.tasks_calendar.renew_calendar_watch_channels",
        "schedule": timedelta(hours=6),  # Check every 6 hours
        "options": {"expires": 3600},
    },
}

BEAT_SCHEDULE.update(CALENDAR_WATCH_RENEWAL)
```

The existing 15-minute polling schedule remains as a fallback. It is not removed — when push channels are active, the polling task skips connections with healthy push channels.

### Polling → Push-aware guard

Modify `sync_all_calendars` to skip connections with active push:

```python
def sync_all_calendars(self) -> dict[str, Any]:
    connections = SyncConnection.objects.filter(
        is_active=True,
        provider="google_calendar",
        status="active",
    )
    count = 0
    for conn in connections:
        # Skip if push channel is active and healthy
        has_active_push = CalendarWatchChannel.objects.filter(
            connection=conn,
            state="active",
            last_push_at__gte=timezone.now() - timedelta(minutes=30),
        ).exists()
        
        if has_active_push:
            continue  # Push handles real-time updates
        
        sync_calendar_delta.delay(connection_id=str(conn.id))
        count += 1
    return {"enqueued": count, "skipped_push_active": connections.count() - count}
```

---

## 9. Configuration & Environment Variables

### New Settings

```python
# config/settings/base.py — additions

# Google Calendar API
GOOGLE_CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
]

# Calendar webhook URL (must be publicly reachable)
CALENDAR_WEBHOOK_URL = os.environ.get(
    "CALENDAR_WEBHOOK_URL",
    "https://api.frontiercrm.com/api/sync/calendar/webhook/",
)

# Watch channel defaults
CALENDAR_WATCH_TTL_SECONDS = int(os.environ.get(
    "CALENDAR_WATCH_TTL_SECONDS",
    7 * 24 * 3600,  # 7 days (max allowed)
))

CALENDAR_WATCH_EXPIRY_GRACE_HOURS = int(os.environ.get(
    "CALENDAR_WATCH_EXPIRY_GRACE_HOURS",
    24,  # Renew channels within 24 hours of expiry
))

# CRM-originated event metadata
CRM_EXTENDED_PROPERTIES_PREFIX = "frontiercrm"

# Scope upgrade
CALENDAR_WRITE_SCOPE_REQUIRED = True
```

### .env additions

```env
# Calendar webhook URL (use ngrok URL for local dev)
CALENDAR_WEBHOOK_URL=https://abc123.ngrok.io/api/sync/calendar/webhook/

# Watch channel defaults
CALENDAR_WATCH_TTL_SECONDS=604800
```

### Required Google Cloud Console Configuration

1. **OAuth consent screen** — add `calendar.events` scope
2. **APIs enabled** — Google Calendar API must be enabled (already done for read-only)
3. **Domain verification** — the webhook endpoint domain must match the OAuth redirect URI domain (Google checks this for push notifications)

---

## 10. Implementation Order

| Step | File(s) | What to do | Effort |
|------|---------|-----------|--------|
| 1 | `apps/sync/oauth.py` | Change `CALENDAR_SCOPES` to `calendar.events`. Add scope verification helper. | Trivial |
| 2 | `apps/sync/adapters/base.py` | Add `create_event`, `update_event`, `delete_event` abstract methods to `CalendarSyncAdapter` | Small |
| 3 | `apps/sync/adapters/google_calendar/client.py` | Add `patch()`, `delete()` HTTP methods. Add `_build_event_body()` helper. | Small |
| 4 | `apps/sync/adapters/google_calendar/adapter.py` | Implement `create_event`, `update_event`, `delete_event`. Add `extendedProperties` for CRM tracking. | Medium |
| 5 | `apps/sync/tasks_calendar.py` | Add `push_crm_event_to_calendar` task. | Medium |
| 6 | `apps/activities/signals.py` (new) | Add post-save signal for `Activity.activity_type=MEETING` → enqueue `push_crm_event_to_calendar`. | Small |
| 7 | `apps/sync/views.py`, `serializers.py` | Add `CalendarEventCreateSerializer`, proxy endpoints for event CRUD. | Medium |
| 8 | `apps/sync/models.py` | Add `CalendarWatchChannel` model. Create migration. | Small |
| 9 | `apps/sync/adapters/base.py` | Add `setup_watch()`, `stop_watch()` abstract methods to `CalendarSyncAdapter` | Small |
| 10 | `apps/sync/adapters/google_calendar/adapter.py` | Implement `setup_watch()`, `stop_watch()`. Watch API calls. | Small |
| 11 | `apps/sync/tasks_calendar.py` | Add `setup_calendar_watch_channel`, `renew_calendar_watch_channels`, `remove_calendar_watch_channel` tasks. | Medium |
| 12 | `apps/sync/views.py` (new webhook view) | Add `calendar_webhook_receiver` — public endpoint with Google header verification. | Small |
| 13 | `apps/sync/urls.py` | Wire webhook endpoint (outside router — no auth). | Trivial |
| 14 | `apps/sync/oauth.py` | After successful OAuth callback + initial sync, call `setup_calendar_watch_channel.delay()` | Small |
| 15 | `config/beat_schedule.py` | Add `CALENDAR_WATCH_RENEWAL` schedule. | Trivial |
| 16 | `apps/sync/tasks_calendar.py` (modify) | Modify `sync_all_calendars` to skip connections with active push channels. | Small |
| 17 | `apps/sync/views.py` | Add scope upgrade endpoint + auth status enhancement (push_status). | Small |
| 18 | `config/settings/base.py` | Add new settings. | Trivial |
| 19 | Frontend | Add "Create Calendar Event" button, meeting form, timeline indicators, scope upgrade banner. | Large |
| 20 | Tests | Unit: adapter write methods, webhook receiver, signal handler. Integration: OAuth scope upgrade. E2E: create meeting → appears in Google Calendar | Medium |

### Dependencies

- Steps 1-7 are the **Event Creation** workstream (can be done independently)
- Steps 8-17 are the **Push Notifications** workstream (depends on existing delta sync from Phase 5)
- Step 6 (signals) depends on Steps 2-5 (adapter + tasks must exist)
- Step 14 depends on Step 11 (setup task must exist)
- Step 16 depends on Step 9 (must be able to check push status)
- Step 19 (frontend) can start after Steps 1 + 5 + 7 provide working API endpoints

---

## 11. Acceptance Criteria

### Calendar Event Creation

1. **Scope upgrade:** User can upgrade their calendar sync from read-only to read-write via the scope upgrade endpoint. Existing connections are not disrupted.

2. **Create event:** Creating a meeting via `POST /api/sync/calendar/events/` creates the event on the user's Google Calendar and stores the Google event ID in the Activity's metadata.

3. **Update event:** Updating a CRM-created meeting (title, time, location) via `PUT` propagates the change to Google Calendar.

4. **Delete event:** Deleting a CRM-created meeting via `DELETE` removes it from Google Calendar and soft-deletes (or marks as cancelled) the Activity.

5. **Signal-based push:** Creating an Activity with `activity_type=MEETING` through the standard Activity API automatically triggers push to Google Calendar (no manual API call needed).

6. **No duplicate push:** Google-originated events (`event_source=google`) are never pushed back to Google Calendar.

7. **Extended properties:** CRM-created events have `extendedProperties.private.frontiercrm_*` set so the CRM can identify its own events in subsequent syncs.

8. **Attendee handling:** Attendees specified during event creation are added to the Google Calendar event as invitees.

### Push Notifications

9. **Watch channel setup:** After initial OAuth and full sync, a watch channel is registered for the user's primary calendar.

10. **Push-triggered sync:** Modifying a Google Calendar event triggers a notification to the webhook endpoint, which enqueues a delta sync within seconds.

11. **Webhook verification:** Only known channel IDs trigger a sync. Unknown channel IDs are logged and return 200 without syncing.

12. **Channel renewal:** Watch channels expiring within 24 hours are automatically renewed by the daily renewal task.

13. **Fallback to polling:** If the webhook endpoint is unreachable (dev environment, network issue), the existing 15-minute polling continues to work.

14. **Webhook response time:** The webhook endpoint responds within 5 seconds (Google's timeout is 30 seconds). All heavy work is deferred to Celery.

15. **Disconnection cleanup:** Disconnecting a calendar sync connection stops the watch channel.

### Integration

16. **Frontend indicators:** CRM-created events show "Created in FrontierCRM" in the timeline. Google-synced events show "Synced from Google Calendar".

17. **No data loss:** Creating a meeting in Google Calendar that a CRM-created meeting already exists for does not duplicate the Activity (deduplication handles it).

---

## 12. Appendix: Conflict Resolution Strategies

### Strategy Overview

| Strategy | When | Direction | Action |
|----------|------|-----------|--------|
| Last-write-wins | Default for initial build | Timestamp comparison | Latest `updated` timestamp wins |
| Google side wins | Push notification sync | Google → CRM | After each push sync, Google changes overwrite CRM |
| CRM side wins | CRM-originated event push | CRM → Google | User-initiated changes are authoritative |
| Manual | Future enhancement | N/A | Show diff UI, let user choose |

### Dedup logic for push notification sync

When processing a push-triggered delta sync:

1. Event with `extendedProperties.private.frontiercrm_source = "crm"` and `frontiercrm_activity_id` is found
2. Compare `event.updated` vs `Activity.updated_at`
3. If Google's `updated` is newer → Google changes overwrite CRM (last-write-wins)
4. If CRM's `updated_at` is newer → skip update (CRM change hasn't propagated yet; next push task handles it)

### Conflict logging

All resolution events are logged to `SyncConflict` for audit:

```python
SyncConflict.objects.create(
    connection=connection,
    entity_type="activity",
    entity_id=activity.id,
    external_id=event.provider_id,
    conflict_type="concurrent_edit",
    resolution_strategy="last_write_wins",
    crm_version={"updated_at": activity.updated_at.isoformat()},
    provider_version={"updated": event.updated.isoformat()},
    resolved_by="system",
    resolved_at=timezone.now(),
)
```

---

*End of specification.*
