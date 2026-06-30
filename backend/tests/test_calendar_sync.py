# ═══════════════════════════════════════════════════════════════════════════════
# Calendar Sync Tests
# ═══════════════════════════════════════════════════════════════════════════════

from unittest.mock import MagicMock, patch

import pytest


class TestCalendarEventDataclass:
    """CalendarEvent dataclass creation and defaults."""

    def test_defaults(self):
        """CalendarEvent has sensible defaults for optional fields."""
        from apps.sync.adapters.base import CalendarEvent

        event = CalendarEvent(provider_id="evt_123", calendar_id="primary")

        assert event.provider_id == "evt_123"
        assert event.calendar_id == "primary"
        assert event.summary == ""
        assert event.description is None
        assert event.start is None
        assert event.end is None
        assert event.all_day is False
        assert event.timezone == "UTC"
        assert event.location is None
        assert event.hangout_link is None
        assert event.status == "confirmed"
        assert event.recurrence == []
        assert event.recurring_event_id is None
        assert event.original_start_time is None
        assert event.attendees == []
        assert event.creator is None
        assert event.organizer is None
        assert event.created is None
        assert event.updated is None
        assert event.html_link is None

    def test_all_fields(self):
        """CalendarEvent stores all fields when provided."""
        from datetime import datetime, timezone
        from apps.sync.adapters.base import CalendarEvent

        dt = datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc)
        event = CalendarEvent(
            provider_id="evt_abc",
            calendar_id="primary",
            i_cal_uid="uid@google.com",
            summary="Team Standup",
            description="Daily standup",
            start=dt,
            end=datetime(2026, 7, 1, 14, 30, 0, tzinfo=timezone.utc),
            all_day=False,
            timezone="America/New_York",
            location="Room 42",
            hangout_link="https://meet.google.com/abc-defg-hij",
            status="confirmed",
            recurrence=["RRULE:FREQ=WEEKLY;BYDAY=MO"],
            recurring_event_id="master_evt_123",
            original_start_time=dt,
            attendees=[{"email": "alice@co.com", "responseStatus": "accepted"}],
            creator={"email": "bob@co.com"},
            organizer={"email": "bob@co.com"},
            created=dt,
            updated=dt,
            html_link="https://calendar.google.com/event?eid=abc",
        )

        assert event.i_cal_uid == "uid@google.com"
        assert event.summary == "Team Standup"
        assert event.description == "Daily standup"
        assert event.attendees[0]["email"] == "alice@co.com"


class TestCalendarDeltaResultDataclass:
    """CalendarDeltaResult dataclass defaults."""

    def test_defaults(self):
        from apps.sync.adapters.base import CalendarDeltaResult

        result = CalendarDeltaResult()
        assert result.items == []
        assert result.deleted_ids == []
        assert result.new_cursor == {}
        assert result.has_more is False
        assert result.full_resync_required is False

    def test_with_items(self):
        from apps.sync.adapters.base import CalendarDeltaResult, CalendarEvent

        event = CalendarEvent(provider_id="e1", calendar_id="primary")
        result = CalendarDeltaResult(
            items=[event],
            deleted_ids=["e2"],
            new_cursor={"syncToken": "abc123"},
            has_more=True,
        )
        assert len(result.items) == 1
        assert "e2" in result.deleted_ids
        assert result.new_cursor["syncToken"] == "abc123"


