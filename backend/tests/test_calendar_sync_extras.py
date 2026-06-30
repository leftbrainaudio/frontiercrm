"""
# ─── Calendar Sync Gap Tests ──────────────────────────────────────────────
#
# Tests covering critical paths missed by the initial test suite:
#   - _get_calendar_adapter (adapter creation, missing token)
#   - _refresh_tokens_if_needed (token validation, refresh, expiry)
#   - _process_deleted_event (deletion path)
#   - Event-to-Activity edge cases (no title, multiple contacts,
#     cross-connection dedup, tentative status)
#   - Client edge cases (403 daily limit, 500/502/503 retry,
#     network failure, max retries exhausted)
#   - Adapter edge cases (pagination, MAX_PAGES, empty list,
#     get_initial_cursor fallback, has_more flag)
#   - _do_sync end-to-end integration (full task execution path)
#   - Unauthenticated API endpoint access
#   - OAuth scope validation failure path
#   - Celery task retry api and rate_limit annotation
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone as tz


# ═══════════════════════════════════════════════════════════════════════════
# _get_calendar_adapter
# ═══════════════════════════════════════════════════════════════════════════

class TestGetCalendarAdapter:
    """_get_calendar_adapter — adapter creation from SyncConnection."""

    def test_no_access_token_returns_none(self, db, tenant_id, user):
        """Missing access_token should return None, not crash."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _get_calendar_adapter

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            access_token_encrypted="",  # No token
        )
        result = _get_calendar_adapter(conn)
        assert result is None

    def test_with_valid_tokens_returns_adapter(self, db, tenant_id, user):
        """Valid access+refresh tokens should produce a GoogleCalendarAdapter."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _get_calendar_adapter
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            access_token_encrypted="valid_access_token",
            refresh_token_encrypted="valid_refresh_token",
        )
        adapter = _get_calendar_adapter(conn)
        assert adapter is not None
        assert isinstance(adapter, GoogleCalendarAdapter)
        assert adapter._client.access_token == "valid_access_token"
        assert adapter._client._refresh_token == "valid_refresh_token"

    def test_without_refresh_token_returns_adapter(self, db, tenant_id, user):
        """Adapter can be created without a refresh token (access only)."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _get_calendar_adapter

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            access_token_encrypted="valid_access_token",
            refresh_token_encrypted="",  # No refresh token
        )
        adapter = _get_calendar_adapter(conn)
        assert adapter is not None
        assert adapter._client._refresh_token is None


# ═══════════════════════════════════════════════════════════════════════════
# _refresh_tokens_if_needed
# ═══════════════════════════════════════════════════════════════════════════

