"""GoogleCalendarAdapter — Google Calendar v3 API implementation of CalendarSyncAdapter.

Provider: 'google_calendar'
Scope: 'https://www.googleapis.com/auth/calendar.events.readonly'
Sync method: events.list with syncToken (delta), falling back to
             timeMin/timeMax (full) when syncToken expires.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from apps.sync.adapters.base import (
    CalendarDeltaResult,
    CalendarEvent,
    CalendarSyncAdapter,
    ConnectionStatus,
    TokenRefreshResult,
)
from apps.sync.adapters.google_calendar.client import (
    CalendarApiError,
    CalendarAuthError,
    CalendarNotFoundError,
    GoogleCalendarApiClient,
)

logger = logging.getLogger(__name__)

MAX_RESULTS_PER_PAGE = 250
MAX_PAGES = 10


class GoogleCalendarAdapter(CalendarSyncAdapter):
    """Google Calendar v3 API implementation of CalendarSyncAdapter.

    Uses syncToken-based delta sync with time-range fallback.
    """

    PROVIDER = "google_calendar"
    REQUIRED_SCOPES = ["https://www.googleapis.com/auth/calendar.events.readonly"]
    DEFAULT_SYNC_WINDOW_DAYS_PAST = 90
    DEFAULT_SYNC_WINDOW_DAYS_FUTURE = 30

    def __init__(self, access_token: str, refresh_token: str | None = None):
        self._client = GoogleCalendarApiClient(access_token=access_token, refresh_token=refresh_token)

    # ── Cursor Management ─────────────────────────────────────────────────

    def get_initial_cursor(self) -> dict:
        """Fetch a starting cursor by doing a time-range query and returning the syncToken."""
        # We need to do a full sync to get the first syncToken
        delta = self._time_range_sync(
            time_min=datetime.now(timezone.utc) - timedelta(days=self.DEFAULT_SYNC_WINDOW_DAYS_PAST),
            time_max=datetime.now(timezone.utc) + timedelta(days=self.DEFAULT_SYNC_WINDOW_DAYS_FUTURE),
        )
        return delta.new_cursor or {"lastSyncTime": datetime.now(timezone.utc).isoformat()}

    # ── Delta Sync ────────────────────────────────────────────────────────

    def get_calendar_delta(self, cursor: dict | None) -> CalendarDeltaResult:
        """Fetch calendar event changes since the given cursor.

        Uses syncToken when available, falls back to time-range sync
        when the token is expired (410 Gone) or cursor is None.
        """
        if cursor is None:
            return self._time_range_sync(
                time_min=datetime.now(timezone.utc) - timedelta(days=self.DEFAULT_SYNC_WINDOW_DAYS_PAST),
                time_max=datetime.now(timezone.utc) + timedelta(days=self.DEFAULT_SYNC_WINDOW_DAYS_FUTURE),
            )

        sync_token = cursor.get("syncToken")
        if sync_token:
            try:
                return self._delta_sync(sync_token)
            except CalendarNotFoundError:
                # syncToken expired (410 Gone) — fall through to time-range
                logger.info("syncToken expired, falling back to time-range sync")
                pass

        # Fallback: time-range sync
        return self._time_range_sync(
            time_min=datetime.now(timezone.utc) - timedelta(days=self.DEFAULT_SYNC_WINDOW_DAYS_PAST),
            time_max=datetime.now(timezone.utc) + timedelta(days=self.DEFAULT_SYNC_WINDOW_DAYS_FUTURE),
        )

    def _delta_sync(self, sync_token: str) -> CalendarDeltaResult:
        """Delta sync using Google Calendar syncToken.

        https://developers.google.com/calendar/api/guides/sync
        """
        all_items: list[CalendarEvent] = []
        all_deleted: list[str] = []
        page_count = 0
        next_sync_token = sync_token
        page_token: str | None = None
        has_more = False

        while True:
            params: dict[str, Any] = {
                "syncToken": sync_token,
                "showDeleted": True,
                "singleEvents": True,
                "maxResults": MAX_RESULTS_PER_PAGE,
            }
            if page_token:
                params["pageToken"] = page_token

            response = self._client.get("calendars/primary/events", params=params)

            # Capture the next sync token
            if "nextSyncToken" in response:
                next_sync_token = response["nextSyncToken"]

            # Process events
            for event_data in response.get("items", []):
                if not event_data.get("id"):
                    continue

                if event_data.get("status") == "cancelled":
                    all_deleted.append(event_data["id"])
                    continue

                event = _parse_google_event(event_data)
                if event:
                    all_items.append(event)

            page_count += 1
            page_token = response.get("nextPageToken")
            if not page_token or page_count >= MAX_PAGES:
                if page_token and page_count >= MAX_PAGES:
                    has_more = True
                break

        return CalendarDeltaResult(
            items=all_items,
            deleted_ids=all_deleted,
            new_cursor={"syncToken": next_sync_token},
            has_more=has_more,
            full_resync_required=False,
        )

    def _time_range_sync(self, time_min: datetime, time_max: datetime) -> CalendarDeltaResult:
        """Full sync using timeMin/timeMax query.

        Fetches events within the specified time window, collecting
        the nextSyncToken from the response for future delta syncs.
        """
        all_items: list[CalendarEvent] = []
        page_count = 0
        next_sync_token = ""
        page_token: str | None = None
        has_more = False

        while True:
            params: dict[str, Any] = {
                "timeMin": time_min.isoformat(),
                "timeMax": time_max.isoformat(),
                "singleEvents": True,
                "showDeleted": True,
                "maxResults": MAX_RESULTS_PER_PAGE,
            }
            if page_token:
                params["pageToken"] = page_token

            response = self._client.get("calendars/primary/events", params=params)

            # Capture the next sync token
            if "nextSyncToken" in response:
                next_sync_token = response["nextSyncToken"]

            # Process events
            for event_data in response.get("items", []):
                if not event_data.get("id"):
                    continue

                if event_data.get("status") == "cancelled":
                    # During full sync, we don't emit deletions for cancelled
                    continue

                event = _parse_google_event(event_data)
                if event:
                    all_items.append(event)

            page_count += 1
            page_token = response.get("nextPageToken")
            if not page_token or page_count >= MAX_PAGES:
                if page_token and page_count >= MAX_PAGES:
                    has_more = True
                break

        cursor = {}
        if next_sync_token:
            cursor["syncToken"] = next_sync_token
        else:
            cursor["lastSyncTime"] = time_max.isoformat()

        return CalendarDeltaResult(
            items=all_items,
            deleted_ids=[],
            new_cursor=cursor,
            has_more=has_more,
            full_resync_required=False,
        )

    # ── Connection Validation ─────────────────────────────────────────────

    def validate_connection(self) -> ConnectionStatus:
        """Test that the OAuth token works and has calendar.events.readonly scope."""
        try:
            # List the primary calendar to test access
            response = self._client.get("calendars/primary")
            return ConnectionStatus(
                is_valid=True,
                account_email=response.get("id", "unknown"),
                scopes=["calendar.events.readonly"],
            )
        except CalendarAuthError:
            return ConnectionStatus(is_valid=False, error="token_expired")
        except Exception as e:
            return ConnectionStatus(is_valid=False, error=str(e))

    def refresh_token(self) -> TokenRefreshResult:
        """Refresh an expired Calendar OAuth token."""
        success = self._client.refresh_access_token()
        if success:
            return TokenRefreshResult(
                success=True,
                access_token=self._client.access_token,
            )
        return TokenRefreshResult(success=False, error="token_refresh_failed")

    # ── Write Methods (Event Creation) ─────────────────────────────────────

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
        body = GoogleCalendarApiClient.build_event_body(
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
        parsed = _parse_google_event(response)
        if parsed is None:
            raise CalendarApiError("Failed to parse created event response")
        return parsed

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
            body["summary"] = summary[:500]
        if description is not None:
            body["description"] = description[:5000]
        if location is not None:
            body["location"] = location
        if start is not None:
            if all_day:
                body["start"] = {"date": start.date().isoformat(), "timeZone": timezone or "UTC"}
            else:
                body["start"] = {"dateTime": start.isoformat(), "timeZone": timezone or "UTC"}
        if end is not None:
            if all_day:
                body["end"] = {"date": end.date().isoformat(), "timeZone": timezone or "UTC"}
            else:
                body["end"] = {"dateTime": end.isoformat(), "timeZone": timezone or "UTC"}
        if attendees is not None:
            body["attendees"] = [
                {"email": a.get("email"), "displayName": a.get("displayName")}
                for a in attendees
                if a.get("email")
            ]
        if recurrence is not None:
            body["recurrence"] = recurrence[:10]

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

    # ── Watch Channel Methods (Push Notifications) ─────────────────────────

    def setup_watch(
        self,
        channel_id: str,
        webhook_url: str,
        ttl_seconds: int = 604800,
    ) -> dict[str, Any]:
        """Register a Google Calendar watch channel for push notifications."""
        body = {
            "id": channel_id,
            "type": "web_hook",
            "address": webhook_url,
            "ttl": ttl_seconds,
        }
        response = self._client.post(
            "calendars/primary/events/watch",
            body=body,
        )
        return response

    def stop_watch(self, channel_id: str, resource_id: str) -> bool:
        """Stop a Google Calendar watch channel."""
        try:
            self._client.post("channels/stop", body={
                "id": channel_id,
                "resourceId": resource_id,
            })
            return True
        except CalendarNotFoundError:
            return False


# ── Helpers ──────────────────────────────────────────────────────────────────


def _parse_google_event(event_data: dict[str, Any]) -> CalendarEvent | None:
    """Parse a Google Calendar v3 event dict into a CalendarEvent dataclass."""
    if not event_data.get("id"):
        return None

    # Parse start/end (support both dateTime and date)
    start = event_data.get("start", {}) or {}
    end = event_data.get("end", {}) or {}
    all_day = "date" in start and "dateTime" not in start

    start_dt = _parse_google_datetime(start)
    end_dt = _parse_google_datetime(end)

    # Determine timezone
    timezone = start.get("timeZone", "UTC") or "UTC"

    # Extract primary user's response status from attendees
    response_status = None

    return CalendarEvent(
        provider_id=event_data["id"],
        calendar_id="primary",
        i_cal_uid=event_data.get("iCalUID"),
        summary=event_data.get("summary", ""),
        description=event_data.get("description"),
        start=start_dt,
        end=end_dt,
        all_day=all_day,
        timezone=timezone,
        location=event_data.get("location"),
        hangout_link=event_data.get("hangoutLink"),
        status=event_data.get("status", "confirmed"),
        recurrence=event_data.get("recurrence", []),
        recurring_event_id=event_data.get("recurringEventId"),
        original_start_time=_parse_google_datetime(event_data.get("originalStartTime")),
        attendees=event_data.get("attendees", []),
        creator=event_data.get("creator"),
        organizer=event_data.get("organizer"),
        created=_parse_google_timestamp(event_data.get("created")),
        updated=_parse_google_timestamp(event_data.get("updated")),
        html_link=event_data.get("htmlLink"),
    )


def _parse_google_datetime(raw: dict[str, str] | None) -> datetime | None:
    """Parse a Google Calendar dateTime or date field."""
    if not raw:
        return None

    if "dateTime" in raw:
        try:
            return datetime.fromisoformat(raw["dateTime"])
        except (ValueError, TypeError):
            return None

    if "date" in raw:
        try:
            return datetime.fromisoformat(raw["date"])
        except (ValueError, TypeError):
            return None

    return None


def _parse_google_timestamp(iso_str: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp string from Google Calendar."""
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str)
    except (ValueError, TypeError):
        return None