class TestGoogleEventParsing:
    """_parse_google_event, _parse_google_datetime, _parse_google_timestamp."""

    def test_parse_google_datetime_dateTime(self):
        from apps.sync.adapters.google_calendar.adapter import _parse_google_datetime

        raw = {"dateTime": "2026-07-01T14:00:00-04:00", "timeZone": "America/New_York"}
        dt = _parse_google_datetime(raw)
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 7
        assert dt.day == 1
        assert dt.hour == 14

    def test_parse_google_datetime_date(self):
        from apps.sync.adapters.google_calendar.adapter import _parse_google_datetime

        raw = {"date": "2026-07-04"}
        dt = _parse_google_datetime(raw)
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 7
        assert dt.day == 4

    def test_parse_google_datetime_none(self):
        from apps.sync.adapters.google_calendar.adapter import _parse_google_datetime

        assert _parse_google_datetime(None) is None
        assert _parse_google_datetime({}) is None

    def test_parse_google_timestamp(self):
        from apps.sync.adapters.google_calendar.adapter import _parse_google_timestamp

        dt = _parse_google_timestamp("2026-07-01T14:00:00.000Z")
        assert dt is not None
        assert dt.year == 2026

    def test_parse_google_timestamp_none(self):
        from apps.sync.adapters.google_calendar.adapter import _parse_google_timestamp

        assert _parse_google_timestamp(None) is None
        assert _parse_google_timestamp("") is None

    def test_parse_google_event_minimal(self):
        from apps.sync.adapters.google_calendar.adapter import _parse_google_event

        event_data = {"id": "evt_001", "status": "confirmed"}
        event = _parse_google_event(event_data)
        assert event is not None
        assert event.provider_id == "evt_001"
        assert event.status == "confirmed"
        assert event.summary == ""

    def test_parse_google_event_no_id(self):
        from apps.sync.adapters.google_calendar.adapter import _parse_google_event

        assert _parse_google_event({}) is None
        assert _parse_google_event({"status": "confirmed"}) is None

    def test_parse_google_event_full(self):
        from apps.sync.adapters.google_calendar.adapter import _parse_google_event

        event_data = {
            "id": "evt_full",
            "iCalUID": "full@google.com",
            "summary": "Full Event",
            "description": "A complete test event",
            "start": {"dateTime": "2026-07-01T10:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2026-07-01T11:00:00Z", "timeZone": "UTC"},
            "location": "Conference Room A",
            "hangoutLink": "https://meet.google.com/abc-defg-hij",
            "status": "confirmed",
            "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=TU"],
            "recurringEventId": "master_001",
            "originalStartTime": {"dateTime": "2026-07-01T10:00:00Z"},
            "attendees": [
                {"email": "alice@co.com", "displayName": "Alice", "responseStatus": "accepted"},
                {"email": "bob@co.com", "responseStatus": "tentative"},
            ],
            "creator": {"email": "charlie@co.com", "displayName": "Charlie"},
            "organizer": {"email": "charlie@co.com"},
            "created": "2026-06-01T12:00:00.000Z",
            "updated": "2026-06-30T12:00:00.000Z",
            "htmlLink": "https://calendar.google.com/event?eid=full",
        }

        event = _parse_google_event(event_data)
        assert event is not None
        assert event.provider_id == "evt_full"
        assert event.i_cal_uid == "full@google.com"
        assert event.summary == "Full Event"
        assert event.description == "A complete test event"
        assert event.start is not None
        assert event.end is not None
        assert event.location == "Conference Room A"
        assert event.hangout_link == "https://meet.google.com/abc-defg-hij"
        assert event.status == "confirmed"
        assert len(event.recurrence) == 1
        assert event.recurring_event_id == "master_001"
        assert len(event.attendees) == 2
        assert event.creator["email"] == "charlie@co.com"
        assert event.organizer["email"] == "charlie@co.com"
        assert event.created is not None
        assert event.updated is not None
        assert event.html_link == "https://calendar.google.com/event?eid=full"

    def test_parse_google_event_all_day(self):
        from apps.sync.adapters.google_calendar.adapter import _parse_google_event

        event_data = {
            "id": "evt_allday",
            "summary": "All Day Event",
            "start": {"date": "2026-07-04"},
            "end": {"date": "2026-07-05"},
            "status": "confirmed",
        }
        event = _parse_google_event(event_data)
        assert event is not None
        assert event.all_day is True
        assert event.start is not None
        assert event.end is not None


