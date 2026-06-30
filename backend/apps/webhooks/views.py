"""Webhook hub: receiver, API viewsets, and dead-event replay."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import requests
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.webhooks.models import WebhookDeadEvent, WebhookEndpoint, WebhookEvent
from apps.webhooks.services import WebhookDeliveryService, compute_signature

# ── Serializers ─────────────────────────────────────────────────────────────

class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        exclude = ()
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at", "last_triggered_at", "failure_count")


class WebhookEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEvent
        exclude = ()
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


class WebhookDeadEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDeadEvent
        exclude = ()
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


# ── ViewSets ────────────────────────────────────────────────────────────────


class WebhookEndpointViewSet(viewsets.ModelViewSet):
    queryset = WebhookEndpoint.objects.all()
    serializer_class = WebhookEndpointSerializer

    def get_queryset(self):
        return WebhookEndpoint.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)


class WebhookEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WebhookEvent.objects.all()
    serializer_class = WebhookEventSerializer
    filterset_fields = ["event_type", "status", "endpoint"]

    def get_queryset(self):
        return WebhookEvent.objects.filter(tenant_id=self.request.user.tenant_id)


class WebhookDeadEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WebhookDeadEvent.objects.all()
    serializer_class = WebhookDeadEventSerializer
    filterset_fields = ["event_type", "endpoint", "resolved_at"]

    def get_queryset(self):
        return WebhookDeadEvent.objects.filter(tenant_id=self.request.user.tenant_id)

    @action(detail=True, methods=["post"])
    def replay(self, request: Request, pk=None):
        """Replay a dead-letter event as a fresh webhook delivery."""
        dead_event = self.get_object()

        if dead_event.resolved_at is not None and dead_event.resolution_notes != "Replayed via admin action":
            return Response(
                {"error": "Dead event is already resolved"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            event = WebhookDeliveryService.enqueue(
                dead_event.endpoint,
                dead_event.event_type,
                dead_event.payload,
            )
            from apps.webhooks.tasks import deliver_webhook

            deliver_webhook.delay(str(event.id))

            # Mark dead event as resolved
            from django.utils import timezone
            dead_event.resolved_at = timezone.now()
            dead_event.resolution_notes = "Replayed via API"
            dead_event.save(update_fields=["resolved_at", "resolution_notes"])

            return Response(
                {
                    "new_event_id": str(event.id),
                    "status": "pending",
                    "message": "Webhook event re-queued for delivery",
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return Response(
                {"error": f"Failed to replay dead event: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ── Webhook receiver (public, inbound) ──────────────────────────────────────


@api_view(["POST"])
@permission_classes([AllowAny])
def webhook_receiver(request: Request) -> Response:
    """Single public endpoint that receives webhook payloads.

    Verifies signature if present, then dispatches to subscribed endpoints.
    """
    payload = request.data
    event_type = payload.get("event_type", "unknown")
    signature = request.META.get("HTTP_X_WEBHOOK_SIGNATURE", "")
    timestamp = request.META.get("HTTP_X_WEBHOOK_TIMESTAMP", "")

    # Find matching endpoints — iterate in-memory for SQLite compat
    active_endpoints = WebhookEndpoint.objects.filter(
        is_active=True,
    )
    endpoints = [
        ep for ep in active_endpoints
        if event_type in ep.events
    ]

    if not endpoints:
        return Response({"status": "no_subscribers"}, status=status.HTTP_200_OK)

    for endpoint in endpoints:
        # Verify signature if endpoint has a secret
        if endpoint.secret and signature:
            expected_sig = compute_signature(payload, endpoint.secret, timestamp)
            if not hmac.compare_digest(signature, expected_sig):
                continue  # skip — signature mismatch

        event = WebhookEvent.objects.create(
            tenant_id=endpoint.tenant_id,
            endpoint=endpoint,
            event_type=event_type,
            payload=payload,
        )
        from apps.webhooks.tasks import deliver_webhook

        deliver_webhook.delay(event.id)

    return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)
