# Phase 5: Google Calendar Sync Specification

**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)
**Status:** Draft for review

---

## Table of Contents

1. [ADR-024: Calendar Sync Architecture](#1-adr-024-calendar-sync-architecture)
2. [Data Model](#2-data-model)
3. [CalendarAdapter API Contract](#3-calendaradapter-api-contract)
4. [REST API Contract](#4-rest-api-contract)
5. [OAuth Scope Extension](#5-oauth-scope-extension)
6. [Celery Tasks & Beat Schedule](#6-celery-tasks--beat-schedule)
7. [Implementation Order](#7-implementation-order)
8. [Acceptance Criteria](#8-acceptance-criteria)
9. [Appendix: Event Field Mapping](#9-appendix-event-field-mapping)

---

## 1. ADR-024: Calendar Sync Architecture

**Status:** Proposed
**Date:** 2026-06-30

### Context

FrontierCRM already has:
- `SyncConnection` model with `google_calendar` provider and `SyncState` with `calendar_event` sync type — the records exist but no adapter implements the calendar API
- `Activity` model with `MEETING` activity type — calendar events should land here
- Gmail OAuth flow in `apps/sync/oauth.py` — can be extended for Calendar scope
- `SyncAdapter` abstract base class in `apps/sync/adapters/base.py` — currently email-only; calendar needs different data models and API methods
- Celery Beat infrastructure in `config/beat_schedule.py` — pattern exists for periodic sync

The design must cover: OAuth scope extension, a new CalendarAdapter, event → Activity mapping with deduplication, periodic sync scheduling, contact-by-email matching, and REST endpoints for manual trigger and status.

### Decision

1. **Separate adapter base class.** Create `CalendarSyncAdapter` as a new abstract base in `adapters/base.py`, sibling to `SyncAdapter`, with calendar-specific methods. Do not overload the email `SyncAdapter` — event data (start/end, recurrence, attendees, location) shares nothing with email message data.

2. **New adapter directory.** `apps/sync/adapters/google_calendar/adapter.py` — `GoogleCalendarAdapter` extends `CalendarSyncAdapter`, wraps Google Calendar v3 REST API.

3. **Polling, not push.** Initial sync uses periodic polling (Celery Beat, every 15 minutes by default). Google Calendar push notifications exist (via Google Cloud Pub/Sub and a public webhook) but add deployment complexity — a `PUBSUB_VERIFICATION_TOKEN` env var, a webhook route that must be publicly reachable, and GCP Pub/Sub setup. Polling is simpler to implement and debug. A future ADR can add push notifications on top.

4. **Read-only scope initially.** Use `https://www.googleapis.com/auth/calendar.events.readonly` for the initial build. This allows syncing events but not creating/modifying them through the CRM (bidirectional create/edit is Phase 6). The scope string is additive-free — adding `calendar.events` later requires no re-consent for offline tokens with `prompt=consent`.

5. **No new database columns.** Store all Google Calendar event metadata in `Activity.metadata` JSONField. The `external_event_id` (Google's event ID) and `external_calendar_id` (calendar ID for the source, usually `primary`) are persisted in metadata. Deduplication by event ID is a metadata lookup. No migration required.

6. **Contact linking by email.** During sync, the adapter matches attendees (`attendees[].email`) against `Contact.email` within the same tenant. Matched contact ids are written into `metadata.contact_ids` and `Activity.entity_type="contact"`. Unmatched attendee emails are stored in `metadata.unmatched_attendee_emails`.

7. **90-day sync window.** Sync events from 90 days in the past to 30 days in the future. This covers past meetings that may still be relevant context and upcoming meetings visible on the timeline.

### Rejected Alternatives

1. **Extend `SyncAdapter` with optional calendar methods** — rejected. The `SyncAdapter` interface (`get_email_delta`, `send_email`, `mark_read`, `get_initial_cursor`) has nothing in common with calendar event APIs. A separate base class keeps the contract clean.

2. **Google Calendar push/webhook notifications for initial build** — rejected for simplicity (see Decision #3). Revisit for Phase 6 or when a tenant exceeds 10k events.

3. **Store calendar event IDs in a dedicated model** — rejected. A `CalendarEvent` model would be redundant with `Activity` (already has `type=meeting`). The metadata JSONField is sufficient for the initial build. Revisit with an `ExternalEventMap` model if sync volume exceeds 100k events per tenant.

4. **Full bidirectional sync (create/update events from CRM)** — rejected for this phase. Read-only sync is the P2 requirement. Write-back requires conflict resolution and additional Google Calendar API scopes.

5. **Separate OAuth flow for calendar** — rejected. Extend the existing Gmail OAuth flow to request the calendar scope in the same authorization request. Users connect once for both email and calendar.

---

## 2. Data Model

**No new database tables.** All changes are conventions enforced by the adapter code, not schema migrations.

### SyncConnection usage

Existing `SyncConnection` with `provider="google_calendar"`:

| Field | Value | Notes |
|-------|-------|-------|
| `provider` | `"google_calendar"` | Already in `PROVIDER_CHOICES` |
| `scopes` | `["https://www.googleapis.com/auth/calendar.events.readonly"]` | Stores the granted scope |
| `provider_account` | Google account email | Same email as Gmail connection |

### SyncState usage

Existing `SyncState` with `sync_type="calendar_event"`:

| Field | Value | Notes |
|-------|-------|-------|
| `sync_type` | `"calendar_event"` | Already in `SYNC_TYPE_CHOICES` |
| `provider` | `"google_calendar"` | |
| `cursor_data` | `{"nextSyncToken": "..."}` or `{"lastEventTime": "...ISO-8601..."}` | Sync token from Google Calendar API |

Two cursor strategies (ordered by preference):
1. **syncToken** — returned by Google Calendar API when using `showDeleted=true` and `singleEvents=true`. Terse, efficient; expires after ~7 days of inactivity, after which a full resync with a time range is required.
2. **timeRange fallback** — when `syncToken` expires, fall back to `timeMin` + `timeMax` queries (90-day window) and set `cursor_data` to the last successful poll time.

### Activity metadata convention (for `activity_type="meeting"`)

```json
{
  "external_event_id": "abc123def456_google_event_id",
  "external_calendar_id": "primary",
  "ical_uid": "event-uuid@google.com",
  "start": "2026-07-01T14:00:00+00:00",
  "end": "2026-07-01T15:00:00+00:00",
  "all_day": false,
  "timezone": "America/New_York",
  "location": "Conference Room B",
  "hangout_link": "https://meet.google.com/abc-defg-hij",
  "status": "confirmed",
  "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO"],
  "original_start": "2026-07-01T14:00:00+00:00",
  "contact_ids": ["uuid1", "uuid2"],
  "unmatched_attendee_emails": ["vendor@external.com"],
  "event_creator": "user@company.com",
  "event_organizer": "user@company.com",
  "response_status": "accepted"
}
```

Fields `external_event_id`, `start`, `end`, and `status` are required for every synced event. All others are optional.

### Activity model fields used

| Activity field | Source | Notes |
|----------------|--------|-------|
| `activity_type` | Constant | `Activity.ActivityType.MEETING` |
| `title` | `event.summary` | Truncated to 500 chars |
| `description` | `event.description` | Truncated to 5000 chars |
| `entity_type` | `"contact"` or `""` | `"contact"` when at least one attendee matched a CRM contact |
| `entity_id` | First matched contact | UUID of the first matched contact |
| `metadata` | See above | JSON object with all event fields |
| `actor_id` | `user.id` | The user who owns the sync connection |
| `duration_minutes` | Computed from start/end | Integer, null for all-day events |

---

## 3. CalendarAdapter API Contract

### Abstract base: `CalendarSyncAdapter`

New class in `apps/sync/adapters/base.py`.

```python
@dataclass
class CalendarEvent:
    """Normalized calendar event from any provider."""
    provider_id: str          # Google Calendar event ID
    calendar_id: str          # Usually "primary"
    i_cal_uid: str | None
    summary: str
    description: str | None
    start: datetime | None    # Start datetime (or date for all-day)
    end: datetime | None      # End datetime
    all_day: bool = False
    timezone: str = "UTC"
    location: str | None = None
    hangout_link: str | None = None
    status: str = "confirmed"  # confirmed, tentative, cancelled
    recurrence: list[str] = field(default_factory=list)
    recurring_event_id: str | None = None  # If this is a single occurrence of a recurring event
    original_start_time: datetime | None = None
    attendees: list[dict] = field(default_factory=list)
    # Each attendee: {"email": str, "displayName": str | None, "responseStatus": str}
    creator: dict | None = None       # {"email": str, "displayName": str | None}
    organizer: dict | None = None     # {"email": str, "displayName": str | None}
    created: datetime | None = None
    updated: datetime | None = None
    html_link: str | None = None      # Link to open event in Google Calendar UI


@dataclass
class CalendarDeltaResult:
    """Result of a calendar delta sync operation."""
    items: list[CalendarEvent] = field(default_factory=list)
    deleted_ids: list[str] = field(default_factory=list)
    new_cursor: dict[str, Any] = field(default_factory=dict)
    has_more: bool = False
    full_resync_required: bool = False


class CalendarSyncAdapter(ABC):
    """Abstract interface for calendar sync providers."""

    PROVIDER = ""
    REQUIRED_SCOPES: list[str] = []

    @abstractmethod
    def get_calendar_delta(self, cursor: dict | None) -> CalendarDeltaResult:
        """Fetch calendar event changes since the given cursor.
        
        When cursor is None or expired, triggers a full sync within
        the default time window (last 90 days to next 30 days).
        """
        ...

    @abstractmethod
    def get_initial_cursor(self) -> dict:
        """Fetch the starting cursor for delta sync (syncToken or time)."""
        ...

    @abstractmethod
    def validate_connection(self) -> ConnectionStatus:
        """Test that the OAuth token works and has calendar.events.readonly scope."""
        ...

    @abstractmethod
    def refresh_token(self) -> TokenRefreshResult:
        """Refresh an expired OAuth token."""
        ...
```

### GoogleCalendarAdapter

New module: `apps/sync/adapters/google_calendar/adapter.py`

```
adapter/
  __init__.py
  adapter.py     ← GoogleCalendarAdapter
  client.py      ← GoogleCalendarApiClient (wraps REST API calls + auth)
```

```python
class GoogleCalendarAdapter(CalendarSyncAdapter):
    """Google Calendar v3 API implementation of CalendarSyncAdapter.

    Provider: 'google_calendar'
    Scope: 'https://www.googleapis.com/auth/calendar.events.readonly'
    Sync method: events.list with syncToken (delta), falling back to
                 timeMin/timeMax (full) when syncToken expires.
    """

    PROVIDER = "google_calendar"
    REQUIRED_SCOPES = ["https://www.googleapis.com/auth/calendar.events.readonly"]
    DEFAULT_SYNC_WINDOW_DAYS_PAST = 90
    DEFAULT_SYNC_WINDOW_DAYS_FUTURE = 30
    MAX_RESULTS_PER_PAGE = 250  # Google max is 2500; 250 is sensible

    def __init__(self, access_token: str, refresh_token: str | None = None):
        self._client = GoogleCalendarApiClient(access_token, refresh_token)
```

#### `GoogleCalendarApiClient`

```
GoogleCalendarApiClient
├── __init__(access_token, refresh_token)
├── get_events(params: dict) -> dict
│   Calls: GET /calendar/v3/calendars/{calendarId}/events
│   Handles: 401 → refresh token, retry
│   Returns: parsed JSON response
├── get_event(event_id: str, calendar_id: str = "primary") -> dict | None
│   Calls: GET /calendar/v3/calendars/{calendarId}/events/{eventId}
├── build_headers() -> dict
│   Sets: Authorization: Bearer {access_token}
└── _refresh_if_needed() -> bool
    Same pattern as GmailApiClient._refresh_if_needed
```

#### Sync algorithm (in `GoogleCalendarAdapter.get_calendar_delta`)

1. **Input:** `cursor dict` with either `{"syncToken": "..."}` or `{"lastSyncTime": "...ISO-8601..."}` or `None`

2. **If cursor has `syncToken`:**
   - `params = {"syncToken": token, "showDeleted": True, "singleEvents": True, "maxResults": MAX_RESULTS_PER_PAGE}`
   - If response includes `nextSyncToken`, update cursor for next poll
   - If response is 410 (Gone — token expired), fall through to time-range sync

3. **If cursor is None or token expired:**
   - `timeMin = now - 90 days`, `timeMax = now + 30 days`
   - `params = {"timeMin": timeMin.isoformat(), "timeMax": timeMax.isoformat(), "singleEvents": True, "showDeleted": True, "maxResults": MAX_RESULTS_PER_PAGE}`
   - Collect all pages, return items
   - Returned `new_cursor` contains the `nextSyncToken` from the response (so subsequent polls are delta)

4. **Pagination:** Follow `nextPageToken` in a loop up to 10 pages (2500 events max per sync). If there are more pages after 10, set `has_more=True`.

5. **Parse events:** Convert each Google event dict → `CalendarEvent` dataclass. Filter out:
   - Events without `id` (shouldn't happen)
   - Events with `status="cancelled"` — these go into `deleted_ids` for removal from CRM
   - Recurring events: when `recurrence` is present, keep the master event. `singleEvents=True` already expands recurring events into individual instances.

---

## 4. REST API Contract

### Existing endpoint reuse

The existing `SyncConnectionViewSet` at `/api/sync/connections/` already has the pattern we need. Calendar sync extends this viewset with two new actions.

| Endpoint | Method | Existing | New |
|----------|--------|----------|-----|
| `/api/sync/connections/` | GET | List connections | Same, includes `google_calendar` providers |
| `/api/sync/connections/{id}/sync/` | POST | Trigger email sync | Extend to also trigger calendar sync when provider is `google_calendar` |
| `/api/sync/states/` | GET | List sync states | Same, includes `calendar_event` sync types |

### New: Calendar OAuth URL

```
POST /api/sync/connections/calendar/auth-url/
```

Request body: None

Response 200:
```json
{
  "url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "random-state-token"
}
```

Same pattern as `gmail/auth-url/` but requests `calendar.events.readonly` scope.

### New: Calendar OAuth callback

```
POST /api/sync/connections/calendar/callback/
```

Request body:
```json
{
  "code": "authorization-code-from-google",
  "state": "state-token-from-auth-url"
}
```

Response 201:
```json
{
  "id": "connection-uuid",
  "provider": "google_calendar",
  "email": "user@example.com",
  "status": "syncing"
}
```

### New: Calendar auth status

```
GET /api/sync/connections/calendar/auth-status/
```

Response 200:
```json
{
  "connected": true,
  "email": "user@example.com",
  "last_sync_at": "2026-07-01T10:00:00Z",
  "last_sync_success": true,
  "sync_state": "complete",
  "events_count": 142
}
```

`events_count` is the `total_synced_count` from the `SyncState` with `sync_type="calendar_event"`.

### Extend: Manual calendar sync

```
POST /api/sync/connections/{id}/sync/
```

When `connection.provider == "google_calendar"`, this triggers `sync_calendar_delta` instead of `sync_email_delta`.

**No new endpoint needed** — the existing `sync` action on the viewset already dispatches to the right celery task based on `connection.provider`.

---

## 5. OAuth Scope Extension

### Current state

Gmail OAuth (`apps/sync/oauth.py::generate_oauth_url`) requests:
```
scope = ["https://www.googleapis.com/auth/gmail.modify"]
```

### New: Calendar OAuth flow

Create a new function or extend `generate_oauth_url`:

```python
# In apps/sync/oauth.py

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events.readonly"]


def generate_calendar_oauth_url() -> dict[str, Any]:
    """Generate a Google Calendar OAuth URL with a state token."""
    state = secrets.token_urlsafe(32)
    client_id = _get_client_id()
    redirect_uri = _get_calendar_redirect_uri()

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(CALENDAR_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "include_granted_scopes": "true",
    }

    url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    _store_state(state)
    return {"url": url, "state": state}
```

Key difference from Gmail OAuth: `include_granted_scopes=true` — when a user already has a Gmail token, re-authorizing adds the calendar scope without losing the existing Gmail scope.

### Token storage

Calendar tokens are stored on a `SyncConnection` record with `provider="google_calendar"`. This is intentionally separate from the Gmail connection — the user may want calendar sync without email sync, or active email sync with a different account. The same refresh token endpoint (`accounts.google.com/o/oauth2/token`) is used.

### Redirect URI

`config/settings/base.py` gets a new setting:

```python
CALENDAR_REDIRECT_URI = os.environ.get(
    "CALENDAR_REDIRECT_URI",
    "http://localhost:8000/api/sync/connections/calendar/callback/",
)
```

Or reuse the existing `GOOGLE_OAUTH_REDIRECT_URI` and route on the server side.

**Recommendation:** Use the same redirect URI as Gmail (`GOOGLE_OAUTH_REDIRECT_URI`) and differentiate callbacks by `state` prefix or an API path suffix. This saves adding an extra Google Cloud Console redirect URI.

---

## 6. Celery Tasks & Beat Schedule

### Task: `sync_calendar_delta`

New file: `apps/sync/tasks_calendar.py` (or add to existing `apps/sync/tasks.py`)

```python
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
```

Follows the same pattern as `sync_email_delta`:
1. Look up `SyncConnection(id=connection_id, provider="google_calendar")`
2. Check connection status (skip if expired/disconnected)
3. Create `GoogleCalendarAdapter` from encrypted tokens
4. Refresh tokens if needed
5. Get or create `SyncState(sync_type="calendar_event")`
6. Call `adapter.get_calendar_delta(cursor)`
7. Process each event → create Activity (with dedup by `metadata.external_event_id`)
8. Process deleted_ids → soft-delete matching Activities
9. Update cursor, SyncState, SyncConnection
10. Use `SyncLock` for concurrency control

### Task: `sync_all_calendar`

```python
@shared_task(bind=True)
def sync_all_calendars(self) -> dict[str, Any]:
    """Iterate all active google_calendar connections and enqueue delta sync."""
    connections = SyncConnection.objects.filter(
        is_active=True,
        provider="google_calendar",
        status="active",
    )
    count = 0
    for conn in connections:
        sync_calendar_delta.delay(connection_id=str(conn.id))
        count += 1
    return {"enqueued": count}
```

### Event → Activity mapping (dedup helper)

```python
def _sync_event_to_activity(
    connection: SyncConnection,
    event: CalendarEvent,
    tenant_id: str,
    user_id: str,
) -> Activity | None:
    """Convert a CalendarEvent to an Activity record, deduplicating by event ID."""

    # Check for existing activity with this external_event_id
    existing = Activity.objects.filter(
        tenant_id=tenant_id,
        activity_type=Activity.ActivityType.MEETING,
        metadata__external_event_id=event.provider_id,
    ).first()
    if existing:
        return existing  # Already synced (or updated in place)

    # Build metadata JSON
    metadata = build_event_metadata(event)

    # Contact linking
    contact_ids = _match_attendees_to_contacts(tenant_id, event.attendees)
    metadata["contact_ids"] = contact_ids
    metadata["unmatched_attendee_emails"] = [
        a["email"] for a in event.attendees
        if a["email"] not in {c.email for c in Contact.objects.filter(
            tenant_id=tenant_id, email__in=[a["email"] for a in event.attendees]
        )}
    ]

    # Only set entity_type/entity_id if we matched a contact
    entity_type = "contact" if contact_ids else ""
    entity_id = contact_ids[0] if contact_ids else None

    return Activity.objects.create(
        tenant_id=tenant_id,
        activity_type=Activity.ActivityType.MEETING,
        title=event.summary[:500] if event.summary else "(No title)",
        description=(event.description or "")[:5000],
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata,
        actor_id=user_id,
        duration_minutes=_compute_duration_minutes(event),
    )
```

### Beat schedule addition

In `config/beat_schedule.py`:

```python
from datetime import timedelta

# ── Calendar Sync ─────────────────────────────────────────────────────────────
# Sync Google Calendar events for all connected users.
# 15-minute interval balances freshness with Google API quota.
CALENDAR_SYNC_SCHEDULE = {
    "sync-all-calendars": {
        "task": "apps.sync.tasks_calendar.sync_all_calendars",
        "schedule": timedelta(minutes=15),
        "options": {"expires": 300},  # Drop if previous run still active
    },
}

# ── Combined schedule (add to existing) ───────────────────────────────────────
BEAT_SCHEDULE.update(CALENDAR_SYNC_SCHEDULE)
```

---

## 7. Implementation Order

| Step | File(s) | What to do | Effort |
|------|---------|-----------|--------|
| 1 | `apps/sync/adapters/base.py` | Add `CalendarEvent`, `CalendarDeltaResult`, `CalendarSyncAdapter` abstract base | Small |
| 2 | `apps/sync/oauth.py` | Add `generate_calendar_oauth_url()`, `handle_calendar_oauth_callback()` | Small |
| 3 | `apps/sync/adapters/google_calendar/client.py` | New module: `GoogleCalendarApiClient` with auth, GET events, error handling (same pattern as `GmailApiClient`) | Medium |
| 4 | `apps/sync/adapters/google_calendar/adapter.py` | New module: `GoogleCalendarAdapter` implementing `get_calendar_delta`, sync token management, time-range fallback | Medium |
| 5 | `apps/sync/tasks_calendar.py` | New module: `sync_calendar_delta`, `sync_all_calendars` tasks with dedup, contact linking, Activity creation | Large |
| 6 | `apps/sync/views.py` | Add `calendar_auth_url`, `calendar_callback`, `calendar_auth_status` actions on `SyncConnectionViewSet` | Small |
| 7 | `apps/sync/oauth.py` (update) | Update `_get_user_email` to optionally fetch from Calendar API profile (or reuse Gmail's — Gmail API profile already returns email) | Trivial |
| 8 | `config/beat_schedule.py` | Add `CALENDAR_SYNC_SCHEDULE` | Trivial |
| 9 | `apps/sync/urls.py` | Wire new endpoints (if needed — existing router picks up viewset actions automatically) | Trivial |
| 10 | Tests | Unit tests for adapter, integration tests for OAuth callback, task tests with mocked Google Calendar API | Medium |

### Dependencies

- Steps 2 depends on Step 1 (CalendarSyncAdapter contract)
- Steps 5 depends on Steps 3+4 (adapter must work)
- Steps 6 depends on Step 2 (OAuth flow must work)
- Steps 8-9 can be done at any time

---

## 8. Acceptance Criteria

1. **OAuth flow:** User can initiate Google Calendar OAuth from the CRM, granting `calendar.events.readonly` scope. The callback creates a `SyncConnection` with `provider="google_calendar"` and a `SyncState` with `sync_type="calendar_event"`.

2. **Full sync:** After initial authorization, a full sync runs automatically, fetching up to 90 days of past events and 30 days of future events. Events appear as `Activity` records with `type="meeting"`.

3. **Delta sync:** Subsequent syncs (Celery Beat every 15 min) use the syncToken from Google Calendar API and only process changes. Events that were deleted in Google Calendar are soft-deleted in the CRM.

4. **Deduplication:** Running the sync twice with no changes produces zero new activities. The same event ID never creates a duplicate Activity.

5. **Contact linking:** An event with `attendees[].email = "alice@company.com"` where `Contact.email = "alice@company.com"` exists within the same tenant is linked via `metadata.contact_ids` and `entity_type="contact"`.

6. **Unmatched attendees:** An event with attendees whose emails don't match any CRM contact stores those emails in `metadata.unmatched_attendee_emails` and sets `entity_type=""`.

7. **Error handling:** A failed sync updates `SyncConnection.error_count` and doesn't block subsequent syncs. After 5 consecutive failures, the connection is marked `status="error"`.

8. **Manual trigger:** `POST /api/sync/connections/{id}/sync/` on a `google_calendar` connection triggers `sync_calendar_delta`.

9. **Auth status:** `GET /api/sync/connections/calendar/auth-status/` returns whether calendar is connected, last sync time, and event count.

10. **No schema migrations:** All new data goes into existing models (SyncConnection, SyncState, Activity) and JSON metadata fields.

---

## 9. Appendix: Event Field Mapping

### Google Calendar API v3 → CalendarEvent → Activity

| Google Calendar field | `CalendarEvent` field | `Activity` field | Notes |
|----------------------|----------------------|-----------------|-------|
| `id` | `provider_id` | `metadata.external_event_id` | Primary dedup key |
| `iCalUID` | `i_cal_uid` | `metadata.ical_uid` | Stable across moves |
| `summary` | `summary` | `title` | Truncated to 500 chars |
| `description` | `description` | `description` | Truncated to 5000 chars |
| `start.dateTime` + `start.timeZone` | `start`, `timezone` | `metadata.start` | ISO-8601 |
| `end.dateTime` + `end.timeZone` | `end` | `metadata.end` | ISO-8601 |
| `start.date` (all-day) | `start`, `all_day=True` | `metadata.start`, `metadata.all_day=true` | Date string |
| `location` | `location` | `metadata.location` | |
| `hangoutLink` | `hangout_link` | `metadata.hangout_link` | Google Meet |
| `status` | `status` | `metadata.status` | confirmed/tentative/cancelled |
| `recurrence` | `recurrence[]` | `metadata.recurrence` | RRULE strings |
| `recurringEventId` | `recurring_event_id` | — | For single instance of recurring |
| `originalStartTime` | `original_start_time` | `metadata.original_start` | For recurring exceptions |
| `attendees[].email` | `attendees[].email` | `metadata.contact_ids` / `unmatched_attendee_emails` | Contact linking |
| `attendees[].responseStatus` | `attendees[].responseStatus` | `metadata.response_status` | Primary user's response |
| `creator.email` | `creator.email` | `metadata.event_creator` | |
| `organizer.email` | `organizer.email` | `metadata.event_organizer` | |
| `htmlLink` | `html_link` | — | URL to open in Google Calendar |
| `created` | `created` | — | Not stored in CRM |
| `updated` | `updated` | — | Not stored in CRM |
| — | — | `duration_minutes` | Computed from start/end |
| — | — | `actor_id` | Connection user ID |
| — | — | `activity_type` | Always `"meeting"` |

### Google Calendar API rate limits

| Limit | Quota | Mitigation |
|-------|-------|------------|
| Queries per day | 1,000,000 (free tier) | 15-min poll = 96 queries/day per user. 10,000 users = 960k/day. Monitor in production. |
| Queries per 100 seconds per user | 100 | Rate-limit task to 5/min via Celery rate_limit |
| Events per page | 2500 max | Use `maxResults=250` for balanced pagination |
| syncToken lifetime | ~7 days stale | Fall back to time-range full sync on 410 GONE |
| Calendar list queries | Heavier quota | Only query `calendars/{id}` for primary calendar. Revisit for multi-calendar support. |

---

*End of specification.*