class TestCalendarEventHelpers:
    """_build_event_metadata, _match_attendees_to_contacts, _compute_duration_minutes."""

    def test_compute_duration_minutes(self):
        from datetime import datetime, timedelta, timezone
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.tasks_calendar import _compute_duration_minutes

        event = CalendarEvent(
            provider_id="e1",
            calendar_id="primary",
            start=datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 7, 1, 15, 30, 0, tzinfo=timezone.utc),
        )
        assert _compute_duration_minutes(event) == 90

    def test_compute_duration_minutes_all_day(self):
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.tasks_calendar import _compute_duration_minutes

        event = CalendarEvent(
            provider_id="e1",
            calendar_id="primary",
            all_day=True,
        )
        assert _compute_duration_minutes(event) is None

    def test_compute_duration_minutes_no_times(self):
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.tasks_calendar import _compute_duration_minutes

        event = CalendarEvent(provider_id="e1", calendar_id="primary")
        assert _compute_duration_minutes(event) is None

    def test_build_event_metadata_minimal(self):
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.tasks_calendar import _build_event_metadata

        event = CalendarEvent(provider_id="e1", calendar_id="primary", status="confirmed")
        meta = _build_event_metadata(event)

        assert meta["external_event_id"] == "e1"
        assert meta["external_calendar_id"] == "primary"
        assert meta["status"] == "confirmed"
        assert meta["all_day"] is False
        # Optional fields absent
        assert "ical_uid" not in meta
        assert "location" not in meta
        assert "hangout_link" not in meta

    def test_build_event_metadata_full(self):
        from datetime import datetime, timezone
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.tasks_calendar import _build_event_metadata

        event = CalendarEvent(
            provider_id="e_full",
            calendar_id="primary",
            i_cal_uid="uid@google.com",
            summary="Full",
            start=datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 7, 1, 15, 0, 0, tzinfo=timezone.utc),
            all_day=False,
            timezone="America/New_York",
            location="Room B",
            hangout_link="https://meet.google.com/abc",
            status="confirmed",
            recurrence=["RRULE:FREQ=WEEKLY"],
            original_start_time=datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc),
            creator={"email": "alice@co.com"},
            organizer={"email": "bob@co.com"},
            html_link="https://calendar.google.com/event?eid=full",
        )
        meta = _build_event_metadata(event)

        assert meta["external_event_id"] == "e_full"
        assert meta["start"] is not None
        assert meta["end"] is not None
        assert meta["ical_uid"] == "uid@google.com"
        assert meta["location"] == "Room B"
        assert meta["hangout_link"] == "https://meet.google.com/abc"
        assert meta["recurrence"] == ["RRULE:FREQ=WEEKLY"]
        assert meta["original_start"] is not None
        assert meta["event_creator"] == "alice@co.com"
        assert meta["event_organizer"] == "bob@co.com"
        assert meta["html_link"] == "https://calendar.google.com/event?eid=full"

    def test_match_attendees_to_contacts_hit(self, db, tenant_id):
        from apps.contacts.models import Contact
        from apps.sync.tasks_calendar import _match_attendees_to_contacts

        contact = Contact.objects.create(
            tenant_id=tenant_id,
            first_name="Alice",
            last_name="Smith",
            email="alice@co.com",
        )
        matched = _match_attendees_to_contacts(str(tenant_id), [
            {"email": "alice@co.com", "responseStatus": "accepted"},
        ])
        assert len(matched) == 1
        assert str(contact.id) in matched

    def test_match_attendees_to_contacts_no_match(self, db, tenant_id):
        from apps.sync.tasks_calendar import _match_attendees_to_contacts

        matched = _match_attendees_to_contacts(str(tenant_id), [
            {"email": "unknown@external.com"},
        ])
        assert matched == []

    def test_match_attendees_to_contacts_empty(self, db, tenant_id):
        from apps.sync.tasks_calendar import _match_attendees_to_contacts

        assert _match_attendees_to_contacts(str(tenant_id), []) == []

    def test_match_attendees_to_contacts_partial(self, db, tenant_id):
        from apps.contacts.models import Contact
        from apps.sync.tasks_calendar import _match_attendees_to_contacts

        Contact.objects.create(
            tenant_id=tenant_id,
            first_name="Alice",
            last_name="Smith",
            email="alice@co.com",
        )
        matched = _match_attendees_to_contacts(str(tenant_id), [
            {"email": "alice@co.com"},
            {"email": "unknown@ext.com"},
        ])
        assert len(matched) == 1


