"""DRF serializers and viewsets for the sync engine — connections, OAuth, sync control."""
from __future__ import annotations

from typing import Any

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.sync.models import SyncConnection, SyncState

from .oauth import generate_oauth_url, handle_oauth_callback


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
        """Trigger manual sync for a connection."""
        connection = self.get_object()

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


class SyncStateViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for sync states."""

    queryset = SyncState.objects.all()
    serializer_class = SyncStateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SyncState.objects.filter(tenant_id=self.request.user.tenant_id)