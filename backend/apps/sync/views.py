"""DRF serializers and viewsets for the sync engine — connections, OAuth, sync control."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from django.conf import settings
from django.utils import timezone as tz
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.sync.models import CalendarWatchChannel, SyncConnection, SyncState

from .oauth import generate_oauth_url, handle_oauth_callback
from .oauth import (
    generate_calendar_oauth_url,
    handle_calendar_oauth_callback,
)

logger = logging.getLogger(__name__)


# ── Serializers ──────────────────────────────────────────────────────────────


class SyncConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncConnection
        fields = [
            "id", "provider", "provider_account", "account_type",
            "is_active", "status", "last_sync_at", "last_sync_success",
            "last_error_message", "error_count", "sync_interval_seconds",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "provider_account", "is_active",
            "status", "last_sync_at", "last_sync_success",
            "last_error_message", "error_count", "created_at", "updated_at",
        ]


class SyncStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncState
        fields = [
            "id", "sync_type", "provider", "state",
            "last_full_sync_at", "last_delta_sync_at", "next_sync_at",
            "total_synced_count", "total_deleted_count",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "sync_type", "provider", "created_at", "updated_at",
        ]


class OAuthUrlResponseSerializer(serializers.Serializer):
    url = serializers.URLField()
    state = serializers.CharField()


class OAuthCallbackSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    state = serializers.CharField(required=True)


class TriggerSyncSerializer(serializers.Serializer):
    trigger = serializers.CharField(default="manual")


class CalendarAuthStatusSerializer(serializers.Serializer):
    connected = serializers.BooleanField()
    email = serializers.CharField(allow_blank=True)
    last_sync_at = serializers.DateTimeField(allow_null=True)
    last_sync_success = serializers.BooleanField(allow_null=True)
    sync_state = serializers.CharField(allow_blank=True)
    events_count = serializers.IntegerField(default=0)


# ── Viewsets ─────────────────────────────────────────────────────────────────


class SyncConnectionViewSet(viewsets.ModelViewSet):
    """CRUD + OAuth flow + manual sync for sync connections."""

    queryset = SyncConnection.objects.all()
    serializer_class = SyncConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SyncConnection.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, user=self.request.user)

    @action(detail=False, methods=["post"], url_path="gmail/auth-url")
    def gmail_auth_url(self, request: Request) -> Response:
        """Generate Gmail OAuth URL."""
        result = generate_oauth_url()
        return Response(result)

    @action(detail=False, methods=["post"], url_path="gmail/callback")
    def gmail_callback(self, request: Request) -> Response:
        """Handle Gmail OAuth callback."""
        serializer = OAuthCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = handle_oauth_callback(
                code=serializer.validated_data["code"],
                state=serializer.validated_data["state"],
                tenant_id=str(request.user.tenant_id),
                user_id=str(request.user.id),
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def sync(self, request: Request, pk: str | None = None) -> Response:
        """Trigger manual sync for a connection.

        Dispatches to the correct task based on connection.provider:
        - 'gmail' → sync_email_delta
        - 'google_calendar' → sync_calendar_delta
        """
        connection = self.get_object()

        if connection.provider == "google_calendar":
            from apps.sync.tasks_calendar import sync_calendar_delta

            sync_calendar_delta.delay(
                connection_id=str(connection.id),
                trigger="manual",
            )
        else:
            from apps.sync.tasks import sync_email_delta

            sync_email_delta.delay(
                connection_id=str(connection.id),
                trigger="manual",
            )

        return Response({"status": "sync_queued", "connection_id": str(connection.id)})

    @action(detail=True, methods=["post"])
    def disconnect(self, request: Request, pk: str | None = None) -> Response:
        """Disconnect a sync connection."""
        connection = self.get_object()
        connection.is_active = False
        connection.status = "disconnected"
        connection.save(update_fields=["is_active", "status"])
        return Response(self.get_serializer(connection).data)

    # ── Calendar OAuth Actions ─────────────────────────────────────────────

    @action(detail=False, methods=["post"], url_path="calendar/auth-url")
    def calendar_auth_url(self, request: Request) -> Response:
        """Generate Google Calendar OAuth URL."""
        result = generate_calendar_oauth_url()
        return Response(result)

    @action(detail=False, methods=["post"], url_path="calendar/callback")
    def calendar_callback(self, request: Request) -> Response:
        """Handle Google Calendar OAuth callback."""
        serializer = OAuthCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = handle_calendar_oauth_callback(
                code=serializer.validated_data["code"],
                state=serializer.validated_data["state"],
                tenant_id=str(request.user.tenant_id),
                user_id=str(request.user.id),
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="calendar/auth-status")
    def calendar_auth_status(self, request: Request) -> Response:
        """Check Google Calendar auth status.

        Returns whether calendar is connected, last sync info, and event count.
        """
        connection = SyncConnection.objects.filter(
            tenant_id=request.user.tenant_id,
            user=request.user,
            provider="google_calendar",
            is_active=True,
        ).first()

        if not connection:
            return Response({
                "connected": False,
                "email": "",
                "last_sync_at": None,
                "last_sync_success": None,
                "sync_state": "",
                "events_count": 0,
            })

        sync_state = SyncState.objects.filter(
            connection=connection,
            sync_type="calendar_event",
        ).first()

        return Response({
            "connected": True,
            "email": connection.provider_account,
            "last_sync_at": connection.last_sync_at,
            "last_sync_success": connection.last_sync_success,
            "sync_state": sync_state.state if sync_state else "unknown",
            "events_count": sync_state.total_synced_count if sync_state else 0,
        })

    # ── Calendar Event CRUD Proxy Endpoints ───────────────────────────────

    def _get_calendar_connection(self, request: Request) -> SyncConnection:
        """Get the user's active google_calendar connection or raise."""
        conn = SyncConnection.objects.filter(
            tenant_id=request.user.tenant_id,
            user=request.user,
            provider="google_calendar",
            is_active=True,
            status="active",
        ).first()
        if not conn:
            raise ValueError("No active Google Calendar connection")
        # Check write scope
        scopes = conn.scopes or []
        has_write = any("calendar.events" in s and "readonly" not in s for s in scopes)
        if not has_write and getattr(settings, "CALENDAR_WRITE_SCOPE_REQUIRED", True):
            raise PermissionError("requires_upgrade")
        return conn

    @action(detail=False, methods=["post"], url_path="calendar/events")
    def create_calendar_event(self, request: Request) -> Response:
        """Create a calendar event on Google Calendar + Activity record.

        POST /api/sync/calendar/events/
        """
        serializer = CalendarEventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            connection = self._get_calendar_connection(request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError:
            return Response(
                {"error": "Write access required", "requires_upgrade": True},
                status=status.HTTP_403_FORBIDDEN,
            )

        from apps.sync.tasks_calendar import push_crm_event_to_calendar

        data = serializer.validated_data

        # Build activity metadata
        metadata: dict[str, Any] = {
            "event_source": "crm",
            "start": data["start"].isoformat(),
            "end": data["end"].isoformat(),
            "all_day": data.get("all_day", False),
            "timezone": data.get("timezone", "UTC"),
            "status": "confirmed",
        }
        if data.get("location"):
            metadata["location"] = data["location"]
        if data.get("attendees"):
            metadata["attendees"] = data["attendees"]
        if data.get("source_entity_type"):
            metadata["created_from_entity_type"] = data["source_entity_type"]
        if data.get("source_entity_id"):
            metadata["created_from_entity_id"] = str(data["source_entity_id"])
        if data.get("link_to_deal"):
            metadata["deal_ids"] = [str(data["link_to_deal"])]
        if data.get("link_to_contacts"):
            metadata["contact_ids"] = [str(cid) for cid in data["link_to_contacts"]]
        if data.get("remind_before_minutes"):
            metadata["remind_before_minutes"] = data["remind_before_minutes"]

        # Link to entity
        entity_type = data.get("source_entity_type", "")
        entity_id = data.get("source_entity_id") or "00000000-0000-0000-0000-000000000000"

        # Compute duration
        try:
            duration = int((data["end"] - data["start"]).total_seconds() // 60)
        except (TypeError, ValueError):
            duration = None

        from apps.activities.models import Activity

        activity = Activity.objects.create(
            tenant_id=request.user.tenant_id,
            activity_type=Activity.ActivityType.MEETING,
            title=data["summary"][:500],
            description=data.get("description", "")[:5000],
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata,
            actor_id=request.user.id,
            duration_minutes=duration,
        )

        # Enqueue push to Google Calendar (async)
        push_crm_event_to_calendar.delay(
            activity_id=str(activity.id),
            connection_id=str(connection.id),
        )

        return Response(
            _format_event_response(activity),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["put"], url_path="calendar/events/(?P<activity_id>[^/.]+)")
    def update_calendar_event(self, request: Request, activity_id: str) -> Response:
        """Update a calendar event on Google Calendar + Activity record.

        PUT /api/sync/calendar/events/{activity_id}/
        """
        from apps.activities.models import Activity

        try:
            activity = Activity.objects.get(
                id=activity_id,
                tenant_id=request.user.tenant_id,
                activity_type=Activity.ActivityType.MEETING,
            )
        except Activity.DoesNotExist:
            return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            connection = self._get_calendar_connection(request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError:
            return Response(
                {"error": "Write access required", "requires_upgrade": True},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CalendarEventUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Update activity fields
        changed = False
        if data.get("summary") is not None:
            activity.title = data["summary"][:500]
            changed = True
        if data.get("description") is not None:
            activity.description = data["description"][:5000]
            changed = True

        # Update metadata
        metadata = dict(activity.metadata or {})
        if data.get("start"):
            metadata["start"] = data["start"].isoformat()
            changed = True
        if data.get("end"):
            metadata["end"] = data["end"].isoformat()
            changed = True
        if data.get("location") is not None:
            metadata["location"] = data["location"]
            changed = True
        if data.get("timezone") is not None:
            metadata["timezone"] = data["timezone"]
            changed = True
        if data.get("all_day") is not None:
            metadata["all_day"] = data["all_day"]
            changed = True
        if data.get("attendees") is not None:
            metadata["attendees"] = data["attendees"]
            changed = True

        if changed:
            activity.metadata = metadata
            # Recompute duration
            if data.get("start") and data.get("end"):
                try:
                    activity.duration_minutes = int(
                        (data["end"] - data["start"]).total_seconds() // 60
                    )
                except (TypeError, ValueError):
                    pass
            activity.save()

        # Enqueue push to Google Calendar
        from apps.sync.tasks_calendar import push_crm_event_to_calendar

        push_crm_event_to_calendar.delay(
            activity_id=str(activity.id),
            connection_id=str(connection.id),
        )

        return Response(_format_event_response(activity))

    @action(detail=False, methods=["delete"], url_path="calendar/events/(?P<activity_id>[^/.]+)")
    def delete_calendar_event(self, request: Request, activity_id: str) -> Response:
        """Delete a calendar event on Google Calendar + Activity record.

        DELETE /api/sync/calendar/events/{activity_id}/
        """
        from apps.activities.models import Activity

        try:
            activity = Activity.objects.get(
                id=activity_id,
                tenant_id=request.user.tenant_id,
                activity_type=Activity.ActivityType.MEETING,
            )
        except Activity.DoesNotExist:
            return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            connection = self._get_calendar_connection(request)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError:
            return Response(
                {"error": "Write access required", "requires_upgrade": True},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Delete from Google Calendar
        external_event_id = (activity.metadata or {}).get("external_event_id")
        if external_event_id:
            from apps.sync.adapters.google_calendar.adapter import GoogleCalendarAdapter

            adapter = GoogleCalendarAdapter(
                access_token=connection.access_token_encrypted,
                refresh_token=connection.refresh_token_encrypted or None,
            )
            try:
                deleted = adapter.delete_event(external_event_id)
            except Exception as e:
                logger.warning("Failed to delete event %s on Google: %s", external_event_id, e)
                deleted = False
        else:
            deleted = True

        # Soft-delete the activity by updating metadata
        activity.metadata = {
            **(activity.metadata or {}),
            "status": "cancelled",
            "deleted_at": tz.now().isoformat(),
        }
        activity.save(update_fields=["metadata"])

        status_code = status.HTTP_204_NO_CONTENT if deleted else status.HTTP_409_CONFLICT
        return Response(status=status_code)

    # ── Calendar Scope Upgrade ────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="calendar/upgrade-scope")
    def upgrade_calendar_scope(self, request: Request, pk: str | None = None) -> Response:
        """Generate an OAuth URL to upgrade calendar scope to read-write.

        POST /api/sync/connections/{id}/calendar/upgrade-scope/
        """
        connection = self.get_object()
        if connection.provider != "google_calendar":
            return Response(
                {"error": "Not a Google Calendar connection"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = generate_calendar_oauth_url()
        return Response({
            "url": result["url"],
            "state": result["state"],
            "connection_id": str(connection.id),
        })

    # ── Calendar Watch Status ─────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="calendar/watch-status")
    def calendar_watch_status(self, request: Request) -> Response:
        """Get push notification status for the user's calendar connection.

        GET /api/sync/calendar/watch-status/
        """
        connection = SyncConnection.objects.filter(
            tenant_id=request.user.tenant_id,
            user=request.user,
            provider="google_calendar",
            is_active=True,
        ).first()

        if not connection:
            return Response({
                "connected": False,
                "push_enabled": False,
            })

        watch_channel = CalendarWatchChannel.objects.filter(
            connection=connection,
            state="active",
        ).first()

        if watch_channel:
            push_healthy = (
                watch_channel.last_push_at
                and watch_channel.last_push_at >= tz.now() - tz.timedelta(minutes=30)
            )
            return Response({
                "connected": True,
                "push_enabled": True,
                "watch_channel_id": watch_channel.channel_id,
                "watch_expires_at": watch_channel.expires_at.isoformat() if watch_channel.expires_at else None,
                "last_push_received_at": watch_channel.last_push_at.isoformat() if watch_channel.last_push_at else None,
                "fallback_polling_active": not push_healthy,
            })

        return Response({
            "connected": True,
            "push_enabled": False,
            "fallback_polling_active": True,
        })


class SyncStateViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for sync states."""

    queryset = SyncState.objects.all()
    serializer_class = SyncStateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SyncState.objects.filter(tenant_id=self.request.user.tenant_id)


# ── Calendar Webhook Receiver (public endpoint) ──────────────────────────────


@api_view(["POST"])
@permission_classes([AllowAny])
def calendar_webhook_receiver(request: Request) -> Response:
    """Receive Google Calendar push notifications.

    Public endpoint at POST /api/sync/calendar/webhook/.
    Authenticated by Google's X-Goog-Channel-ID and X-Goog-Resource-ID headers.
    """
    channel_id = request.headers.get("X-Goog-Channel-ID", "")
    resource_id = request.headers.get("X-Goog-Resource-ID", "")
    resource_state = request.headers.get("X-Goog-Resource-State", "")
    message_number = request.headers.get("X-Goog-Message-Number", "")

    # Handle Google's sync verification notification
    if resource_state == "sync":
        return Response({"status": "channel_verified"}, status=status.HTTP_200_OK)

    # Find the matching watch channel
    try:
        channel = CalendarWatchChannel.objects.get(
            channel_id=channel_id,
            resource_id=resource_id,
            state="active",
        )
        channel.last_push_at = tz.now()
        channel.last_message_number = message_number
        channel.save(update_fields=["last_push_at", "last_message_number"])

        # Enqueue delta sync for this connection
        from apps.sync.tasks_calendar import sync_calendar_for_push_notification

        sync_calendar_for_push_notification.delay(
            connection_id=str(channel.connection_id),
        )

        return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)

    except CalendarWatchChannel.DoesNotExist:
        logger.warning("Received notification for unknown channel %s", channel_id)
        return Response({"status": "unknown_channel"}, status=status.HTTP_200_OK)


# ── Calendar Event Serializers ────────────────────────────────────────────────


class CalendarEventCreateSerializer(serializers.Serializer):
    summary = serializers.CharField(max_length=500, required=True)
    start = serializers.DateTimeField(required=True)
    end = serializers.DateTimeField(required=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    location = serializers.CharField(required=False, allow_blank=True, default="")
    timezone = serializers.CharField(required=False, default="UTC")
    all_day = serializers.BooleanField(required=False, default=False)
    attendees = serializers.ListField(
        child=serializers.DictField(), required=False, default=list,
    )
    source_entity_type = serializers.CharField(required=False, allow_blank=True, default="")
    source_entity_id = serializers.UUIDField(required=False, allow_null=True)
    link_to_contacts = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list,
    )
    link_to_deal = serializers.UUIDField(required=False, allow_null=True)
    remind_before_minutes = serializers.IntegerField(required=False, default=15)


class CalendarEventUpdateSerializer(serializers.Serializer):
    summary = serializers.CharField(max_length=500, required=False)
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    timezone = serializers.CharField(required=False)
    all_day = serializers.BooleanField(required=False)
    attendees = serializers.ListField(child=serializers.DictField(), required=False)


# ── Calendar Event Response Formatter ────────────────────────────────────────


def _format_event_response(activity: Any) -> dict[str, Any]:
    """Format an Activity as a calendar event response."""
    metadata = activity.metadata or {}
    return {
        "id": str(activity.id),
        "external_event_id": metadata.get("external_event_id", ""),
        "html_link": metadata.get("html_link", ""),
        "summary": activity.title,
        "start": metadata.get("start"),
        "end": metadata.get("end"),
        "status": metadata.get("status", "confirmed"),
    }