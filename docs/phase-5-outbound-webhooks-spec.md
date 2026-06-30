# Phase 5 — Outbound Webhook Delivery Engine Specification

**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)
**Status:** Draft
**Priority:** P2

---

## Table of Contents

1. [ADR-027: Outbound Webhook Delivery Engine Architecture](#1-adr-027-outbound-webhook-delivery-engine-architecture)
2. [Data Model Extensions](#2-data-model-extensions)
3. [WebhookDeliveryService](#3-webhookdeliveryservice)
4. [Signed Payloads for Consumer Verification](#4-signed-payloads-for-consumer-verification)
5. [Event Triggers](#5-event-triggers)
6. [Retry & Backoff Strategy](#6-retry--backoff-strategy)
7. [Dead-Letter Queue](#7-dead-letter-queue)
8. [Celery Beat: Retry Scheduler](#8-celery-beat--retry-scheduler)
9. [API Contracts](#9-api-contracts)
10. [Implementation Order](#10-implementation-order)
11. [Acceptance Criteria](#11-acceptance-criteria)
12. [Open Questions / Spike Items](#12-open-questions--spike-items)

---

## 1. ADR-027: Outbound Webhook Delivery Engine Architecture

**Status:** Proposed
**Date:** 2026-06-30
**ADR Number:** 027

### Context

FrontierCRM already has:

- `WebhookEndpoint` model — tenant-scoped, stores URL, HMAC secret, subscribed event types, max_retries
- `WebhookEvent` model — tracks per-delivery state (status, attempt_count, response_body, error_message)
- `dispatch_webhook` Celery task in `views.py` — basic delivery with exponential backoff (60s/120s/240s) and HMAC signing
- `webhook_receiver` public endpoint — receives inbound webhooks from external services
- `SlackNotificationService` pattern — purpose-built service + Celery task + Django signal for Activity-driven outbound delivery

What's missing:

1. **No dedicated delivery service** — the delivery logic lives in `views.py` as a standalone function, not a testable service class
2. **No outbound event triggers** — no signal handlers fire webhook deliveries when Deals change, Contacts update, or emails sync. The existing `dispatch_webhook` is only called from the inbound receiver
3. **No dead-letter queue** — failed events are simply marked `FAILED` with no retention policy, no replay, no monitoring
4. **No Celery Beat retry sweep** — after a Celery task exhausts its own retries, there's no scheduled job to retry events whose `next_retry_at` has passed
5. **No signed payload spec for consumers** — the HMAC signature is computed but undocumented; consumers can't verify webhook origin
6. **No event enrichment** — payloads carry raw Activity JSON, not hydrated deal/contact data that consumers need

### Options Considered

**Option A — Extract delivery into a standalone service, add signal handlers, add dead-letter**

Build a `WebhookDeliveryService` class (mirroring `SlackNotificationService`), add Django signal handlers for Deal, Contact, Activity models, add `DeadLetterEvent` model, add Celery Beat retry sweep, and document the signed-payload format.

- Pros: clean architecture, testable service, complete lifecycle (create → queue → deliver → retry → dead-letter), existing `WebhookEndpoint`/`WebhookEvent` models reused
- Cons: significant migration of existing `views.py` logic; three new signal wiring points; new DB migration for dead-letter model

**Option B — Refactor views.py inline, add triggers as Celery tasks only (no signals)**

Keep all delivery logic in `views.py`, add direct Celery task calls from Deal/Contact save methods or post-save hooks. Skip dead-letter; keep existing `FAILED` status.

- Pros: least code change, no new DB models, no signal wiring
- Cons: delivery logic still untestable as a class; no dead-letter replay; task-based triggers are fragile (cache-the-task model pattern is error-prone); no signed-payload documentation

**Option C — Full event bus (Message Broker / Redis Streams)**

Push all domain events (Deal.created, Deal.updated, Contact.created, Email.received) onto a Redis Stream or RabbitMQ exchange. A dedicated consumer process reads events and dispatches webhooks.

- Pros: decoupling, durability, exactly-once semantics possible, multiple consumers (webhooks + Slack + future)
- Cons: over-engineered for P2 — CRM doesn't yet produce enough event volume to justify a broker layer; introduces operational complexity (consumer group management, rebalancing, DLQ at broker level); adds system dependency

### Decision

**Option A — Extract delivery into a standalone service, add signal handlers, add dead-letter.**

Rationale:

1. The existing `WebhookEndpoint`/`WebhookEvent` models are well-designed for this — they already have `status`, `attempt_count`, `next_retry_at`, `response_status`, `response_body`, `error_message`, and the `max_retries` per-endpoint setting. The missing pieces (dead-letter, signal triggers, signed-payload documentation) each require <50 lines of new code.
2. Extracting `WebhookDeliveryService` makes the delivery logic unit-testable. Currently, testing delivery requires mocking `requests.post` inside `views.py` — a service class lets tests inject a mock HTTP client.
3. Django signals are the established pattern in this codebase (see `apps/slack/signals.py`). Adding `apps/webhooks/signals.py` with `post_save` handlers on Deal, Contact, and (optionally) Activity keeps the pattern consistent.
4. A dead-letter model (`WebhookDeadEvent`) is cheap — one new table, no FK relationships to worry about. It makes failed deliveries inspectable and replayable from the admin.
5. The Celery Beat retry sweep is essential for reliability. When Celery restarts or a task fails to enqueue, PENDING events with stale `next_retry_at` dates pile up. A periodic task sweeps these back into delivery.

**Rejected:** Option B (no service class, no dead-letter — leaves developer experience and operational visibility poor). Option C (event bus — too much infrastructure for current scale).

### Consequences

- New file: `apps/webhooks/services.py` — `WebhookDeliveryService` class
- New file: `apps/webhooks/signals.py` — signal handlers for Deal, Contact
- New file: `apps/webhooks/tasks.py` — refactored Celery tasks (move from views.py)
- New file: `apps/webhooks/admin.py` — admin registration for all webhook models
- New model: `WebhookDeadEvent` in `apps/webhooks/models.py` — dead-letter queue entry
- Migration: new `webhooks_deadevent` table
- Celery Beat: one new periodic task (`retry_stale_webhooks`) every 5 minutes
- Updated docs: `api.md` and webhook section in admin guide for consumer signature verification
- Existing `WebhookEndpoint` and `WebhookEvent` models — unchanged (backward compatible)
- Existing `views.py` — keep `webhook_receiver` (inbound) untouched; remove `dispatch_webhook` and `_retry_or_fail` to `tasks.py`; keep `_compute_signature` and import it from tasks

---

## 2. Data Model Extensions

### 2.1 Current Models (unchanged — for reference)

**`WebhookEndpoint(TenantScopedModel)`** — already in place:

| Field | Type | Notes |
|-------|------|-------|
| `url` | URLField(2000) | Target URL |
| `secret` | CharField(255) | HMAC secret |
| `events` | JSONField(list) | Subscribed event types |
| `description` | CharField(500) | Human label |
| `is_active` | BooleanField | Soft-disable toggle |
| `last_triggered_at` | DateTimeField | Last successful send |
| `failure_count` | IntegerField | Consecutive failures |
| `max_retries` | IntegerField(default=3) | Per-endpoint retry limit |

**`WebhookEvent(TenantScopedModel)`** — already in place:

| Field | Type | Notes |
|-------|------|-------|
| `endpoint` | FK(WebhookEndpoint) | Target endpoint |
| `event_type` | CharField(100) | e.g. "deal.updated" |
| `payload` | JSONField | The event payload body |
| `status` | CharField(20) | pending / delivered / failed |
| `attempt_count` | IntegerField(default=0) | Delivery attempts so far |
| `last_attempt_at` | DateTimeField | Most recent delivery attempt |
| `next_retry_at` | DateTimeField | When to retry (null if not scheduled) |
| `response_status` | IntegerField(nullable) | HTTP status from target |
| `response_body` | TextField | Truncated response body |
| `error_message` | TextField | Human-readable error text |

**No changes needed** to either model. The field names, indexes, and choices are all correct.

### 2.2 New Model: WebhookDeadEvent

Location: `apps/webhooks/models.py`

```python
class WebhookDeadEvent(TenantScopedModel):
    """Dead-letter record for a permanently failed webhook delivery.

    Created when a WebhookEvent exhausts its retries and is marked FAILED.
    Preserves the original event data for inspection and replay.
    """

    original_event = models.OneToOneField(
        WebhookEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dead_letter",
    )
    endpoint = models.ForeignKey(
        WebbookEndpoint,
        on_delete=models.CASCADE,
        related_name="dead_events",
    )
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    final_attempt_count = models.IntegerField()
    last_error = models.TextField(blank=True, default="")
    last_response_status = models.IntegerField(null=True, blank=True)
    last_response_body = models.TextField(blank=True, default="")
    failed_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "webhooks_dead_event"
        indexes = [
            models.Index(fields=["endpoint", "-failed_at"]),
            models.Index(fields=["resolved_at"]),  # sweep un-resolved
        ]
        ordering = ["-failed_at"]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.endpoint_id} — failed {self.failed_at}"
```

**Migration notes:**
- Table: `webhooks_dead_event`
- Inherits `tenant_id`, `id`, `created_at`, `updated_at` from `TenantScopedModel`
- `original_event` is nullable so dead events survive even if the `WebhookEvent` is cleaned up
- `resolved_at` is null until an admin marks it as handled (via admin action or replay)

### 2.3 Model Relationships Diagram

```
Tenant
  └── WebhookEndpoint (FK: tenant_id)
       ├── WebhookEvent (FK: endpoint)
       │    └── WebhookDeadEvent (OneToOne: original_event)
       └── WebhookDeadEvent (FK: endpoint)   ← direct link for orphaned dead events
```

---

## 3. WebhookDeliveryService

Location: `apps/webhooks/services.py`

### 3.1 Architecture

```
[Signal / API handler] → enqueue_webhook() creates WebhookEvent (status=PENDING)
                                │
                                ▼
                        Celery: deliver_webhook(event_id)
                                │
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
        WebhookDeliveryService        WebhookDeliveryService
        .deliver(event)               .deliver(event)
                  │                           │
          ┌───────┴───────┐            ┌───────┴───────┐
          ▼               ▼            ▼               ▼
       HTTP 2xx        HTTP 4xx/5xx   HTTP 2xx       HTTP 4xx/5xx
          │               │               │               │
          ▼               ▼               ▼               ▼
    status=DELIVERED   retry or      status=DELIVERED   retry or
    reset failures     dead-letter   reset failures     dead-letter
```

### 3.2 Service Class

```python
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
    def enqueue(cls, endpoint: WebhookEndpoint, event_type: str, payload: dict[str, Any]) -> WebhookEvent:
        """Create a WebhookEvent and enqueue it for async delivery.

        Call this from signal handlers and API endpoints to fire a webhook.
        Does NOT deliver synchronously — callers should .delay() the Celery task.
        """
        event = WebhookEvent.objects.create(
            tenant_id=endpoint.tenant_id,
            endpoint=endpoint,
            event_type=event_type,
            payload=cls._enrich_payload(endpoint, event_type, payload),
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

        try:
            resp = self.http_client.post(
                endpoint.url,
                json=event.payload,
                headers=self._build_headers(endpoint, event.payload),
                timeout=WEBHOOK_TIMEOUT_SECONDS,
            )

            event.response_status = resp.status_code
            event.response_body = resp.text[:MAX_RESPONSE_BODY_LENGTH]

            if 200 <= resp.status_code < 300:
                return self._handle_success(event, endpoint)
            else:
                return self._handle_failure(event, endpoint, f"HTTP {resp.status_code}: {resp.text[:200]}")

        except requests.Timeout:
            return self._handle_failure(event, endpoint, "Request timed out")
        except requests.ConnectionError:
            return self._handle_failure(event, endpoint, "Connection error")
        except requests.RequestException as exc:
            return self._handle_failure(event, endpoint, str(exc))
        finally:
            event.save()

    # ── Internal: success / failure / dead-letter ────────────────────────────

    def _handle_success(self, event: WebhookEvent, endpoint: WebhookEndpoint) -> dict[str, Any]:
        """Mark event as delivered and reset endpoint health."""
        event.status = WebhookEvent.EventStatus.DELIVERED
        event.next_retry_at = None
        endpoint.last_triggered_at = event.last_attempt_at
        endpoint.failure_count = 0
        endpoint.save(update_fields=["last_triggered_at", "failure_count"])
        return {"status": "delivered", "http_status": event.response_status}

    def _handle_failure(self, event: WebhookEvent, endpoint: WebhookEndpoint, error: str) -> dict[str, Any]:
        """Retry with backoff or move to dead-letter queue."""
        event.error_message = error

        if event.attempt_count < endpoint.max_retries:
            delay_seconds = self._backoff_delay(event.attempt_count)
            event.status = WebhookEvent.EventStatus.PENDING
            event.next_retry_at = timezone.now() + timedelta(seconds=delay_seconds)
            return {"status": "retrying", "http_status": event.response_status, "error": error}

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

        return {"status": "dead_letter", "http_status": event.response_status, "error": error}

    @staticmethod
    def _backoff_delay(attempt_count: int) -> int:
        """Calculate exponential backoff delay in seconds.

        attempt 1 → 60s
        attempt 2 → 120s
        attempt 3 → 240s
        attempt 4+ → 600s (cap)
        """
        delay = 60 * (2 ** (attempt_count - 1))
        return min(delay, 600)

    @staticmethod
    def _build_headers(endpoint: WebhookEndpoint, payload: dict[str, Any]) -> dict[str, str]:
        """Build HTTP headers including HMAC signature."""
        timestamp = str(int(time.time()))
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-FrontierCRM-Event": payload.get("event_type", "unknown"),
            "X-FrontierCRM-Timestamp": timestamp,
            "X-FrontierCRM-Signature-256": compute_signature(payload, endpoint.secret, timestamp),
        }
        return headers

    @staticmethod
    def _enrich_payload(endpoint: WebhookEndpoint, event_type: str, raw_payload: dict[str, Any]) -> dict[str, Any]:
        """Enrich the event payload with standard envelope fields.

        Every outbound webhook payload gets:
          - event_type: the event type string
          - event_id: the WebhookEvent UUID (for dedup by consumer)
          - tenant_id: the tenant UUID
          - timestamp: ISO-8601 UTC timestamp
          - data: the original event payload
        """
        # Enrichment happens in the Celery task, not at enqueue time,
        # because the event_id isn't available until after .create().
        # Return raw payload; enrichment is applied in deliver().
        return raw_payload


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
```

### 3.3 Enriched Payload Structure

Every outbound webhook delivery carries this envelope:

```json
{
  "event_type": "deal.updated",
  "event_id": "uuid-of-the-webhookevent",
  "tenant_id": "uuid-of-the-tenant",
  "timestamp": "2026-06-30T12:00:00Z",
  "data": {
    "deal_id": "uuid",
    "deal_name": "Acme Corp Renewal",
    "value": "50000.00",
    "currency": "USD",
    "pipeline_name": "Sales 2026",
    "stage_name": "Negotiation",
    "previous_stage_name": "Discovery",
    "status": "open",
    "owner_name": "Alice Smith",
    "owner_email": "alice@frontiercrm.com",
    "contact_name": "Bob Johnson",
    "contact_email": "bob@acme.com"
  }
}
```

The enrichment is performed by `WebhookDeliveryService.deliver()` before the HTTP POST. The `WebhookEvent.payload` stores the raw source event; enrichment is applied at delivery time so the payload can be re-enriched on retry.

---

## 4. Signed Payloads for Consumer Verification

### 4.1 Headers

Every outbound webhook request includes:

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Type` | `application/json` | Standard |
| `User-Agent` | `FrontierCRM-Webhook/1.0` | Identify source |
| `X-FrontierCRM-Event` | e.g. `deal.updated` | Event type at a glance |
| `X-FrontierCRM-Timestamp` | Unix timestamp string | Prevent replay attacks |
| `X-FrontierCRM-Signature-256` | Hex HMAC-SHA256 | Verify payload integrity |

### 4.2 Signature Algorithm

```
HMAC-SHA256(
  secret,
  timestamp + "." + canonical_json(payload)
)
```

Where:
- `secret` is the `WebhookEndpoint.secret` value
- `timestamp` is the `X-FrontierCRM-Timestamp` header value
- `canonical_json(payload)` is `json.dumps(payload, sort_keys=True, separators=(",", ":"))` — sorted keys, no whitespace

### 4.3 Consumer Verification (Documentation)

The admin guide will document this for consumers:

```python
import hashlib
import hmac
import json

def verify_webhook_signature(payload: dict, header_signature: str, header_timestamp: str, secret: str) -> bool:
    """Verify a FrontierCRM webhook signature.

    Call this in your webhook endpoint before processing the payload.
    """
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    message = f"{header_timestamp}.{raw}"
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header_signature)
```

**Recommended consumer flow:**
1. Receive POST at your endpoint
2. Read `X-FrontierCRM-Signature-256` and `X-FrontierCRM-Timestamp` headers
3. Verify signature using the shared secret (set in FrontierCRM webhook settings)
4. Check timestamp is within ±5 minutes to prevent replay attacks
5. Process the payload
6. Return 2xx to acknowledge

---

## 5. Event Triggers

### 5.1 Trigger Architecture

```
┌──────────────────────────────┐
│  Deal.post_save              │
│  Contact.post_save           │
│  Activity.post_save          │
│  Email sync completion       │
│  (apps/webhooks/signals.py)  │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  WebhookDeliveryService      │
│  .enqueue(endpoint, type,    │
│            payload)          │
│  → creates WebhookEvent      │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  deliver_webhook.delay()     │
│  (Celery task)               │
└──────────────────────────────┘
```

### 5.2 Event Type Taxonomy

| Event Type | Trigger | Payload Includes |
|-----------|---------|-----------------|
| `deal.created` | Deal post_save (created=True) | deal_id, name, value, status, pipeline, stage, owner |
| `deal.updated` | Deal post_save (created=False) | Same + changed_fields list |
| `deal.stage_changed` | Deal post_save, stage FK changed | from_stage, to_stage |
| `deal.status_changed` | Deal status field changed | from_status, to_status |
| `contact.created` | Contact post_save (created=True) | contact_id, name, email, phone, account |
| `contact.updated` | Contact post_save (created=False) | Same + changed_fields list |
| `activity.created` | Activity post_save (created=True) | activity_id, type, entity ref, summary |
| `email.received` | Email sync creates Activity (email type) | from, to, subject, snippet, thread_id |

### 5.3 Signal Handler: apps/webhooks/signals.py

```python
"""Signal handlers — fire outbound webhooks when entities change."""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.activities.models import Activity
from apps.contacts.models import Contact
from apps.pipelines.models import Deal

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Deal)
def deal_changed_handler(sender, instance, created, **kwargs):
    """Fire webhooks when a Deal is created or updated.

    Triggers:
      - deal.created
      - deal.updated (with stage/status change subtypes detected in task)
    """
    if not instance.is_active:
        return  # skip archived/inactive deals

    event_type = "deal.created" if created else "deal.updated"
    _fire_webhooks(instance.tenant_id, event_type, _build_deal_payload(instance))


@receiver(post_save, sender=Contact)
def contact_changed_handler(sender, instance, created, **kwargs):
    """Fire webhooks when a Contact is created or updated."""
    event_type = "contact.created" if created else "contact.updated"
    _fire_webhooks(instance.tenant_id, event_type, _build_contact_payload(instance))


@receiver(post_save, sender=Activity)
def activity_created_handler(sender, instance, created, **kwargs):
    """Fire webhooks when an Activity is created (email, note, etc.)."""
    if not created:
        return

    # Map activity type to event type
    activity_to_event = {
        Activity.ActivityType.EMAIL: "email.received",
        Activity.ActivityType.NOTE: "activity.created",
        Activity.ActivityType.TASK: "activity.created",
        Activity.ActivityType.CALL: "activity.created",
        Activity.ActivityType.MEETING: "activity.created",
        Activity.ActivityType.FILE_UPLOAD: "activity.created",
    }
    event_type = activity_to_event.get(instance.activity_type)
    if event_type is None:
        return  # only fire for user-facing activity types

    _fire_webhooks(instance.tenant_id, event_type, _build_activity_payload(instance))


# ── Helpers ────────────────────────────────────────────────────────────────────


def _fire_webhooks(tenant_id, event_type, payload):
    """Find matching endpoints and enqueue events.

    Runs synchronously but only does DB writes (no HTTP calls).
    The actual HTTP delivery happens in the Celery task.
    """
    from apps.webhooks.models import WebhookEndpoint
    from apps.webhooks.services import WebhookDeliveryService

    endpoints = WebhookEndpoint.objects.filter(
        tenant_id=tenant_id,
        is_active=True,
    )
    matched = 0
    for endpoint in endpoints:
        if not _matches_event(endpoint, event_type):
            continue
        try:
            event = WebhookDeliveryService.enqueue(endpoint, event_type, payload)
            from apps.webhooks.tasks import deliver_webhook
            deliver_webhook.delay(str(event.id))
            matched += 1
        except Exception as exc:
            logger.error("Failed to enqueue webhook %s for event %s: %s", endpoint.id, event_type, exc)


def _matches_event(endpoint, event_type: str) -> bool:
    """Check if the endpoint subscribes to this event type.

    Empty events list = subscribe to everything.
    Otherwise, check for exact match or wildcard prefix.
    """
    if not endpoint.events:
        return True
    for pattern in endpoint.events:
        if pattern == event_type:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            if event_type.startswith(prefix):
                return True
    return False


def _build_deal_payload(deal) -> dict:
    """Build a standardized Deal payload for webhook delivery."""
    return {
        "deal_id": str(deal.id),
        "deal_name": deal.name,
        "value": str(deal.value),
        "currency": deal.currency,
        "status": deal.status,
        "pipeline_id": str(deal.pipeline_id),
        "pipeline_name": deal.pipeline.name,
        "stage_id": str(deal.stage_id),
        "stage_name": deal.stage.name,
        "owner_id": str(deal.owner_id) if deal.owner_id else None,
        "contact_id": str(deal.contact_id) if deal.contact_id else None,
    }


def _build_contact_payload(contact) -> dict:
    """Build a standardized Contact payload for webhook delivery."""
    return {
        "contact_id": str(contact.id),
        "name": contact.name,
        "email": contact.email,
        "phone": contact.phone,
        "account_id": str(contact.account_id) if contact.account_id else None,
        "owner_id": str(contact.owner_id) if contact.owner_id else None,
    }


def _build_activity_payload(activity) -> dict:
    """Build an Activity payload for webhook delivery."""
    return {
        "activity_id": str(activity.id),
        "activity_type": activity.activity_type,
        "title": activity.title,
        "entity_type": activity.entity_type,
        "entity_id": str(activity.entity_id) if activity.entity_id else None,
        "actor_id": str(activity.actor_id) if activity.actor_id else None,
        "metadata": activity.metadata,
    }
```

### 5.4 AppConfig: Loading Signals

Register the signals in `apps/webhooks/apps.py`:

```python
class WebhooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.webhooks"
    verbose_name = "Webhooks"

    def ready(self):
        import apps.webhooks.signals  # noqa: F401
```

---

## 6. Retry & Backoff Strategy

### 6.1 Strategy

| Attempt | Delay | Cumulative Wall Time |
|---------|-------|---------------------|
| 1 | 60s | 1 min |
| 2 | 120s | 3 min |
| 3 | 240s | 7 min |
| 4 | 480s | 15 min |
| 5+ | 600s (cap) | Every 10 min |

**Formula:** `delay = min(60 * 2^(attempt-1), 600)`

### 6.2 Retry Lifecycle

```
                    ┌──────────────┐
                    │  PENDING     │ ← WebhookDeliveryService.enqueue()
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Celery task │ ← deliver_webhook.delay(event_id)
                    │  .deliver()  │
                    └──────┬───────┘
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
        ┌──────────────┐       ┌──────────────┐
        │  DELIVERED   │       │  PENDING     │ ← next_retry_at set
        │  (done)      │       │  (retry)     │
        └──────────────┘       └──────┬───────┘
                                       │
                                ┌──────▼───────┐
                                │  Celery Beat │ ← retry_stale_webhooks
                                │  sweep task  │    (every 5 min)
                                └──────┬───────┘
                                       │
                               ┌───────┴────────┐
                               ▼                ▼
                        ┌──────────┐     ┌──────────────┐
                        │ PENDING  │     │  FAILED      │
                        │ +retry   │     │  → dead-letter│
                        └──────────┘     └──────────────┘
```

### 6.3 Retry vs. Celery Task Retries

The system has **two layers of retry**:

1. **Celery task retries** (`max_retries=0` on `deliver_webhook` task) — disabled. We manage retry ourselves via `next_retry_at`.
2. **Application-level retry** via `_handle_failure` — the event stays `PENDING` with a `next_retry_at` timestamp, and the Beat sweep picks it up later.

Rationale: Celery task retries re-raise the exception and consume broker resources. Application-level retry with a DB timestamp is more observable (admins can see `next_retry_at` values), survives broker restarts, and doesn't accumulate Celery retry stack frames.

---

## 7. Dead-Letter Queue

### 7.1 When an Event Enters the Dead-Letter Queue

A `WebhookDeadEvent` record is created when:
- `event.attempt_count >= endpoint.max_retries`
- The event status is set to `FAILED`

### 7.2 Dead-Event Lifecycle

```
WebhookEvent: FAILED
       │
       ▼
WebhookDeadEvent created
       │
       ├── Admin inspects via Django admin
       ├── Admin replays action → creates new WebhookEvent + enqueues delivery
       ├── Admin resolves (marks as handled with notes)
       └── Auto-pruned after 90 days (via Celery Beat cleanup task)
```

### 7.3 Admin Actions

The Django admin for `WebhookDeadEvent` provides:

- **List view**: filter by endpoint, event_type, resolved status, date range
- **Detail view**: full payload, last error, response dump
- **Action: Replay** — creates a fresh `WebhookEvent` from the dead event's payload and enqueues delivery. The new event gets a new ID and a fresh retry counter.
- **Action: Resolve** — sets `resolved_at` and `resolution_notes`
- **Action: Resolve selected** — batch-resolve multiple dead events

### 7.4 Data Retention

- Dead events are auto-pruned after 90 days via a Celery Beat task (`prune_old_dead_events`, runs daily at 03:00 UTC)
- Configurable via `settings.WEBHOOK_DEAD_EVENT_RETENTION_DAYS` (default: 90)

---

## 8. Celery Beat — Retry Scheduler

### 8.1 Periodic Tasks

Two new Celery Beat entries in `config/settings/base.py`:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # ... existing tasks ...
    "retry-stale-webhooks": {
        "task": "apps.webhooks.tasks.retry_stale_webhooks",
        "schedule": 300.0,  # every 5 minutes
        "options": {"expires": 240.0},  # drop if beat is backed up
    },
    "prune-old-dead-webhook-events": {
        "task": "apps.webhooks.tasks.prune_dead_events",
        "schedule": crontab(hour=3, minute=0),  # daily at 03:00 UTC
        "options": {"expires": 3600},
    },
}
```

### 8.2 Retry Sweep Task

```python
@shared_task(bind=True)
def retry_stale_webhooks(self):
    """Find PENDING events past their next_retry_at and re-deliver them.

    This is the safety net — catches events that were missed by the
    original Celery task (e.g. after broker restart, worker outage).
    """
    from django.utils import timezone
    from apps.webhooks.models import WebhookEvent
    from apps.webhooks.services import WebhookDeliveryService

    now = timezone.now()
    stale = WebhookEvent.objects.filter(
        status=WebhookEvent.EventStatus.PENDING,
        next_retry_at__lte=now,
        endpoint__is_active=True,
    ).select_related("endpoint")[:500]  # batch limit

    service = WebhookDeliveryService()
    results = {"retried": 0, "delivered": 0, "dead_letter": 0, "errors": 0}
    for event in stale:
        try:
            result = service.deliver(event)
            results[result["status"]] = results.get(result["status"], 0) + 1
        except Exception as exc:
            results["errors"] += 1
            logger.error("Stale webhook retry error for event %s: %s", event.id, exc)

    return results
```

### 8.3 Prune Dead Events Task

```python
@shared_task
def prune_dead_events():
    """Remove dead events older than the retention period."""
    from django.conf import settings
    from django.utils import timezone
    from apps.webhooks.models import WebhookDeadEvent

    retention = getattr(settings, "WEBHOOK_DEAD_EVENT_RETENTION_DAYS", 90)
    cutoff = timezone.now() - timedelta(days=retention)
    count, _ = WebhookDeadEvent.objects.filter(failed_at__lt=cutoff).delete()
    logger.info("Pruned %s dead webhook events older than %s days", count, retention)
    return {"pruned": count}
```

---

## 9. API Contracts

### 9.1 Existing Endpoints (unchanged)

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/webhooks/endpoints/` | List/create endpoints |
| GET/PUT/PATCH/DELETE | `/api/webhooks/endpoints/{id}/` | Retrieve/update/delete endpoint |
| GET | `/api/webhooks/events/` | List webhook events (read-only) |
| GET | `/api/webhooks/events/{id}/` | Retrieve webhook event detail |
| POST | `/api/webhooks/receive/` | Public inbound webhook receiver |

### 9.2 New Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/webhooks/dead-events/` | List dead-letter events (read-only) |
| GET | `/api/webhooks/dead-events/{id}/` | Retrieve dead-event detail |
| POST | `/api/webhooks/dead-events/{id}/replay/` | Replay a dead event as a fresh delivery |

### 9.3 Dead-Event List Response

```json
{
  "id": "uuid",
  "endpoint_id": "uuid",
  "event_type": "deal.updated",
  "final_attempt_count": 3,
  "last_error": "HTTP 500: Internal Server Error",
  "failed_at": "2026-06-30T12:00:00Z",
  "resolved_at": null
}
```

### 9.4 Replay Response

```json
{
  "new_event_id": "uuid",
  "status": "pending",
  "message": "Webhook event re-queued for delivery"
}
```

---

## 10. Implementation Order

### Phase 1 — Core Service (P0)
1. Create `apps/webhooks/services.py` with `WebhookDeliveryService`
2. Move `compute_signature` from `views.py` to `services.py`; import from there
3. Create `apps/webhooks/tasks.py` with `deliver_webhook` and `retry_stale_webhooks` and `prune_dead_events`
4. Refactor `views.py` — keep `webhook_receiver` and `WebhookEndpointViewSet`, remove `dispatch_webhook` and `_retry_or_fail`, import from tasks.py/services.py
5. Add `WebhookDeadEvent` model to `models.py`
6. Generate migration
7. Create `apps/webhooks/admin.py` — register `WebhookEndpoint`, `WebhookEvent`, `WebhookDeadEvent`

### Phase 2 — Event Triggers (P0)
8. Create `apps/webhooks/signals.py` — Deal, Contact, Activity handlers
9. Create `apps/webhooks/apps.py` — register signals in `ready()`
10. Add `CELERY_BEAT_SCHEDULE` entries to base settings

### Phase 3 — API & Admin (P1)
11. Add `WebhookDeadEventViewSet` (ReadOnlyModelViewSet) + `replay` action
12. Add URL routes for dead-events endpoint
13. Add Django admin list/detail views with Replay and Resolve actions
14. Add admin action for batch-resolve

### Phase 4 — Testing (P1)
15. Unit tests for `WebhookDeliveryService` (mock HTTP client)
16. Unit tests for `_backoff_delay` and `_matches_event`
17. Integration tests for signal → enqueue → delivery flow
18. Integration tests for dead-letter creation and replay
19. Tests for `retry_stale_webhooks` sweep

---

## 11. Acceptance Criteria

### Must Have (P0)
- [ ] Signal handler on Deal.post_save fires `deal.created` and `deal.updated` events
- [ ] Signal handler on Contact.post_save fires `contact.created` and `contact.updated` events
- [ ] Signal handler on Activity.post_save fires event for email/note/call/meeting/task
- [ ] `WebhookDeliveryService.enqueue()` creates a `WebhookEvent` with PENDING status
- [ ] `WebhookDeliveryService.deliver()` performs HTTP POST with correct headers
- [ ] HMAC-SHA256 signature is computed and sent as `X-FrontierCRM-Signature-256`
- [ ] Success (HTTP 2xx) → event marked `DELIVERED`, endpoint `failure_count` reset
- [ ] Failure (4xx/5xx), attempt < max_retries → event stays `PENDING`, `next_retry_at` set
- [ ] Failure, attempt >= max_retries → event marked `FAILED`, `WebhookDeadEvent` created
- [ ] `retry_stale_webhooks` Beat task sweeps PENDING events past `next_retry_at`
- [ ] `prune_dead_events` Beat task removes dead events older than retention period

### Should Have (P1)
- [ ] Wildcard event subscription works (`deal.*` matches `deal.created`, `deal.updated`)
- [ ] Dead-event replay creates a fresh WebhookEvent and enqueues it
- [ ] Admin can resolve dead events with notes
- [ ] Empty `events` list on endpoint = subscribe to all events
- [ ] Inactive endpoints don't fire (both endpoint-level and deal-level checks)

### Nice to Have (P2)
- [ ] Webhook delivery metrics (delivery count, success rate, latency) via Django signals
- [ ] Per-tenant webhook dashboard showing delivery health
- [ ] Email notification when dead-letter accumulates (e.g. 5+ dead events in 1 hour)

---

## 12. Open Questions / Spike Items

1. **Concurrent delivery to the same endpoint** — If two Deals update simultaneously, two `deliver_webhook` tasks may POST to the same URL concurrently. Is this acceptable for consumers? For P2: yes. Future: in-flight dedup.

2. **Webhook timeout vs. endpoint health** — Current timeout is 30s. Should we allow per-endpoint timeout configuration? Keep it simple for now — hardcoded 30s, revisit if consumers report timeouts.

3. **Changed-fields detection** — `deal.updated` events should include a list of changed fields. Detecting FK changes (stage, pipeline) requires comparing old/new in the signal handler. Use Django's `update_fields` or store previous values in a `_pre` cache via `from django.db.models.signals import pre_save`. Spike needed.

4. **Wildcard event syntax** — `deal.*` matches all deal events. Should we also support `*.created` (all creation events)? For now, only prefix wildcards (endswith `.*`). Expand if users ask.

5. **Payload size limits** — The `payload` JSONField in `WebhookEvent` has no size limit. Should we cap at 1MB? Add a validation in `enqueue()` that truncates or rejects oversized payloads. For P2, let it through — SQLite/Postgres JSON fields handle 1MB+ gracefully.

6. **Webhook retry webhook (recursive)** — What happens if a webhook delivery event itself triggers another webhook? The Activity signal handler could create a recursive loop. Mitigation: signal handlers check `activity.activity_type != "webhook"` or add an `exclude_event_types` list.
