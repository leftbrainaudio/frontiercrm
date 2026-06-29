"""Webhook hub: receiver, signature verification, retry with backoff."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import requests
from celery import shared_task
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .models import WebhookEndpoint, WebhookEvent

# ── API ──────────────────────────────────────────────────────────────────────


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


# ── Webhook receiver (public) ────────────────────────────────────────────────


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
            expected_sig = _compute_signature(payload, endpoint.secret, timestamp)
            if not hmac.compare_digest(signature, expected_sig):
                continue  # skip — signature mismatch

        event = WebhookEvent.objects.create(
            tenant_id=endpoint.tenant_id,
            endpoint=endpoint,
            event_type=event_type,
            payload=payload,
        )
        dispatch_webhook.delay(event.id)

    return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def dispatch_webhook(self, event_id: str) -> None:
    """Deliver webhook event with exponential backoff retry."""
    try:
        event = WebhookEvent.objects.get(id=event_id)
    except WebhookEvent.DoesNotExist:
        return

    endpoint = event.endpoint
    event.attempt_count += 1
    event.last_attempt_at = __import__("django.utils.timezone", fromlist=["now"]).now()

    try:
        resp = requests.post(
            endpoint.url,
            json=event.payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": _compute_signature(event.payload, endpoint.secret, str(int(time.time()))),
                "User-Agent": "FrontierCRM-Webhook/1.0",
            },
            timeout=30,
        )
        event.response_status = resp.status_code
        event.response_body = resp.text[:2000]

        if 200 <= resp.status_code < 300:
            event.status = WebhookEvent.EventStatus.DELIVERED
            endpoint.last_triggered_at = event.last_attempt_at
            endpoint.failure_count = 0
            endpoint.save(update_fields=["last_triggered_at", "failure_count"])
        else:
            _retry_or_fail(self, event, endpoint, f"HTTP {resp.status_code}: {resp.text[:200]}")

    except requests.RequestException as exc:
        _retry_or_fail(self, event, endpoint, str(exc))

    event.save()


def _retry_or_fail(task: Any, event: WebhookEvent, endpoint: WebhookEndpoint, error: str) -> None:
    """Retry with backoff or mark as failed."""
    event.error_message = error
    if event.attempt_count < endpoint.max_retries:
        event.status = WebhookEvent.EventStatus.PENDING
        delay = 60 * (2 ** (event.attempt_count - 1))  # 60s, 120s, 240s
        event.next_retry_at = __import__("django.utils.timezone", fromlist=["now"]).now() + __import__(
            "datetime", fromlist=["timedelta"]
        ).timedelta(seconds=delay)
        task.retry(countdown=delay)
    else:
        event.status = WebhookEvent.EventStatus.FAILED
        endpoint.failure_count += 1
        endpoint.save(update_fields=["failure_count"])


def _compute_signature(payload: dict[str, Any], secret: str, timestamp: str) -> str:
    """HMAC-SHA256 signature of payload + timestamp."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    message = f"{timestamp}.{raw}"
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
