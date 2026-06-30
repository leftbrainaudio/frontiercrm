"""Tests for Calendar Event Creation & Push Notifications (Phase 5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone as tz

from apps.sync.adapters.base import CalendarEvent
from apps.sync.adapters.google_calendar.adapter import (
    GoogleCalendarAdapter,
    _parse_google_event,
)
from apps.sync.adapters.google_calendar.client import GoogleCalendarApiClient
from apps.sync.models import CalendarWatchChannel, SyncConnection
from apps.sync.tasks_calendar import push_crm_event_to_calendar


# =============================================================================
# Adapter Write Methods
# =============================================================================


class TestCalendarApiClient:
    """Test GoogleCalendarApiClient HTTP methods."""

    def test_build_event_body_basic(self):
        """_build_event_body produces correct Google API body."""
        start = datetime(2026, 7, 15, 14, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 7, 15, 15, 0, 0, tzinfo=timezone.utc)

        body = GoogleCalendarApiClient.build_event_body(
            summary="Test Meeting",
            start=start,
            end=end,
            description="A test",
            location="Room A",
            timezone="America/New_York",
        )

        assert body["summary"] == "Test Meeting"
        assert body["start"]["dateTime"] == start.isoformat()
        assert body["start"]["timeZone"] == "America/New_York"
        assert body["end"]["dateTime"] == end.isoformat()
        assert body["description"] == "A test"
        assert body["location"] == "Room A"

    def test_build_event_body_all_day(self):
        """All-day events use 'date' format not 'dateTime'."""
        start = datetime(2026, 7, 15, tzinfo=timezone.utc)
        end = datetime(2026, 7, 16, tzinfo=timezone.utc)

        body = GoogleCalendarApiClient.build_event_body(
            summary="All Day Event",
            start=start,
            end=end,
            all_day=True,
        )

        assert "dateTime" not in body["start"]
        assert body["start"]["date"] == "2026-07-15"
        assert body["end"]["date"] == "2026-07-16"

    def test_build_event_body_attendees(self):
        """Attendees are formatted correctly."""
        start = datetime(2026, 7, 15, 14, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 7, 15, 15, 0, 0, tzinfo=timezone.utc)

        body = GoogleCalendarApiClient.build_event_body(
            summary="Meeting",
            start=start,
            end=end,
            attendees=[
                {"email": "alice@example.com", "displayName": "Alice"},
                {"email": ""},
                {"email": "bob@example.com"},
            ],
        )

        assert len(body["attendees"]) == 2
        assert body["attendees"][0]["email"] == "alice@example.com"
        assert body["attendees"][1]["email"] == "bob@example.com"
        assert body["attendees"][0]["displayName"] == "Alice"

    def test_build_event_body_recurrence(self):
        """Recurrence rules are capped at 10."""
        start = datetime(2026, 7, 15, 14, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 7, 15, 15, 0, 0, tzinfo=timezone.utc)

        body = GoogleCalendarApiClient.build_event_body(
            summary="Recurring",
            start=start,
            end=end,
            recurrence=["RRULE:FREQ=WEEKLY;COUNT=5"],
        )

        assert "RRULE:FREQ=WEEKLY;COUNT=5" in body["recurrence"]
        assert body.get("singleEvents") is False


class TestGoogleCalendarAdapterWrite:
    """Test adapter write methods with mocked HTTP client."""

    def setup_method(self):
        self.adapter = GoogleCalendarAdapter(
            access_token="fake-token",
            refresh_token="fake-refresh",
        )
        self.adapter._client = MagicMock(spec=GoogleCalendarApiClient)

    def test_create_event_with_extended_properties(self):
        """create_event includes ExtendedProperties for CRM tracking."""
        self.adapter._client.post.return_value = {
            "id": "google-event-123",
            "summary": "Test Meeting",
            "status": "confirmed",
            "start": {"dateTime": "2026-07-15T14:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2026-07-15T15:00:00Z", "timeZone": "UTC"},
            "htmlLink": "https://calendar.google.com/event?eid=abc",
        }

        result = self.adapter.create_event(
            summary="Test Meeting",
            start=datetime(2026, 7, 15, 14, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 7, 15, 15, 0, 0, tzinfo=timezone.utc),
            source_activity_id="act-123",
            source_entity_type="deal",
            source_entity_id="deal-456",
        )

        assert result.provider_id == "google-event-123"

        call_body = self.adapter._client.post.call_args[1]["body"]
        assert "extendedProperties" in call_body
        ep = call_body["extendedProperties"]["private"]
        assert ep["frontiercrm_activity_id"] == "act-123"
        assert ep["frontiercrm_entity_type"] == "deal"
        assert ep["frontiercrm_entity_id"] == "deal-456"
        assert ep["frontiercrm_source"] == "crm"

    def test_update_event(self):
        """update_event sends PATCH with only changed fields."""
        self.adapter._client.patch.return_value = {
            "id": "google-event-123",
            "summary": "Updated Meeting",
            "status": "confirmed",
            "start": {"dateTime": "2026-07-16T10:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2026-07-16T11:00:00Z", "timeZone": "UTC"},
        }

        result = self.adapter.update_event(
            event_id="google-event-123",
            summary="Updated Meeting",
            start=datetime(2026, 7, 16, 10, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 7, 16, 11, 0, 0, tzinfo=timezone.utc),
        )

        assert result is not None
        assert result.summary == "Updated Meeting"

        call_body = self.adapter._client.patch.call_args[1]["body"]
        assert call_body["summary"] == "Updated Meeting"

    def test_delete_event(self):
        """delete_event returns True on success."""
        self.adapter._client.delete.return_value = {}
        result = self.adapter.delete_event("google-event-123")
        assert result is True

    def test_delete_event_not_found(self):
        """delete_event returns False if event already deleted."""
        from apps.sync.adapters.google_calendar.client import CalendarNotFoundError

        self.adapter._client.delete.side_effect = CalendarNotFoundError("Not found")
        result = self.adapter.delete_event("google-event-123")
        assert result is False


# =============================================================================
# Event Parsing
# =============================================================================


class TestEventParsing:
    """Test _parse_google_event helper."""

    def test_parse_basic_event(self):
        raw = {
            "id": "evt-1",
            "summary": "Team Standup",
            "status": "confirmed",
            "start": {"dateTime": "2026-07-15T09:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2026-07-15T09:30:00Z", "timeZone": "UTC"},
            "htmlLink": "https://calendar.google.com/event?eid=abc",
        }
        event = _parse_google_event(raw)
        assert event is not None
        assert event.provider_id == "evt-1"
        assert event.summary == "Team Standup"
        assert not event.all_day

    def test_parse_all_day_event(self):
        raw = {
            "id": "evt-2",
            "summary": "Holiday",
            "status": "confirmed",
            "start": {"date": "2026-12-25", "timeZone": "UTC"},
            "end": {"date": "2026-12-26", "timeZone": "UTC"},
        }
        event = _parse_google_event(raw)
        assert event is not None
        assert event.all_day is True

    def test_parse_no_id_returns_none(self):
        raw = {"summary": "No ID"}
        event = _parse_google_event(raw)
        assert event is None


# =============================================================================
# Celery Tasks
# =============================================================================


@pytest.mark.django_db
class TestPushCrmEventToCalendar:
    """Test push_crm_event_to_calendar task."""

    def _make_connection(self, user):
        return SyncConnection.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@example.com",
            access_token_encrypted="fake-token",
            refresh_token_encrypted="fake-refresh",
            status="active",
            is_active=True,
            scopes=["https://www.googleapis.com/auth/calendar.events"],
        )

    def _make_activity(self, user, **overrides):
        from apps.activities.models import Activity

        defaults = dict(
            tenant_id=user.tenant_id,
            activity_type=Activity.ActivityType.MEETING,
            title="Test Meeting",
            entity_type="",
            entity_id="00000000-0000-0000-0000-000000000000",
            metadata={"event_source": "crm"},
            actor_id=user.id,
        )
        defaults.update(overrides)
        return Activity.objects.create(**defaults)

    def test_skip_google_sourced(self, user, db):
        """Events with event_source=google are skipped (no push-back)."""
        conn = self._make_connection(user)
        activity = self._make_activity(
            user,
            title="Google Sourced",
            metadata={"event_source": "google", "external_event_id": "evt-1"},
        )
        result = push_crm_event_to_calendar(
            activity_id=str(activity.id),
            connection_id=str(conn.id),
        )
        assert result["skipped"] is True
        assert result["reason"] == "google_sourced"

    @patch("apps.sync.tasks_calendar._get_calendar_adapter")
    @patch("apps.sync.tasks_calendar._refresh_tokens_if_needed", return_value=True)
    @patch("apps.sync.tasks_calendar.push_crm_event_to_calendar.delay")  # Suppress signal eager execution
    def test_create_new_event(self, mock_signal, mock_refresh, mock_adapter_getter, user, db):
        """CRM-originated event creates on Google Calendar."""
        conn = self._make_connection(user)
        mock_adapter = MagicMock()
        mock_adapter.create_event.return_value = CalendarEvent(
            provider_id="new-google-event-1",
            calendar_id="primary",
            summary="New CRM Event",
            html_link="https://calendar.google.com/event?eid=new1",
        )
        mock_adapter_getter.return_value = mock_adapter

        activity = self._make_activity(
            user,
            title="New CRM Event",
            entity_type="deal",
            entity_id="00000000-0000-0000-0000-000000000003",
            metadata={
                "event_source": "crm",
                "start": "2026-07-15T14:00:00+00:00",
                "end": "2026-07-15T15:00:00+00:00",
                "timezone": "UTC",
                "all_day": False,
            },
        )

        result = push_crm_event_to_calendar(
            activity_id=str(activity.id),
            connection_id=str(conn.id),
        )
        assert result["success"] is True
        assert result["external_event_id"] == "new-google-event-1"

        activity.refresh_from_db()
        assert activity.metadata["external_event_id"] == "new-google-event-1"
        assert activity.metadata["html_link"] == "https://calendar.google.com/event?eid=new1"

    @patch("apps.sync.tasks_calendar._get_calendar_adapter")
    @patch("apps.sync.tasks_calendar._refresh_tokens_if_needed", return_value=True)
    @patch("apps.sync.tasks_calendar.push_crm_event_to_calendar.delay")  # Suppress signal eager execution
    def test_update_existing_event(self, mock_signal, mock_refresh, mock_adapter_getter, user, db):
        """Existing event is updated on Google Calendar."""
        conn = self._make_connection(user)
        mock_adapter = MagicMock()
        mock_adapter.update_event.return_value = CalendarEvent(
            provider_id="existing-event-1",
            calendar_id="primary",
            summary="Updated CRM Event",
        )
        mock_adapter_getter.return_value = mock_adapter

        activity = self._make_activity(
            user,
            title="Updated CRM Event",
            metadata={
                "event_source": "crm",
                "external_event_id": "existing-event-1",
                "start": "2026-07-15T14:00:00+00:00",
                "end": "2026-07-15T15:00:00+00:00",
            },
        )

        result = push_crm_event_to_calendar(
            activity_id=str(activity.id),
            connection_id=str(conn.id),
        )
        assert result["success"] is True
        assert result["external_event_id"] == "existing-event-1"
        mock_adapter.update_event.assert_called_once()


# =============================================================================
# CalendarWatchChannel Model
# =============================================================================


@pytest.mark.django_db
class TestCalendarWatchChannelModel:
    """Test CalendarWatchChannel model creation and constraints."""

    def test_create_channel(self, user, db):
        conn = SyncConnection.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@example.com",
            access_token_encrypted="fake-token",
            status="active",
            is_active=True,
        )
        channel = CalendarWatchChannel.objects.create(
            tenant_id=conn.tenant_id,
            connection=conn,
            channel_id="test-channel-1",
            resource_id="resource-1",
            webhook_url="https://example.com/webhook/",
            expires_at=tz.now() + timedelta(days=7),
            state="active",
        )
        assert channel.channel_id == "test-channel-1"
        assert channel.state == "active"

    def test_channel_id_unique(self, user, db):
        conn = SyncConnection.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@example.com",
            access_token_encrypted="fake-token",
            status="active",
            is_active=True,
        )
        CalendarWatchChannel.objects.create(
            tenant_id=conn.tenant_id,
            connection=conn,
            channel_id="unique-channel",
            resource_id="res-1",
            webhook_url="https://example.com/",
            expires_at=tz.now() + timedelta(days=7),
        )
        with pytest.raises(Exception):
            CalendarWatchChannel.objects.create(
                tenant_id=conn.tenant_id,
                connection=conn,
                channel_id="unique-channel",
                resource_id="res-2",
                webhook_url="https://example.com/",
                expires_at=tz.now() + timedelta(days=7),
            )


# =============================================================================
# Signal Handler
# =============================================================================


@pytest.mark.django_db
class TestActivitySignal:
    """Test that Activity post-save signal enqueues push for MEETING events."""

    @patch("apps.sync.tasks_calendar.push_crm_event_to_calendar.delay")
    def test_meeting_created_triggers_push(self, mock_delay, user, db):
        """Creating a MEETING Activity enqueues push_crm_event_to_calendar."""
        SyncConnection.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@example.com",
            access_token_encrypted="fake-token",
            status="active",
            is_active=True,
            scopes=["https://www.googleapis.com/auth/calendar.events"],
        )

        from apps.activities.models import Activity

        activity = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type=Activity.ActivityType.MEETING,
            title="Signal Test Meeting",
            entity_type="",
            entity_id="00000000-0000-0000-0000-000000000000",
            metadata={"event_source": "crm"},
            actor_id=user.id,
        )
        mock_delay.assert_called_once_with(
            activity_id=str(activity.id),
            connection_id=str(SyncConnection.objects.first().id),
        )

    @patch("apps.sync.tasks_calendar.push_crm_event_to_calendar.delay")
    def test_non_meeting_skipped(self, mock_delay, user, db):
        """Non-MEETING activities do not trigger calendar push."""
        from apps.activities.models import Activity

        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type=Activity.ActivityType.NOTE,
            title="A Note",
            entity_type="",
            entity_id="00000000-0000-0000-0000-000000000000",
            metadata={},
            actor_id=user.id,
        )
        mock_delay.assert_not_called()

    @patch("apps.sync.tasks_calendar.push_crm_event_to_calendar.delay")
    def test_google_sourced_meeting_skipped(self, mock_delay, user, db):
        """Google-sourced MEETING activities do not trigger push-back."""
        from apps.activities.models import Activity

        SyncConnection.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@example.com",
            access_token_encrypted="fake-token",
            status="active",
            is_active=True,
            scopes=["https://www.googleapis.com/auth/calendar.events"],
        )
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type=Activity.ActivityType.MEETING,
            title="Google Event",
            entity_type="",
            entity_id="00000000-0000-0000-0000-000000000000",
            metadata={"event_source": "google", "external_event_id": "evt-1"},
            actor_id=user.id,
        )
        mock_delay.assert_not_called()

    @patch("apps.sync.tasks_calendar.push_crm_event_to_calendar.delay")
    def test_no_connection_skipped(self, mock_delay, user, db):
        """No calendar connection means no push."""
        from apps.activities.models import Activity

        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type=Activity.ActivityType.MEETING,
            title="No Connection",
            entity_type="",
            entity_id="00000000-0000-0000-0000-000000000000",
            metadata={"event_source": "crm"},
            actor_id=user.id,
        )
        mock_delay.assert_not_called()


# =============================================================================
# Webhook Receiver
# =============================================================================


@pytest.mark.django_db
class TestWebhookReceiver:
    """Test calendar webhook receiver endpoint."""

    def test_valid_notification(self, user, db):
        """Valid Google push notification enqueues delta sync."""
        conn = SyncConnection.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            provider="google_calendar",
            provider_account="test@example.com",
            access_token_encrypted="fake-token",
            status="active",
            is_active=True,
        )
        CalendarWatchChannel.objects.create(
            tenant_id=conn.tenant_id,
            connection=conn,
            channel_id="webhook-channel-1",
            resource_id="webhook-resource-1",
            webhook_url="https://example.com/webhook/",
            expires_at=tz.now() + timedelta(days=7),
            state="active",
        )

        with patch("apps.sync.tasks_calendar.sync_calendar_for_push_notification.delay") as mock_delay:
            from apps.sync.views import calendar_webhook_receiver
            from rest_framework.test import APIRequestFactory

            factory = APIRequestFactory()
            request = factory.post(
                "/api/sync/calendar/webhook/",
                content_type="application/json",
                **{
                    "HTTP_X_GOOG_CHANNEL_ID": "webhook-channel-1",
                    "HTTP_X_GOOG_RESOURCE_ID": "webhook-resource-1",
                    "HTTP_X_GOOG_RESOURCE_STATE": "exists",
                    "HTTP_X_GOOG_MESSAGE_NUMBER": "42",
                },
            )

            response = calendar_webhook_receiver(request)
            assert response.status_code == 202
            mock_delay.assert_called_once_with(
                connection_id=str(conn.id),
            )

    def test_sync_verification(self, user, db):
        """Google sync verification returns 200."""
        from apps.sync.views import calendar_webhook_receiver
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post(
            "/api/sync/calendar/webhook/",
            content_type="application/json",
            **{
                "HTTP_X_GOOG_CHANNEL_ID": "channel-1",
                "HTTP_X_GOOG_RESOURCE_ID": "resource-1",
                "HTTP_X_GOOG_RESOURCE_STATE": "sync",
            },
        )

        response = calendar_webhook_receiver(request)
        assert response.status_code == 200
        assert response.data["status"] == "channel_verified"

    def test_unknown_channel(self, user, db):
        """Unknown channel returns 200 but does not enqueue sync."""
        from apps.sync.views import calendar_webhook_receiver
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post(
            "/api/sync/calendar/webhook/",
            content_type="application/json",
            **{
                "HTTP_X_GOOG_CHANNEL_ID": "unknown-channel",
                "HTTP_X_GOOG_RESOURCE_ID": "unknown-resource",
                "HTTP_X_GOOG_RESOURCE_STATE": "exists",
            },
        )

        response = calendar_webhook_receiver(request)
        assert response.status_code == 200
        assert response.data["status"] == "unknown_channel"


# =============================================================================
# OAuth Scope Verification
# =============================================================================


class TestScopeVerification:
    """Test verify_calendar_scopes helper."""

    @patch("apps.sync.oauth.requests.get")
    def test_verify_scopes_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "scope": "https://www.googleapis.com/auth/calendar.events "
                     "https://www.googleapis.com/auth/gmail.modify",
        }

        from apps.sync.oauth import verify_calendar_scopes

        scopes = verify_calendar_scopes("fake-token")
        assert "https://www.googleapis.com/auth/calendar.events" in scopes

    @patch("apps.sync.oauth.requests.get")
    def test_verify_scopes_api_error(self, mock_get):
        mock_get.return_value.status_code = 401

        from apps.sync.oauth import verify_calendar_scopes

        scopes = verify_calendar_scopes("bad-token")
        assert scopes == []