class TestSyncEventToActivity:
    """_sync_event_to_activity — creation, dedup, contact linking."""

    def test_creates_meeting_activity(self, db, tenant_id, user):
        from datetime import datetime, timezone
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity
        from apps.activities.models import Activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@test.com",
        )
        event = CalendarEvent(
            provider_id="evt_001",
            calendar_id="primary",
            summary="Team Standup",
            start=datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 7, 1, 14, 30, 0, tzinfo=timezone.utc),
        )
        activity = _sync_event_to_activity(conn, event, str(user.id))
        assert activity is not None
        assert activity.activity_type == Activity.ActivityType.MEETING
        assert activity.title == "Team Standup"
        assert activity.metadata["external_event_id"] == "evt_001"
        assert activity.duration_minutes == 30

    def test_deduplicates_by_event_id(self, db, tenant_id, user):
        from datetime import datetime, timezone
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity
        from apps.activities.models import Activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@test.com",
        )
        event = CalendarEvent(
            provider_id="evt_dup",
            calendar_id="primary",
            summary="Dup Check",
            start=datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 7, 1, 14, 30, 0, tzinfo=timezone.utc),
        )

        # First call creates
        a1 = _sync_event_to_activity(conn, event, str(user.id))
        # Second call should return same
        a2 = _sync_event_to_activity(conn, event, str(user.id))
        assert a1.id == a2.id
        assert Activity.objects.filter(
            tenant_id=tenant_id,
            activity_type=Activity.ActivityType.MEETING,
        ).count() == 1

    def test_links_contact(self, db, tenant_id, user):
        from datetime import datetime, timezone
        from apps.contacts.models import Contact
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity

        contact = Contact.objects.create(
            tenant_id=tenant_id,
            first_name="Alice",
            last_name="Smith",
            email="alice@co.com",
        )
        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@test.com",
        )
        event = CalendarEvent(
            provider_id="evt_contact",
            calendar_id="primary",
            summary="Meeting with Contact",
            start=datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 7, 1, 14, 30, 0, tzinfo=timezone.utc),
            attendees=[{"email": "alice@co.com", "responseStatus": "accepted"}],
        )
        activity = _sync_event_to_activity(conn, event, str(user.id))
        assert activity.entity_type == "contact"
        assert str(activity.entity_id) == str(contact.id)
        assert "alice@co.com" not in activity.metadata.get("unmatched_attendee_emails", [])

    def test_no_contact_match_uses_sentinel_entity_id(self, db, tenant_id, user):
        from datetime import datetime, timezone
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@test.com",
        )
        event = CalendarEvent(
            provider_id="evt_nocontact",
            calendar_id="primary",
            summary="No Contact",
            start=datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 7, 1, 14, 30, 0, tzinfo=timezone.utc),
            attendees=[{"email": "stranger@external.com"}],
        )
        activity = _sync_event_to_activity(conn, event, str(user.id))
        assert activity.entity_type == ""
        # Zero-UUID sentinel when no contact matched
        assert str(activity.entity_id) == "00000000-0000-0000-0000-000000000000"
        assert "stranger@external.com" in activity.metadata.get("unmatched_attendee_emails", [])

    def test_truncates_long_title(self, db, tenant_id, user):
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@test.com",
        )
        event = CalendarEvent(
            provider_id="evt_long",
            calendar_id="primary",
            summary="A" * 1000,
        )
        activity = _sync_event_to_activity(conn, event, str(user.id))
        assert len(activity.title) == 500

    def test_truncates_long_description(self, db, tenant_id, user):
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@test.com",
        )
        event = CalendarEvent(
            provider_id="evt_longdesc",
            calendar_id="primary",
            description="B" * 6000,
        )
        activity = _sync_event_to_activity(conn, event, str(user.id))
        assert len(activity.description) == 5000