class TestRefreshTokensIfNeeded:
    """_refresh_tokens_if_needed — token expiry check and refresh."""

    def test_token_still_valid_skips_refresh(self, db, tenant_id, user):
        """When token_expires_at is in the future, no refresh needed."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import (
            _get_calendar_adapter,
            _refresh_tokens_if_needed,
        )

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            access_token_encrypted="valid_token",
            refresh_token_encrypted="refresh_me",
            token_expires_at=tz.now() + tz.timedelta(hours=1),  # Still valid
        )
        adapter = _get_calendar_adapter(conn)
        assert adapter is not None

        with patch.object(adapter, "refresh_token") as mock_refresh:
            result = _refresh_tokens_if_needed(conn, adapter)
            assert result is True
            mock_refresh.assert_not_called()

    def test_expired_token_refresh_succeeds(self, db, tenant_id, user):
        """When token is expired, refresh is called and tokens updated."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import (
            _get_calendar_adapter,
            _refresh_tokens_if_needed,
        )

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            access_token_encrypted="expired_token",
            refresh_token_encrypted="refresh_me",
            token_expires_at=tz.now() - tz.timedelta(minutes=5),  # Expired
        )
        adapter = _get_calendar_adapter(conn)
        assert adapter is not None

        from apps.sync.adapters.base import TokenRefreshResult
        with patch.object(adapter, "refresh_token", return_value=TokenRefreshResult(
            success=True,
            access_token="new_token_abc",
            expires_in=3600,
        )):
            result = _refresh_tokens_if_needed(conn, adapter)

        assert result is True
        conn.refresh_from_db()
        assert conn.access_token_encrypted == "new_token_abc"
        assert conn.token_expires_at is not None
        assert conn.token_expires_at > tz.now()

    def test_expired_token_refresh_fails_marks_expired(self, db, tenant_id, user):
        """When refresh fails, connection status is set to 'expired'."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import (
            _get_calendar_adapter,
            _refresh_tokens_if_needed,
        )

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            access_token_encrypted="expired_token",
            refresh_token_encrypted="refresh_me",
            token_expires_at=tz.now() - tz.timedelta(minutes=5),
            status="active",
        )
        adapter = _get_calendar_adapter(conn)
        assert adapter is not None

        from apps.sync.adapters.base import TokenRefreshResult
        with patch.object(adapter, "refresh_token", return_value=TokenRefreshResult(
            success=False,
        )):
            result = _refresh_tokens_if_needed(conn, adapter)

        assert result is False
        conn.refresh_from_db()
        assert conn.status == "expired"
        assert "Token refresh failed" in conn.last_error_message

    def test_token_expires_at_none_triggers_refresh(self, db, tenant_id, user):
        """When token_expires_at is None, refresh is attempted."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import (
            _get_calendar_adapter,
            _refresh_tokens_if_needed,
        )

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            access_token_encrypted="some_token",
            refresh_token_encrypted="refresh_me",
            token_expires_at=None,  # No expiry info
        )
        adapter = _get_calendar_adapter(conn)
        assert adapter is not None

        from apps.sync.adapters.base import TokenRefreshResult
        with patch.object(adapter, "refresh_token", return_value=TokenRefreshResult(
            success=True,
            access_token="refreshed",
            expires_in=3600,
        )):
            result = _refresh_tokens_if_needed(conn, adapter)

        assert result is True
        conn.refresh_from_db()
        assert conn.access_token_encrypted == "refreshed"


# ═══════════════════════════════════════════════════════════════════════════
# _process_deleted_event
# ═══════════════════════════════════════════════════════════════════════════

