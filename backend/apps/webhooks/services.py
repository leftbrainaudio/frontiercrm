"""Outbound webhook delivery service — manages delivery, retry, and dead-letter."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import timedelta
from typing import Any

import requests
from django.utils import timezone

from apps.webhooks.models import WebhookDeadEvent, WebhookEndpoint, WebhookEvent

# Default timeout for webhook delivery HTTP calls
WEBHOOK_TIMEOUT_SECONDS = 30
# Max response body bytes to store
MAX_RESPONSE_BODY_LENGTH = 2000
# User-Agent header for all outbound webhooks
USER_AGENT = "FrontierCRM-Webhook/1.0"


class WebhookDeliveryError(Exception):
    """Raised when a webhook delivery fails unrecoverably."""


class WebhookDeliveryService:
    """Orchestrates outbound webhook delivery with retry and dead-letter."""

    def __init__(self, http_client: Any = None):
        """Allow injecting a mock HTTP client for testing."""
        self.http_client = http_client or requests

    # ── Public API ────────────────────────────────────────────────────────────

    @classmethod
    def enqueue(
        cls, endpoint: WebhookEndpoint, event_type: str, payload: dict[str, Any]
    ) -> WebhookEvent:
        """Create a WebhookEvent and return it for async delivery.

        Call this from signal handlers and API endpoints to fire a webhook.
        Does NOT deliver synchronously — callers should .delay() the Celery task.
        """
        event = WebhookEvent.objects.create(
            tenant_id=endpoint.tenant_id,
            endpoint=endpoint,
            event_type=event_type,
            payload=payload,
        )
        return event

    def deliver(self, event: WebhookEvent) -> dict[str, Any]:
        """Deliver a single webhook event. May retry or move to dead-letter.

        Returns a result dict with:
            status: "delivered" | "retrying" | "dead_letter"
            http_status: int | None
            error: str | None
        """
        event.attempt_count += 1
        event.last_attempt_at = timezone.now()
        endpoint: WebhookEndpoint = event.endpoint

        # Enrich payload at delivery time (event_id is available now)
        enriched_payload = self._build_enriched_payload(event)

        try:
            resp = self.http_client.post(
                endpoint.url,
                json=enriched_payload,
                headers=self._build_headers(endpoint, enriched_payload),
                timeout=WEBHOOK_TIMEOUT_SECONDS,
            )

            event.response_status = resp.status_code
            event.response_body = resp.text[:MAX_RESPONSE_BODY_LENGTH]

            if 200 <= resp.status_code < 300:
                return self._handle_success(event, endpoint)
            else:
                return self._handle_failure(
                    event,
                    endpoint,
                    f"HTTP {resp.status_code}: {resp.text[:200]}",
                )

        except requests.Timeout:
            return self._handle_failure(event, endpoint, "Request timed out")
        except requests.ConnectionError:
            return self._handle_failure(event, endpoint, "Connection error")
        except requests.RequestException as exc:
            return self._handle_failure(event, endpoint, str(exc))
        finally:
            event.save()

    # ── Internal: success / failure / dead-letter ────────────────────────────

    def _handle_success(
        self, event: WebhookEvent, endpoint: WebhookEndpoint
    ) -> dict[str, Any]:
        """Mark event as delivered and reset endpoint health."""
        event.status = WebhookEvent.EventStatus.DELIVERED
        event.next_retry_at = None
        endpoint.last_triggered_at = event.last_attempt_at
        endpoint.failure_count = 0
        endpoint.save(update_fields=["last_triggered_at", "failure_count"])
        return {"status": "delivered", "http_status": event.response_status}

    def _handle_failure(
        self,
        event: WebhookEvent,
        endpoint: WebhookEndpoint,
        error: str,
    ) -> dict[str, Any]:
        """Retry with backoff or move to dead-letter queue."""
        event.error_message = error

        if event.attempt_count < endpoint.max_retries:
            delay_seconds = self._backoff_delay(event.attempt_count)
            event.status = WebhookEvent.EventStatus.PENDING
            event.next_retry_at = timezone.now() + timedelta(seconds=delay_seconds)
            return {
                "status": "retrying",
                "http_status": event.response_status,
                "error": error,
            }

        # Exhausted retries — dead-letter
        event.status = WebhookEvent.EventStatus.FAILED
        event.next_retry_at = None
        endpoint.failure_count += 1
        endpoint.save(update_fields=["failure_count"])

        # Create dead-letter record
        WebhookDeadEvent.objects.create(
            tenant_id=endpoint.tenant_id,
            endpoint=endpoint,
            original_event=event,
            event_type=event.event_type,
            payload=event.payload,
            final_attempt_count=event.attempt_count,
            last_error=error,
            last_response_status=event.response_status,
            last_response_body=event.response_body,
        )

        return {
            "status": "dead_letter",
            "http_status": event.response_status,
            "error": error,
        }

    @staticmethod
    def _backoff_delay(attempt_count: int) -> int:
        """Calculate exponential backoff delay in seconds.

        attempt 1 -> 60s
        attempt 2 -> 120s
        attempt 3 -> 240s
        attempt 4+ -> 600s (cap)
        """
        delay = 60 * (2 ** (attempt_count - 1))
        return min(delay, 600)

    @staticmethod
    def _build_headers(
        endpoint: WebhookEndpoint, payload: dict[str, Any]
    ) -> dict[str, str]:
        """Build HTTP headers including HMAC signature."""
        timestamp = str(int(time.time()))
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-FrontierCRM-Event": payload.get("event_type", "unknown"),
            "X-FrontierCRM-Timestamp": timestamp,
            "X-FrontierCRM-Signature-256": compute_signature(
                payload, endpoint.secret, timestamp
            ),
        }
        return headers

    @staticmethod
    def _build_enriched_payload(event: WebhookEvent) -> dict[str, Any]:
        """Wrap the raw event payload in the standard delivery envelope.

        Every outbound webhook payload gets:
          - event_type: the event type string
          - event_id: the WebhookEvent UUID (for dedup by consumer)
          - tenant_id: the tenant UUID
          - timestamp: ISO-8601 UTC timestamp
          - data: the original event payload
        """
        return {
            "event_type": event.event_type,
            "event_id": str(event.id),
            "tenant_id": str(event.tenant_id),
            "timestamp": timezone.now().isoformat(),
            "data": event.payload,
        }


def compute_signature(payload: dict[str, Any], secret: str, timestamp: str) -> str:
    """HMAC-SHA256 signature of payload + timestamp.

    Consumers verify by:
      1. Extract X-FrontierCRM-Timestamp from headers
      2. Recompute HMAC-SHA256(timestamp + canonical_json(payload), secret)
      3. Compare with X-FrontierCRM-Signature-256 using constant-time comparison

    Canonical JSON: sorted keys, no whitespace separators.
    """
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    message = f"{timestamp}.{raw}"
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