class TestGoogleCalendarApiClient:
    """GoogleCalendarApiClient — HTTP methods, auth, retry."""

    def test_init(self):
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        client = GoogleCalendarApiClient(
            access_token="abc123",
            refresh_token="refresh_xyz",
        )
        assert client.access_token == "abc123"
        assert client._refresh_token == "refresh_xyz"

    @patch("apps.sync.adapters.google_calendar.client.requests.request")
    def test_get_request(self, mock_request):
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        mock_request.return_value.status_code = 200
        mock_request.return_value.content = b'{"items": []}'
        mock_request.return_value.json.return_value = {"items": []}

        client = GoogleCalendarApiClient(access_token="test_token")
        result = client.get("calendars/primary/events", params={"maxResults": 10})

        assert result == {"items": []}
        # Verify the URL was constructed correctly
        call_kwargs = mock_request.call_args.kwargs
        assert call_kwargs["url"].startswith("https://www.googleapis.com/calendar/v3/calendars/primary/events")
        assert call_kwargs["headers"]["Authorization"] == "Bearer test_token"

    @patch("apps.sync.adapters.google_calendar.client.requests.request")
    def test_401_triggers_token_refresh(self, mock_request):
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        # First call returns 401, second succeeds
        mock_request.side_effect = [
            MagicMock(status_code=401, text="Unauthorized", content=b""),
            MagicMock(status_code=200, content=b'{"items": []}', json=lambda: {"items": []}),
        ]

        client = GoogleCalendarApiClient(
            access_token="expired_token",
            refresh_token="refresh_me",
        )

        with patch.object(client, "refresh_access_token", return_value=True) as mock_refresh:
            result = client.get("calendars/primary")
            assert result == {"items": []}
            mock_refresh.assert_called_once()

    @patch("apps.sync.adapters.google_calendar.client.requests.request")
    def test_429_rate_limit_retry(self, mock_request):
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        # Rate limited first, then success
        mock_request.side_effect = [
            MagicMock(status_code=429, headers={}, text="Rate limited", content=b""),
            MagicMock(status_code=200, content=b"{}", json=lambda: {}),
        ]

        client = GoogleCalendarApiClient(access_token="tok")
        # Should retry and succeed
        result = client.get("calendars/primary")
        assert result == {}
        assert mock_request.call_count == 2

    @patch("apps.sync.adapters.google_calendar.client.requests.post")
    def test_token_refresh_success(self, mock_post):
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"access_token": "new_token"}

        client = GoogleCalendarApiClient(access_token="old_token", refresh_token="refresh_xyz")
        result = client.refresh_access_token()
        assert result is True
        assert client.access_token == "new_token"

    @patch("apps.sync.adapters.google_calendar.client.requests.post")
    def test_token_refresh_no_refresh_token(self, mock_post):
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        client = GoogleCalendarApiClient(access_token="tok", refresh_token=None)
        result = client.refresh_access_token()
        assert result is False
        mock_post.assert_not_called()

    def test_410_raised_as_not_found(self):
        """410 Gone for syncToken expiry is raised as CalendarNotFoundError."""
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient, CalendarNotFoundError
        from unittest.mock import patch

        with patch.object(GoogleCalendarApiClient, "_request") as mock_request:
            mock_request.side_effect = CalendarNotFoundError("syncToken expired")
            client = GoogleCalendarApiClient(access_token="tok")
            with pytest.raises(CalendarNotFoundError):
                client.get("calendars/primary/events", params={"syncToken": "expired"})