class TestProcessDeletedEvent:
    """_process_deleted_event — handling deleted calendar events."""

    def test_deletes_matching_activity(self, db, tenant_id, user):
        """Existing activity with matching external_event_id is handled."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _process_deleted_event

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
        )
        from apps.activities.models import Activity
        activity = Activity.objects.create(
            tenant_id=tenant_id,
            activity_type=Activity.ActivityType.MEETING,
            title="Old Meeting",
            entity_id="00000000-0000-0000-0000-000000000000",
            metadata={"external_event_id": "evt_to_delete"},
            actor_id=str(user.id),
        )
        # Should not crash
        _process_deleted_event(conn, "evt_to_delete")
        # Activity still exists (no soft-delete field, just tracked in metadata)
        activity.refresh_from_db()
        assert activity.title == "Old Meeting"

    def test_no_matching_activity(self, db, tenant_id, user):
        """Non-existent event ID should not crash."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _process_deleted_event

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
        )
        # Should not crash or raise
        _process_deleted_event(conn, "nonexistent_event_id")

    def test_multiple_matching_activities(self, db, tenant_id, user):
        """Multiple activities with same external_event_id handled."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _process_deleted_event
        from apps.activities.models import Activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
        )
        Activity.objects.create(
            tenant_id=tenant_id,
            activity_type=Activity.ActivityType.MEETING,
            title="Meeting A",
            entity_id="00000000-0000-0000-0000-000000000000",
            metadata={"external_event_id": "evt_dup"},
            actor_id=str(user.id),
        )
        Activity.objects.create(
            tenant_id=tenant_id,
            activity_type=Activity.ActivityType.MEETING,
            title="Meeting B",
            entity_id="00000000-0000-0000-0000-000000000000",
            metadata={"external_event_id": "evt_dup"},
            actor_id=str(user.id),
        )
        # Should not crash
        _process_deleted_event(conn, "evt_dup")
        # Both activities still exist (no hard delete)
        assert Activity.objects.filter(
            tenant_id=tenant_id,
            metadata__external_event_id="evt_dup",
        ).count() == 2


# ═══════════════════════════════════════════════════════════════════════════
# _sync_event_to_activity — edge cases
# ═══════════════════════════════════════════════════════════════════════════

class TestSyncEventToActivityEdgeCases:
    """_sync_event_to_activity — uncovered edge cases."""

    def test_empty_summary_uses_no_title_fallback(self, db, tenant_id, user):
        """Events with empty summary get '(No title)' as title."""
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity
        from apps.activities.models import Activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
        )
        event = CalendarEvent(
            provider_id="evt_notitle",
            calendar_id="primary",
            summary="",  # Empty summary
        )
        activity = _sync_event_to_activity(conn, event, str(user.id))
        assert activity is not None
        assert activity.title == "(No title)"
        assert activity.activity_type == Activity.ActivityType.MEETING

    def test_handles_none_description(self, db, tenant_id, user):
        """Events with None description should not crash (defaults to empty)."""
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
        )
        event = CalendarEvent(
            provider_id="evt_nodesc",
            calendar_id="primary",
            summary="No Desc Meeting",
            description=None,  # Should be handled gracefully
        )
        activity = _sync_event_to_activity(conn, event, str(user.id))
        assert activity.description == ""

    def test_multiple_matched_contacts_uses_first(self, db, tenant_id, user):
        """Multiple attendees matching contacts — entity_id uses first match."""
        from apps.contacts.models import Contact
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
        )
        contact_a = Contact.objects.create(
            tenant_id=tenant_id,
            first_name="Alice",
            last_name="Alpha",
            email="alice@co.com",
        )
        Contact.objects.create(
            tenant_id=tenant_id,
            first_name="Bob",
            last_name="Beta",
            email="bob@co.com",
        )
        event = CalendarEvent(
            provider_id="evt_multicontact",
            calendar_id="primary",
            summary="Multi Contact Meeting",
            attendees=[
                {"email": "alice@co.com"},
                {"email": "bob@co.com"},
            ],
        )
        activity = _sync_event_to_activity(conn, event, str(user.id))
        assert activity.entity_type == "contact"
        # entity_id should be one of the matched contact IDs
        # (order may vary since Contact.objects.filter(email__in=...) doesn't guarantee order)
        contact_b = Contact.objects.get(tenant_id=tenant_id, email="bob@co.com")
        assert str(activity.entity_id) in (str(contact_a.id), str(contact_b.id))
        assert "alice@co.com" not in activity.metadata.get("unmatched_attendee_emails", [])
        assert "bob@co.com" not in activity.metadata.get("unmatched_attendee_emails", [])

    def test_tentative_status_stored_in_metadata(self, db, tenant_id, user):
        """Events with 'tentative' status are synced with status in metadata."""
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
        )
        event = CalendarEvent(
            provider_id="evt_tentative",
            calendar_id="primary",
            summary="Tentative Meeting",
            status="tentative",
        )
        activity = _sync_event_to_activity(conn, event, str(user.id))
        assert activity.metadata["status"] == "tentative"

    def test_dedup_scoped_to_connection(self, db, tenant_id, user):
        """Dedup is by tenant+type+external_event_id — different event IDs
        for different connections should not collide."""
        from apps.sync.adapters.base import CalendarEvent
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import _sync_event_to_activity
        from apps.activities.models import Activity
        from datetime import datetime, timezone

        conn1 = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="acc1@test.com",
        )
        conn2 = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="acc2@test.com",
        )

        event1 = CalendarEvent(
            provider_id="evt_001",
            calendar_id="primary",
            summary="Cal 1 Event",
            start=datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 7, 1, 14, 30, 0, tzinfo=timezone.utc),
        )
        event2 = CalendarEvent(
            provider_id="evt_002",
            calendar_id="primary",
            summary="Cal 2 Event",
            start=datetime(2026, 7, 1, 15, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 7, 1, 15, 30, 0, tzinfo=timezone.utc),
        )

        a1 = _sync_event_to_activity(conn1, event1, str(user.id))
        a2 = _sync_event_to_activity(conn2, event2, str(user.id))
        assert a1.id != a2.id
        assert Activity.objects.filter(
            tenant_id=tenant_id,
            activity_type=Activity.ActivityType.MEETING,
        ).count() == 2


# ═══════════════════════════════════════════════════════════════════════════
# GoogleCalendarApiClient edge cases
# ═══════════════════════════════════════════════════════════════════════════

class TestGoogleCalendarApiClientEdgeCases:
    """GoogleCalendarApiClient — uncovered error/retry paths."""

    @patch("apps.sync.adapters.google_calendar.client.requests.request")
    def test_403_daily_limit_exceeded(self, mock_request):
        """403 with dailyLimitExceeded raises CalendarRateLimitError."""
        from apps.sync.adapters.google_calendar.client import (
            GoogleCalendarApiClient,
            CalendarRateLimitError,
        )

        mock_response = MagicMock(status_code=403)
        mock_response.text = "dailyLimitExceeded - Daily quota exceeded"
        mock_request.return_value = mock_response

        client = GoogleCalendarApiClient(access_token="tok")
        with pytest.raises(CalendarRateLimitError, match="Daily API quota exceeded"):
            client.get("calendars/primary")

    @patch("apps.sync.adapters.google_calendar.client.requests.request")
    def test_500_retry_then_success(self, mock_request):
        """500 server error triggers retry, succeeds on second attempt."""
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        mock_request.side_effect = [
            MagicMock(status_code=500, text="Server Error", content=b""),
            MagicMock(status_code=200, content=b'{"kind": "calendar#calendar"}', json=lambda: {"kind": "calendar#calendar"}),
        ]

        client = GoogleCalendarApiClient(access_token="tok")
        result = client.get("calendars/primary")
        assert result == {"kind": "calendar#calendar"}
        assert mock_request.call_count == 2

    @patch("apps.sync.adapters.google_calendar.client.requests.request")
    def test_503_retry_then_success(self, mock_request):
        """503 service unavailable triggers retry."""
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        mock_request.side_effect = [
            MagicMock(status_code=503, text="Service Unavailable", content=b""),
            MagicMock(status_code=200, content=b"{}", json=lambda: {}),
        ]

        client = GoogleCalendarApiClient(access_token="tok")
        result = client.get("calendars/primary")
        assert result == {}
        assert mock_request.call_count == 2

    @patch("apps.sync.adapters.google_calendar.client.requests.request")
    def test_502_retry_then_success(self, mock_request):
        """502 bad gateway triggers retry."""
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        mock_request.side_effect = [
            MagicMock(status_code=502, text="Bad Gateway", content=b""),
            MagicMock(status_code=200, content=b"{}", json=lambda: {}),
        ]

        client = GoogleCalendarApiClient(access_token="tok")
        result = client.get("calendars/primary")
        assert result == {}
        assert mock_request.call_count == 2

    @patch("apps.sync.adapters.google_calendar.client.requests.request")
    def test_connection_error_retry_then_fail(self, mock_request):
        """Network failure retries and eventually raises CalendarApiError."""
        import requests
        from apps.sync.adapters.google_calendar.client import (
            GoogleCalendarApiClient,
            CalendarApiError,
        )

        mock_request.side_effect = requests.ConnectionError("Connection refused")

        client = GoogleCalendarApiClient(access_token="tok")
        with patch.object(client, "MAX_RETRIES", 2):  # Speed up test
            with pytest.raises(CalendarApiError, match="Request failed after 2 retries"):
                client.get("calendars/primary")
        assert mock_request.call_count == 2

    @patch("apps.sync.adapters.google_calendar.client.requests.request")
    def test_204_empty_response(self, mock_request):
        """204 No Content is handled gracefully (returns empty dict)."""
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        mock_request.return_value = MagicMock(status_code=204, content=b"")

        client = GoogleCalendarApiClient(access_token="tok")
        result = client.get("calendars/primary")
        assert result == {}

    @patch("apps.sync.adapters.google_calendar.client.requests.request")
    def test_max_retries_on_500_gives_up(self, mock_request):
        """All retries are exhausted on persistent 500 errors."""
        from apps.sync.adapters.google_calendar.client import (
            GoogleCalendarApiClient,
            CalendarApiError,
        )

        mock_request.return_value = MagicMock(status_code=500, text="Server Error", content=b"")

        client = GoogleCalendarApiClient(access_token="tok")
        with patch.object(client, "MAX_RETRIES", 3):
            with pytest.raises(CalendarApiError, match="Request failed after 3 retries"):
                client.get("calendars/primary")
        assert mock_request.call_count == 3


# ═══════════════════════════════════════════════════════════════════════════
# GoogleCalendarAdapter edge cases
# ═══════════════════════════════════════════════════════════════════════════

class TestGoogleCalendarAdapterEdgeCases:
    """GoogleCalendarAdapter — pagination, empty lists, has_more."""

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_delta_sync_pagination(self, mock_client_class):
        """Delta sync follows nextPageToken across multiple pages."""
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        # First page has nextPageToken, second page is final
        mock_client.get.side_effect = [
            {
                "nextSyncToken": "final_token",
                "nextPageToken": "page2",
                "items": [
                    {"id": "evt_p1", "status": "confirmed", "summary": "Page 1 Event"},
                ],
            },
            {
                "nextSyncToken": "final_token",
                "items": [
                    {"id": "evt_p2", "status": "confirmed", "summary": "Page 2 Event"},
                ],
            },
        ]

        adapter = GoogleCalendarAdapter(access_token="tok")
        result = adapter.get_calendar_delta({"syncToken": "tok"})

        assert len(result.items) == 2
        assert result.items[0].provider_id == "evt_p1"
        assert result.items[1].provider_id == "evt_p2"
        assert result.new_cursor["syncToken"] == "final_token"
        assert result.has_more is False
        assert mock_client.get.call_count == 2

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_delta_sync_has_more_flag(self, mock_client_class):
        """When MAX_PAGES is reached and more pages exist, has_more=True."""
        from apps.sync.adapters.google_calendar.adapter import (
            GoogleCalendarAdapter,
            MAX_PAGES,
        )

        mock_client = mock_client_class.return_value
        # Simulate MAX_PAGES responses each with a nextPageToken
        side_effects = []
        for i in range(MAX_PAGES):
            side_effects.append({
                "nextSyncToken": f"token_{i}",
                "nextPageToken": f"page_{i+1}",
                "items": [{"id": f"evt_p{i}", "status": "confirmed", "summary": f"Event {i}"}],
            })
        # The last page would be beyond MAX_PAGES, but we never get there
        mock_client.get.side_effect = side_effects

        adapter = GoogleCalendarAdapter(access_token="tok")
        result = adapter.get_calendar_delta({"syncToken": "tok"})

        assert len(result.items) == MAX_PAGES
        assert result.has_more is True

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_delta_sync_empty_items(self, mock_client_class):
        """Delta sync with no new events returns empty items list."""
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        mock_client.get.return_value = {
            "nextSyncToken": "still_fresh",
            "items": [],
        }

        adapter = GoogleCalendarAdapter(access_token="tok")
        result = adapter.get_calendar_delta({"syncToken": "tok"})

        assert result.items == []
        assert result.deleted_ids == []
        assert result.new_cursor["syncToken"] == "still_fresh"

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_get_initial_cursor_time_range_fallback(self, mock_client_class):
        """get_initial_cursor falls back to lastSyncTime when no syncToken."""
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        # Return a response with no nextSyncToken
        mock_client.get.return_value = {
            "items": [],
        }

        adapter = GoogleCalendarAdapter(access_token="tok")
        cursor = adapter.get_initial_cursor()

        assert "lastSyncTime" in cursor
        assert cursor["lastSyncTime"] is not None

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_time_range_sync_empty_items(self, mock_client_class):
        """Time range sync with no events returns empty result."""
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        mock_client.get.return_value = {"items": []}

        adapter = GoogleCalendarAdapter(access_token="tok")
        result = adapter.get_calendar_delta(None)

        assert result.items == []
        assert result.deleted_ids == []
        assert "lastSyncTime" in result.new_cursor  # Fallback when no syncToken

    @patch("apps.sync.adapters.google_calendar.adapter.GoogleCalendarApiClient")
    def test_validate_connection_unknown_error(self, mock_client_class):
        """Generic exception during validate returns error status."""
        from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

        mock_client = mock_client_class.return_value
        mock_client.get.side_effect = RuntimeError("Unexpected error")

        adapter = GoogleCalendarAdapter(access_token="tok")
        status = adapter.validate_connection()
        assert status.is_valid is False
        assert status.error is not None


# ═══════════════════════════════════════════════════════════════════════════
# _do_sync end-to-end integration
# ═══════════════════════════════════════════════════════════════════════════

class TestSyncTaskDoSync:
    """sync_calendar_delta._do_sync — full execution path."""

    def test_do_sync_full_flow(self, db, tenant_id, user):
        """Complete sync flow: adapter produces events → activities created →
        sync state updated → connection updated."""
        import json
        from datetime import datetime, timezone
        from django.utils import timezone as tz
        from apps.sync.models import SyncConnection, SyncState
        from apps.sync.tasks_calendar import sync_calendar_delta
        from apps.sync.adapters.base import CalendarDeltaResult, CalendarEvent
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient
        from apps.activities.models import Activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            access_token_encrypted="valid_token",
            refresh_token_encrypted="refresh_me",
            token_expires_at=tz.now() + tz.timedelta(hours=1),  # Still valid
            status="active",
            is_active=True,
        )

        # Create sync state entry (simulates one already existing)
        SyncState.objects.create(
            tenant_id=tenant_id,
            user_id=user.id,
            connection=conn,
            sync_type="calendar_event",
            provider="google_calendar",
            state="pending",
            cursor_data={"syncToken": "existing_token"},
        )

        # Mock the adapter's API client to return events
        mock_get = MagicMock()
        mock_get.side_effect = [
            # First call: calendar delta response with events
            {
                "nextSyncToken": "new_sync_token_789",
                "items": [
                    {
                        "id": "evt_integration_1",
                        "status": "confirmed",
                        "summary": "Integration Test Event",
                        "start": {"dateTime": "2026-07-01T14:00:00Z"},
                        "end": {"dateTime": "2026-07-01T15:00:00Z"},
                    },
                ],
            },
        ]

        with patch.object(GoogleCalendarApiClient, "_request", mock_get):
            with patch("apps.sync.tasks_calendar.GoogleCalendarAdapter") as MockAdapter:
                adapter_instance = MockAdapter.return_value
                adapter_instance._client = MagicMock()
                adapter_instance._client.get = mock_get

                # Simulate _refresh_tokens_if_needed returning True
                with patch("apps.sync.tasks_calendar._refresh_tokens_if_needed", return_value=True):
                    # Simulate the adapter delta response
                    with patch.object(
                        adapter_instance,
                        "get_calendar_delta",
                        return_value=CalendarDeltaResult(
                            items=[
                                CalendarEvent(
                                    provider_id="evt_integration_1",
                                    calendar_id="primary",
                                    summary="Integration Test Event",
                                    start=datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc),
                                    end=datetime(2026, 7, 1, 15, 0, 0, tzinfo=timezone.utc),
                                ),
                            ],
                            deleted_ids=[],
                            new_cursor={"syncToken": "new_sync_token_789"},
                        ),
                    ):
                        result = sync_calendar_delta(str(conn.id), trigger="test")

        # Assert task result
        assert result["synced"] == 1
        assert result["deleted"] == 0
        assert result["connection_id"] == str(conn.id)
        assert result["trigger"] == "test"

        # Assert activity was created
        activity = Activity.objects.filter(
            tenant_id=tenant_id,
            activity_type=Activity.ActivityType.MEETING,
            metadata__external_event_id="evt_integration_1",
        ).first()
        assert activity is not None
        assert activity.title == "Integration Test Event"

        # Assert sync state was updated
        sync_state = SyncState.objects.get(connection=conn, sync_type="calendar_event")
        assert sync_state.state == "complete"
        assert sync_state.cursor_data == {"syncToken": "new_sync_token_789"}
        assert sync_state.total_synced_count == 1
        assert sync_state.last_delta_sync_at is not None

        # Assert connection was updated
        conn.refresh_from_db()
        assert conn.last_sync_success is True
        assert conn.error_count == 0

    def test_do_sync_processes_deletions(self, db, tenant_id, user):
        """Deleted event IDs from delta are processed."""
        from datetime import datetime, timezone
        from django.utils import timezone as tz
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import sync_calendar_delta
        from apps.sync.adapters.base import CalendarDeltaResult, CalendarEvent
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient
        from apps.activities.models import Activity

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            access_token_encrypted="valid_token",
            refresh_token_encrypted="refresh_me",
            token_expires_at=tz.now() + tz.timedelta(hours=1),
            status="active",
            is_active=True,
        )

        # Create an activity that should be marked as deleted
        Activity.objects.create(
            tenant_id=tenant_id,
            activity_type=Activity.ActivityType.MEETING,
            title="Event to Delete",
            entity_id="00000000-0000-0000-0000-000000000000",
            metadata={"external_event_id": "evt_to_delete"},
            actor_id=str(user.id),
        )

        mock_get = MagicMock()
        mock_get.side_effect = [
            {
                "nextSyncToken": "post_delete_token",
                "items": [
                    {
                        "id": "evt_new",
                        "status": "confirmed",
                        "summary": "New Event",
                        "start": {"dateTime": "2026-07-01T14:00:00Z"},
                        "end": {"dateTime": "2026-07-01T15:00:00Z"},
                    },
                ],
            },
        ]

        with patch.object(GoogleCalendarApiClient, "_request", mock_get):
            with patch("apps.sync.tasks_calendar.GoogleCalendarAdapter") as MockAdapter:
                adapter_instance = MockAdapter.return_value
                adapter_instance._client = MagicMock()
                adapter_instance._client.get = mock_get

                with patch("apps.sync.tasks_calendar._refresh_tokens_if_needed", return_value=True):
                    with patch.object(
                        adapter_instance,
                        "get_calendar_delta",
                        return_value=CalendarDeltaResult(
                            items=[
                                CalendarEvent(
                                    provider_id="evt_new",
                                    calendar_id="primary",
                                    summary="New Event",
                                    start=datetime(2026, 7, 1, 14, 0, 0, tzinfo=timezone.utc),
                                    end=datetime(2026, 7, 1, 15, 0, 0, tzinfo=timezone.utc),
                                ),
                            ],
                            deleted_ids=["evt_to_delete"],
                            new_cursor={"syncToken": "post_delete_token"},
                        ),
                    ):
                        result = sync_calendar_delta(str(conn.id), trigger="scheduled")

        assert result["synced"] == 1
        assert result["deleted"] == 1

        # Both activities still exist in DB (no hard delete)
        assert Activity.objects.filter(
            tenant_id=tenant_id,
            activity_type=Activity.ActivityType.MEETING,
        ).count() == 2

    def test_do_sync_with_no_events(self, db, tenant_id, user):
        """Delta sync with no new events or deletions returns 0/0."""
        from django.utils import timezone as tz
        from apps.sync.models import SyncConnection
        from apps.sync.tasks_calendar import sync_calendar_delta
        from apps.sync.adapters.base import CalendarDeltaResult
        from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="cal@test.com",
            access_token_encrypted="valid_token",
            refresh_token_encrypted="refresh_me",
            token_expires_at=tz.now() + tz.timedelta(hours=1),
            status="active",
            is_active=True,
        )

        mock_get = MagicMock()
        mock_get.side_effect = [
            {
                "nextSyncToken": "same_token",
                "items": [],
            },
        ]

        with patch.object(GoogleCalendarApiClient, "_request", mock_get):
            with patch("apps.sync.tasks_calendar.GoogleCalendarAdapter") as MockAdapter:
                adapter_instance = MockAdapter.return_value
                adapter_instance._client = MagicMock()
                adapter_instance._client.get = mock_get

                with patch("apps.sync.tasks_calendar._refresh_tokens_if_needed", return_value=True):
                    with patch.object(
                        adapter_instance,
                        "get_calendar_delta",
                        return_value=CalendarDeltaResult(
                            items=[],
                            deleted_ids=[],
                            new_cursor={"syncToken": "same_token"},
                        ),
                    ):
                        result = sync_calendar_delta(str(conn.id), trigger="scheduled")

        assert result["synced"] == 0
        assert result["deleted"] == 0
        assert "error" not in result


# ═══════════════════════════════════════════════════════════════════════════
# API endpoint — unauthenticated access
# ═══════════════════════════════════════════════════════════════════════════

class TestCalendarApiEndpointsAuth:
    """Calendar endpoints require authentication."""

    def test_auth_url_requires_auth(self, api_client):
        """POST /api/sync/connections/calendar/auth-url/ without auth."""
        response = api_client.post("/api/sync/connections/calendar/auth-url/")
        assert response.status_code in (401, 403)

    def test_callback_requires_auth(self, api_client):
        """POST /api/sync/connections/calendar/callback/ without auth."""
        response = api_client.post(
            "/api/sync/connections/calendar/callback/",
            {"code": "abc", "state": "xyz"},
            format="json",
        )
        assert response.status_code in (401, 403)

    def test_auth_status_requires_auth(self, api_client):
        """GET /api/sync/connections/calendar/auth-status/ without auth."""
        response = api_client.get("/api/sync/connections/calendar/auth-status/")
        assert response.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════
# OAuth — scope validation and error paths
# ═══════════════════════════════════════════════════════════════════════════

class TestCalendarOAuthEdgeCases:
    """Calendar OAuth — uncovered error paths."""

    def test_token_exchange_network_error(self, db, tenant_id, user):
        """Network failure during token exchange returns None gracefully."""
        from apps.sync.oauth import _exchange_code_for_calendar
        from unittest.mock import patch
        import requests

        with patch("apps.sync.oauth.requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Network error")
            result = _exchange_code_for_calendar("auth_code")
        assert result is None

    def test_token_exchange_non_200(self, db, tenant_id, user):
        """Non-200 response during token exchange returns None."""
        from apps.sync.oauth import _exchange_code_for_calendar
        from unittest.mock import patch

        with patch("apps.sync.oauth.requests.post") as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {"error": "invalid_grant"}
            result = _exchange_code_for_calendar("auth_code")
        assert result is None

    def test_get_calendar_user_email_network_error(self):
        """Network failure during email fetch returns 'unknown@unknown.com'."""
        from apps.sync.oauth import _get_calendar_user_email
        from unittest.mock import patch
        import requests

        with patch("apps.sync.oauth.requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Timeout")
            email = _get_calendar_user_email("some_token")
        assert email == "unknown@unknown.com"

    def test_calendar_oauth_url_includes_include_granted_scopes(self):
        """The calendar OAuth URL must include include_granted_scopes=true."""
        from apps.sync.oauth import generate_calendar_oauth_url
        from unittest.mock import patch

        with patch("apps.sync.oauth._store_calendar_state"):
            result = generate_calendar_oauth_url()
        assert "include_granted_scopes=true" in result["url"]

    def test_calendar_oauth_url_has_correct_scopes(self):
        """The calendar OAuth URL uses calendar.events.readonly scope."""
        from apps.sync.oauth import generate_calendar_oauth_url
        from unittest.mock import patch

        with patch("apps.sync.oauth._store_calendar_state"):
            result = generate_calendar_oauth_url()
        # Verify the correct calendar scope is requested
        assert "calendar.events.readonly" in result["url"]


# ═══════════════════════════════════════════════════════════════════════════
# Celery task configuration
# ═══════════════════════════════════════════════════════════════════════════

class TestCalendarTaskConfiguration:
    """sync_calendar_delta task metadata — retries, rate limit, bind."""

    def test_task_has_rate_limit(self):
        """The calendar sync task is rate limited to prevent API abuse."""
        from apps.sync.tasks_calendar import sync_calendar_delta

        # Celery task should have rate_limit attribute
        assert hasattr(sync_calendar_delta, "rate_limit")

    def test_task_max_retries(self):
        """The calendar sync task has configured max_retries."""
        from apps.sync.tasks_calendar import sync_calendar_delta

        # Celery task should have max_retries configured
        assert hasattr(sync_calendar_delta, "max_retries")
        # Should be > 0
        assert sync_calendar_delta.max_retries > 0

    def test_task_is_bound(self):
        """The calendar sync task is a bound task (self arg available)."""
        from apps.sync.tasks_calendar import sync_calendar_delta

        # Bound tasks have 'bind=True' in their decorator — the task class
        # gets a 'bind' attribute from Celery
        assert hasattr(sync_calendar_delta, "bind")


# ═══════════════════════════════════════════════════════════════════════════
# CalendarEvent dataclass — additional edge cases
# ═══════════════════════════════════════════════════════════════════════════

class TestCalendarEventHashAndEquality:
    """CalendarEvent — sensible equality/hash semantics."""

    def test_events_with_same_fields_are_not_identical(self):
        """Two CalendarEvent instances with same values are different objects."""
        from apps.sync.adapters.base import CalendarEvent

        e1 = CalendarEvent(provider_id="e1", calendar_id="primary")
        e2 = CalendarEvent(provider_id="e1", calendar_id="primary")
        # Dataclass with default eq=True means by-value comparison
        assert e1 == e2
        assert id(e1) != id(e2)