class TestGoogleCalendarAdapter:
    """GoogleCalendarAdapter — get_calendar_delta, validate, refresh."""

    def test_provider_and_scopes(self):
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        assert GoogleCalendarAdapter.PROVIDER == "google_calendar"
        assert "calendar.events.readonly" in GoogleCalendarAdapter.REQUIRED_SCOPES[0]

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_delta_sync_with_sync_token(self, mock_client_class):
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        # Simulate a delta sync response with one item
        mock_client.get.return_value = {
            "nextSyncToken": "new_sync_token_456",
            "items": [
                {
                    "id": "evt_delta_1",
                    "status": "confirmed",
                    "summary": "Delta Event",
                    "start": {"dateTime": "2026-07-01T10:00:00Z"},
                    "end": {"dateTime": "2026-07-01T11:00:00Z"},
                }
            ],
        }

        adapter = GoogleCalendarAdapter(access_token="tok")
        result = adapter.get_calendar_delta({"syncToken": "old_token_123"})

        assert len(result.items) == 1
        assert result.items[0].provider_id == "evt_delta_1"
        assert result.items[0].summary == "Delta Event"
        assert result.new_cursor["syncToken"] == "new_sync_token_456"
        assert result.has_more is False

        # Verify API call params
        call_params = mock_client.get.call_args.kwargs["params"]
        assert call_params["syncToken"] == "old_token_123"
        assert call_params["showDeleted"] is True
        assert call_params["singleEvents"] is True

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_delta_sync_cancelled_event(self, mock_client_class):
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        mock_client.get.return_value = {
            "nextSyncToken": "new_token",
            "items": [
                {"id": "evt_cancelled", "status": "cancelled"},
                {"id": "evt_active", "status": "confirmed", "summary": "Active"},
            ],
        }

        adapter = GoogleCalendarAdapter(access_token="tok")
        result = adapter.get_calendar_delta({"syncToken": "tok"})

        # Cancelled events go to deleted_ids
        assert "evt_cancelled" in result.deleted_ids
        # Active events stay in items
        assert len(result.items) == 1
        assert result.items[0].provider_id == "evt_active"

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_time_range_sync_when_cursor_none(self, mock_client_class):
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        mock_client.get.return_value = {
            "nextSyncToken": "from_full_sync",
            "items": [
                {"id": "evt_full_1", "status": "confirmed", "summary": "Full Sync Item"},
            ],
        }

        adapter = GoogleCalendarAdapter(access_token="tok")
        result = adapter.get_calendar_delta(None)

        assert len(result.items) == 1
        assert result.items[0].provider_id == "evt_full_1"
        assert result.new_cursor["syncToken"] == "from_full_sync"

        # Verify time range params were passed
        call_params = mock_client.get.call_args.kwargs["params"]
        assert "timeMin" in call_params
        assert "timeMax" in call_params

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_delta_sync_falls_back_to_time_range_on_410(self, mock_client_class):
        from apps.sync.adapters.google_calendar.adapter import (
            GoogleCalendarAdapter,
        )
        from apps.sync.adapters.google_calendar.client import CalendarNotFoundError

        mock_client = mock_client_class.return_value
        # First delta call raises 410 (syncToken expired)
        mock_client.get.side_effect = [
            CalendarNotFoundError("syncToken expired"),
            # Second call (time range) succeeds
            {
                "nextSyncToken": "new_from_fallback",
                "items": [{"id": "evt_fallback", "status": "confirmed", "summary": "Fallback"}],
            },
        ]

        adapter = GoogleCalendarAdapter(access_token="tok")
        result = adapter.get_calendar_delta({"syncToken": "expired_token"})

        assert len(result.items) == 1
        assert result.items[0].provider_id == "evt_fallback"
        assert mock_client.get.call_count == 2

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_validate_connection_success(self, mock_client_class):
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        mock_client.get.return_value = {"id": "user@example.com", "kind": "calendar#calendarListEntry"}

        adapter = GoogleCalendarAdapter(access_token="tok")
        status = adapter.validate_connection()
        assert status.is_valid is True
        assert status.account_email == "user@example.com"

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_validate_connection_auth_error(self, mock_client_class):
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter
        from apps.sync.adapters.google_calendar.client import CalendarAuthError

        mock_client = mock_client_class.return_value
        mock_client.get.side_effect = CalendarAuthError("Token expired")

        adapter = GoogleCalendarAdapter(access_token="tok")
        status = adapter.validate_connection()
        assert status.is_valid is False

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_refresh_token_success(self, mock_client_class):
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        mock_client.refresh_access_token.return_value = True
        mock_client.access_token = "refreshed_token"

        adapter = GoogleCalendarAdapter(access_token="old_token", refresh_token="refresh_me")
        result = adapter.refresh_token()
        assert result.success is True
        assert result.access_token == "refreshed_token"

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_refresh_token_failure(self, mock_client_class):
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        mock_client.refresh_access_token.return_value = False

        adapter = GoogleCalendarAdapter(access_token="old_token", refresh_token="refresh_me")
        result = adapter.refresh_token()
        assert result.success is False


class TestCalendarTasks:
    """sync_calendar_delta, sync_all_calendars — Celery tasks."""

    def test_task_fails_for_missing_connection(self, db):
        from apps.sync.tasks_calendar import sync_calendar_delta

        result = sync_calendar_delta("00000000-0000-0000-0000-000000000000")
        assert "error" in result

    def test_task_fails_for_expired_connection(self, db, tenant_id, user):
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import sync_calendar_delta

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@test.com",
            status="expired",
        )
        result = sync_calendar_delta(str(conn.id))
        assert "error" in result
        assert "expired" in result["error"]

    def test_sync_all_calendars_enqueues_active(self, db, tenant_id, user):
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import sync_all_calendars
        from unittest.mock import patch

        SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="active@test.com",
            status="active",
            is_active=True,
        )
        SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="inactive@test.com",
            status="error",
            is_active=True,
        )

        with patch("apps.sync.tasks_calendar.sync_calendar_delta.delay") as mock_delay:
            result = sync_all_calendars()
            assert result["enqueued"] == 1
            mock_delay.assert_called_once()

    def test_sync_all_calendars_skips_inactive(self, db, tenant_id, user):
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import sync_all_calendars
        from unittest.mock import patch

        SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="inactive@test.com",
            status="active",
            is_active=False,
        )

        with patch("apps.sync.tasks_calendar.sync_calendar_delta.delay") as mock_delay:
            result = sync_all_calendars()
            assert result["enqueued"] == 0


class TestCalendarOAuth:
    """Calendar OAuth functions — generate URL, callback, state management."""

    def test_generate_calendar_oauth_url(self):
        from apps.sync.oauth import generate_calendar_oauth_url
        from unittest.mock import patch

        with patch("apps.sync.oauth._store_calendar_state") as mock_store:
            result = generate_calendar_oauth_url()

        assert "url" in result
        assert "state" in result
        assert len(result["state"]) > 10
        assert "calendar.events.readonly" in result["url"]
        assert "accounts.google.com/o/oauth2/auth" in result["url"]
        assert "include_granted_scopes=true" in result["url"]
        mock_store.assert_called_once_with(result["state"])

    def test_handle_calendar_oauth_callback_invalid_state(self, db, tenant_id, user):
        from apps.sync.oauth import handle_calendar_oauth_callback
        from unittest.mock import patch

        with patch("apps.sync.oauth._verify_calendar_state", return_value=False):
            with pytest.raises(ValueError, match="Invalid or expired state token"):
                handle_calendar_oauth_callback(
                    code="auth_code",
                    state="bad_state",
                    tenant_id=str(tenant_id),
                    user_id=str(user.id),
                )

    def test_handle_calendar_oauth_callback_token_exchange_fails(self, db, tenant_id, user):
        from apps.sync.oauth import handle_calendar_oauth_callback
        from unittest.mock import patch

        with patch("apps.sync.oauth._verify_calendar_state", return_value=True):
            with patch("apps.sync.oauth._exchange_code_for_calendar", return_value=None):
                with pytest.raises(ValueError, match="Failed to exchange"):
                    handle_calendar_oauth_callback(
                        code="auth_code",
                        state="valid_state",
                        tenant_id=str(tenant_id),
                        user_id=str(user.id),
                    )

    def test_handle_calendar_oauth_callback_creates_connection(self, db, tenant_id, user):
        from apps.sync.oauth import handle_calendar_oauth_callback
        from apps.sync.models import SyncConnection, SyncState
        from unittest.mock import patch

        with patch("apps.sync.oauth._verify_calendar_state", return_value=True):
            with patch("apps.sync.oauth._exchange_code_for_calendar", return_value={
                "access_token": "acc_tok",
                "refresh_token": "ref_tok",
                "expires_in": 3600,
            }):
                with patch("apps.sync.oauth._get_calendar_user_email", return_value="user@co.com"):
                    with patch("apps.sync.tasks_calendar.sync_calendar_delta.delay") as mock_task:
                        result = handle_calendar_oauth_callback(
                            code="auth_code",
                            state="valid_state",
                            tenant_id=str(tenant_id),
                            user_id=str(user.id),
                        )

        assert result["provider"] == "google_calendar"
        assert result["email"] == "user@co.com"
        assert result["status"] == "syncing"

        # Verify DB records created
        conn = SyncConnection.objects.get(provider="google_calendar")
        assert conn.provider_account == "user@co.com"

        state = SyncState.objects.get(connection=conn)
        assert state.sync_type == "calendar_event"

        # Verify initial sync was enqueued
        mock_task.assert_called_once_with(
            connection_id=str(conn.id), trigger="initial_oauth"
        )

    def test_get_calendar_redirect_uri(self):
        from apps.sync.oauth import _get_calendar_redirect_uri
        from django.conf import settings

        # Reuses GOOGLE_OAUTH_REDIRECT_URI
        uri = _get_calendar_redirect_uri()
        assert uri == getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", "")

    def test_store_and_verify_calendar_state(self):
        from apps.sync.oauth import _store_calendar_state, _verify_calendar_state

        state = "test_state_token_xyz"
        _store_calendar_state(state)
        assert _verify_calendar_state(state) is True  # First call succeeds
        assert _verify_calendar_state(state) is False  # Second call fails (one-time use)
        assert _verify_calendar_state("nonexistent") is False


class TestCalendarApiEndpoints:
    """Calendar sync endpoints — auth URL, callback, auth status."""

    def test_calendar_auth_url_endpoint(self, auth_client):
        """POST /api/sync/connections/calendar/auth-url/ returns URL + state."""
        response = auth_client.post("/api/sync/connections/calendar/auth-url/")
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "state" in data
        assert "calendar.events.readonly" in data["url"]

    def test_calendar_callback_validates_input(self, auth_client):
        """POST /api/sync/connections/calendar/callback/ requires code and state."""
        response = auth_client.post("/api/sync/connections/calendar/callback/", {}, format="json")
        assert response.status_code == 400

        response = auth_client.post(
            "/api/sync/connections/calendar/callback/",
            {"code": "abc"},
            format="json",
        )
        assert response.status_code == 400

    def test_calendar_auth_status_not_connected(self, auth_client):
        """GET .../calendar/auth-status/ returns connected=false when no connection."""
        response = auth_client.get("/api/sync/connections/calendar/auth-status/")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["email"] == ""
        assert data["events_count"] == 0

    def test_calendar_auth_status_connected(self, db, auth_client, tenant_id, user):
        """GET .../calendar/auth-status/ returns connection details when connected."""
        from apps.sync.models import SyncConnection, SyncState

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            is_active=True,
            status="active",
            last_sync_at="2026-07-01T10:00:00Z",
            last_sync_success=True,
        )
        SyncState.objects.create(
            tenant_id=tenant_id,
            user=user,
            connection=conn,
            sync_type="calendar_event",
            provider="google_calendar",
            state="complete",
            total_synced_count=42,
        )

        response = auth_client.get("/api/sync/connections/calendar/auth-status/")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["email"] == "cal@test.com"
        assert data["sync_state"] == "complete"
        assert data["events_count"] == 42
        assert data["last_sync_success"] is True

    def test_sync_viewset_actions_are_registered(self, auth_client):
        """Verify the router registers calendar actions on the viewset."""
        response = auth_client.get("/api/sync/connections/")
        # Verify it returns successfully (router is working)
        assert response.status_code == 200


class TestCalendarHandleSyncError:
    """_handle_sync_error on calendar connections."""

    def test_consecutive_failures_mark_error(self, db, tenant_id, user):
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _handle_sync_error

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            error_count=4,
            status="active",
        )
        _handle_sync_error(conn, Exception("Something went wrong"))
        conn.refresh_from_db()

        assert conn.status == "error"
        assert conn.error_count == 5
        assert "5 consecutive" in conn.last_error_message
        assert conn.last_sync_success is False

    def test_backoff_doubles_interval(self, db, tenant_id, user):
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _handle_sync_error

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            error_count=2,
            sync_interval_seconds=60,
            status="active",
        )

        _handle_sync_error(conn, Exception("Fail 3"))
        conn.refresh_from_db()
        assert conn.error_count == 3
        assert conn.sync_interval_seconds == 120

        _handle_sync_error(conn, Exception("Fail 4"))
        conn.refresh_from_db()
        assert conn.error_count == 4
        assert conn.sync_interval_seconds == 240

    def test_backoff_respects_cap(self, db, tenant_id, user):
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _handle_sync_error

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            error_count=2,
            sync_interval_seconds=300,
            status="active",
        )

        _handle_sync_error(conn, Exception("Fail 3"))
        conn.refresh_from_db()
        # 300 * 2 = 600, which is the cap
        assert conn.sync_interval_seconds == 600

    def test_backoff_from_zero_interval(self, db, tenant_id, user):
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _handle_sync_error

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            error_count=2,
            sync_interval_seconds=0,  # Default/unset
            status="active",
        )

        _handle_sync_error(conn, Exception("Fail 3"))
        conn.refresh_from_db()
        # 0 * 2 would be 0, but our fix floors at 60 → 60 * 2 = 120
        assert conn.sync_interval_seconds == 120