# Phase 5 — Slack Notifications Specification

**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)
**Status:** Draft
**Priority:** P3

---

## Table of Contents

1. [ADR-025: Slack Notifications via Outgoing Webhooks](#1-adr-025-slack-notifications-via-outgoing-webhooks)
2. [Data Model: SlackWebhook](#2-data-model-slackwebhook)
3. [Notification Service](#3-notification-service)
4. [Event Triggers & Message Templates](#4-event-triggers--message-templates)
5. [API Contracts](#5-api-contracts)
6. [Settings UI: Slack Integration Page](#6-settings-ui-slack-integration-page)
7. [Implementation Order](#7-implementation-order)
8. [Acceptance Criteria](#8-acceptance-criteria)
9. [Open Questions / Spike Items](#9-open-questions--spike-items)

---

## 1. ADR-025: Slack Notifications via Outgoing Webhooks

**Status:** Proposed
**Date:** 2026-06-30

### Context

FrontierCRM needs to notify team members in Slack when important CRM events happen — deal stage changes, won/lost deals, new emails from contacts. The project already has:

- An `Activity` model tracking all relevant events with `activity_type`, `entity_type`, `entity_id`, `actor_id`, and rich `metadata` JSON
- A `WebhookEndpoint`+`WebhookEvent` outbound webhook system with retry/dead-letter tracking
- A `Tenant.settings` JSONField that could store Slack configurations
- Celery infrastructure with beat scheduling and retry patterns

No Slack-specific code exists anywhere in the codebase.

### Options Considered

**Option A — Slack Bolt SDK (Socket Mode or Event API)**
Run a Slack Bolt app server that listens for slash commands and events via WebSocket/Events API.

- Pros: bidirectional (could support /fr commands, interactive messages, modals)
- Cons: requires Slack App registration, OAuth flow, event subscription URL, separate long-lived process; 10x more complexity than needed for one-direction notification; socket-mode servers need session management

**Option B — Incoming Webhooks (Slack Incoming Webhooks API)**
Each user/workspace configures a Slack Incoming Webhook URL (or Slack app webhook URL). FrontierCRM POSTs JSON payloads to that URL on matching events.

- Pros: stateless (just HTTP POST to a URL), no OAuth, no separate server process, can build on existing `WebhookEndpoint` infrastructure, simple message blocks supported
- Cons: one-direction only (no slash commands, no interactive messages); webhook URL is a bearer token in the URL

**Option C — Slack API with OAuth (chat.postMessage)**
Full Slack OAuth flow (bot token, scopes), store workspace-level access token, call `chat.postMessage` API.

- Pros: programmable channels, rate-limit-aware, can target multiple channels per workspace
- Cons: requires Slack App creation + OAuth redirect handling + token refresh; heavier than needed for P3 notifications

**Option D — Webhook Endpoint + Frontend Configuration Only (no new model)**
Reuse the existing `WebhookEndpoint` model and let users configure Slack Incoming Webhook URLs as a generic webhook. The `events` JSONField already stores event subscriptions.

- Pros: zero new code; existing webhook delivery system handles retry, event tracking, and dead-letter
- Cons: no Slack-specific message formatting (blocks, attachments, markdown-friendly); user sees "Webhook Endpoint" in UI instead of "Slack"; no Slack icon, no test-message button; no rate-limit awareness for Slack's per-webhook throttle (1 msg/sec); poor UX for non-technical users

### Decision

**Hybrid of Option B + Option D — a purpose-built `SlackWebhook` model that wraps the existing webhook infrastructure with Slack-specific formatting.**

Rationale:
1. The existing `WebhookEndpoint` model is generic — it stores a URL, secret, and events list. Slack Incoming Webhooks don't use HMAC signing; they authenticate via the URL itself. Force-fitting would confuse the signing logic.
2. Slack Webhook URLs have rate limits (1 request per second per webhook). The generic WebhookEndpoint has `max_retries` but no rate-limit awareness. A dedicated service can implement simple per-webhook throttling.
3. Slack message formatting (blocks with fields, color, fallback text) is different from generic JSON payloads. A dedicated formatter keeps the webhook delivery generic and the formatting Slack-specific.
4. Future Slack features (channel selector, test message button, DM notifications) need a Slack-specific model anyway. Introducing the right abstraction now avoids a model rename/migration later.

**Rejected:** Pure reusable-webhook approach (Option D) — UX and rate-limit needs are Slack-specific enough to justify a dedicated model.

### Consequences

- New `apps/slack/` Django app with models, views, serializers, tasks, and message formatters
- New database table `slack_webhook`
- Backward compatible — the existing `WebhookEndpoint` system is untouched
- Frontend gets a dedicated Slack settings page instead of a "Webhook Endpoint" form
- Future add: channel selector, test button, per-user DM notification preferences

---

## 2. Data Model: SlackWebhook

### Model Definition

Location: `apps/slack/models.py`

```python
class SlackWebhook(TenantScopedModel):
    """Slack incoming webhook configuration per tenant/workspace."""

    # The webhook URL from Slack (Incoming Webhooks or Slack app)
    webhook_url = models.URLField(max_length=2000)

    # Optional override — which Slack channel to post to.
    # If empty, uses the default channel configured when the webhook was created.
    channel_override = models.CharField(max_length=100, blank=True, default="")

    # Display name shown in UI (e.g. "Sales Team Channel")
    display_name = models.CharField(max_length=255, blank=True, default="")

    # Which event types trigger notifications on this webhook.
    # List of strings matching Activity.ActivityType values.
    # Empty list = all events trigger. Partial list = only those event types.
    subscribed_events = models.JSONField(default=list, blank=True,
        help_text="List of activity_type values to notify on. Empty = all events.")

    # Optional filters — notify only when deals match a pipeline/stage
    pipeline_filter = models.ForeignKey(
        "pipelines.Pipeline", on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="If set, only notify on deals in this pipeline",
    )

    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)

    class Meta:
        db_table = "slack_webhook"
        indexes = [
            models.Index(fields=["tenant_id", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.display_name or self.webhook_url[:50]
```

### Migration Notes

- Table: `slack_webhook`
- Inherits `tenant_id`, `id`, `created_at`, `updated_at` from `TenantScopedModel`
- No `deleted_at` — soft-delete via `is_active=False` (webhook URLs are cheap; no need for cascade-safe soft delete)

### Existing Model Relationships

```
Tenant (teams/models.py)
  └── slack_webhooks         ← reverse relation from SlackWebhook.tenant_id
  └── settings.json          ← stores default_slack_webhook_id (optional)

SlackWebhook
  └── pipeline_filter_id     → pipelines.Pipeline (nullable, optional scope)
```

---

## 3. Notification Service

### Architecture

```
Activity Created (via Django signal or post-save hook)
  │
  ▼
SlackNotificationService.notify(activity)
  │
  ├── 1. Query active SlackWebhook records for this tenant
  ├── 2. Filter by subscribed_events (if non-empty)
  ├── 3. Filter by pipeline_filter (if set, check activity.entity_type=deal)
  ├── 4. Build Slack message blocks via SlackMessageFormatter
  ├── 5. Rate-limit check (per-webhook: max 1 POST / second)
  ├── 6. POST to webhook_url
  ├── 7. On success: update last_triggered_at, reset failure_count
  └── 8. On failure: increment failure_count (auto-deactivate at >= 10 failures)
```

### Service Class

Location: `apps/slack/services.py`

```python
from __future__ import annotations

import json
import time
from typing import Any

import requests
from django.db.models import QuerySet
from django.utils import timezone

from apps.activities.models import Activity
from apps.slack.models import SlackWebhook
from apps.slack.formatters import SlackMessageFormatter


SLACK_RATE_LIMIT_SECONDS = 1.0  # 1 request per second per webhook
MAX_FAILURE_COUNT = 10           # Auto-deactivate after 10 consecutive failures


class SlackNotificationService:
    """Orchestrates Slack webhook delivery for Activity events."""

    _last_send_time: dict[str, float] = {}  # webhook_id -> timestamp

    @classmethod
    def notify(cls, activity: Activity) -> list[dict[str, Any]]:
        """Deliver a notification for a single Activity to all matching webhooks.

        Returns a list of delivery results (one per webhook).
        """
        webhooks: QuerySet[SlackWebhook] = SlackWebhook.objects.filter(
            tenant_id=activity.tenant_id,
            is_active=True,
        )

        results: list[dict[str, Any]] = []
        for wh in webhooks:
            if not cls._should_notify(wh, activity):
                continue

            message = SlackMessageFormatter.format(activity)
            result = cls._send(wh, message)
            results.append(result)

        return results

    @classmethod
    def _should_notify(cls, webhook: SlackWebhook, activity: Activity) -> bool:
        """Check if this webhook should receive this activity type."""
        # If subscribed_events is empty, notify on everything
        if webhook.subscribed_events:
            if activity.activity_type not in webhook.subscribed_events:
                return False

        # If pipeline_filter is set, only notify on deals in that pipeline
        if webhook.pipeline_filter_id and activity.entity_type == "deal":
            deal_pipeline_id = activity.metadata.get("pipeline_id")
            if str(deal_pipeline_id) != str(webhook.pipeline_filter_id):
                return False

        return True

    @classmethod
    def _send(cls, webhook: SlackWebhook, payload: dict[str, Any]) -> dict[str, Any]:
        """POST a Slack message payload to the webhook URL with rate limiting."""
        wh_id = str(webhook.id)

        # Rate limit: enforce 1 request/sec per webhook
        last_sent = cls._last_send_time.get(wh_id, 0.0)
        elapsed = time.time() - last_sent
        if elapsed < SLACK_RATE_LIMIT_SECONDS:
            time.sleep(SLACK_RATE_LIMIT_SECONDS - elapsed)

        try:
            resp = requests.post(
                webhook.webhook_url,
                json=payload,
                timeout=10,
            )
            cls._last_send_time[wh_id] = time.time()

            if resp.status_code == 200:
                webhook.last_triggered_at = timezone.now()
                webhook.failure_count = 0
                webhook.save(update_fields=["last_triggered_at", "failure_count", "updated_at"])
                return {"webhook_id": wh_id, "status": "delivered"}
            else:
                return cls._handle_failure(webhook, resp)

        except requests.RequestException as exc:
            return cls._handle_failure(webhook, exc=exc)

    @classmethod
    def _handle_failure(
        cls, webhook: SlackWebhook,
        resp: requests.Response | None = None,
        exc: Exception | None = None,
    ) -> dict[str, Any]:
        webhook.failure_count += 1
        if webhook.failure_count >= MAX_FAILURE_COUNT:
            webhook.is_active = False
        webhook.save(update_fields=["failure_count", "is_active", "updated_at"])

        error = resp.text[:500] if resp is not None else str(exc)
        return {"webhook_id": str(webhook.id), "status": "failed", "error": error}
```

### Trigger Mechanism — Django Signal (Recommended)

Create `apps/slack/signals.py` with a `post_save` handler on `Activity`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.activities.models import Activity
from apps.slack.services import SlackNotificationService


@receiver(post_save, sender=Activity)
def activity_created_handler(sender, instance, created, **kwargs):
    """Fire Slack notifications when a new Activity is created."""
    if not created:
        return
    # Fire async — don't block the HTTP response
    from celery import current_app
    current_app.send_task(
        "apps.slack.tasks.deliver_slack_notifications",
        args=[str(instance.id)],
    )
```

### Celery Task

Location: `apps/slack/tasks.py`

```python
from __future__ import annotations

from celery import shared_task

from apps.activities.models import Activity
from apps.slack.services import SlackNotificationService


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def deliver_slack_notifications(self, activity_id: str) -> dict:
    """Load an Activity and push notifications to all matching Slack webhooks."""
    try:
        activity = Activity.objects.get(id=activity_id)
    except Activity.DoesNotExist:
        return {"error": "Activity not found", "activity_id": activity_id}

    results = SlackNotificationService.notify(activity)
    return {"activity_id": activity_id, "results": results}
```

### Rate-Limiting Strategy

| Mechanism | Detail |
|-----------|--------|
| Per-webhook max | 1 POST / second (Slack Incoming Webhook limit) |
| Implementation | In-process `time.sleep()` per-webhook in `_send()` |
| Concurrency | Celery task runs per-activity; multiple activities created simultaneously may batch to the same webhook within 1 second. The in-process sleep serializes per activity, not per-second globally. For P3 this is acceptable — at CRM activity rates (>1 activity/second per webhook is rare), the sleep is negligible. |
| Future improvement | Token bucket rate limiter in Redis if Slack volume grows beyond ~60/minute per webhook |

---

## 4. Event Triggers & Message Templates

### Trigger Map

The signal handler fires on **all** `Activity` creates. The `SlackWebhook.subscribed_events` list controls which activity types actually send. Default recommendation for new webhooks: notify on all four business events below.

| Activity Type (enum) | Human Event | Slack Notification Priority |
|---|---|---|
| `deal_stage_change` | Deal moved from A → B | High |
| `deal_status_change` | Deal won, lost, or abandoned | High |
| `email` | New email received from contact | Medium |
| `note` | Note added to deal/contact | Low (opt-in) |
| `call` | Call logged | Low (opt-in) |
| `meeting` | Meeting recorded | Low (opt-in) |
| `task` | Task assigned/completed | Medium (opt-in) |
| `file_upload` | File attached to deal/contact | Low (opt-in) |
| `system` | Admin/system event | Admin-only |

### Slack Message Template: Deal Stage Change

**Blocks payload** (Slack Block Kit — renders rich, not just text):

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🔄 Deal Stage Changed"
      }
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Deal:*\n<https://app.frontiercrm.com/deals/{deal_id}|{deal_name}>"},
        {"type": "mrkdwn", "text": "*Value:*\n${value}"},
        {"type": "mrkdwn", "text": "*From:*\n{from_stage}"},
        {"type": "mrkdwn", "text": "*To:*\n{to_stage}"},
        {"type": "mrkdwn", "text": "*Owner:*\n{owner_name}"},
        {"type": "mrkdwn", "text": "*Pipeline:*\n{pipeline_name}"}
      ]
    },
    {
      "type": "context",
      "elements": [
        {"type": "mrkdwn", "text": "FrontierCRM · {timestamp}"}
      ]
    }
  ]
}
```

### Slack Message Template: Deal Won/Lost

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🎉 Deal Won!"
      }
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Deal:*\n<https://app.frontiercrm.com/deals/{deal_id}|{deal_name}>"},
        {"type": "mrkdwn", "text": "*Value:*\n${value}"},
        {"type": "mrkdwn", "text": "*Owner:*\n{owner_name}"},
        {"type": "mrkdwn", "text": "*Pipeline:*\n{pipeline_name}"}
      ]
    },
    {
      "type": "context",
      "elements": [
        {"type": "mrkdwn", "text": "FrontierCRM · {timestamp}"}
      ]
    }
  ]
}
```

For **Deal Lost** use a `❌` emoji, title "Deal Lost", and append a `lost_reason` field if available in `activity.metadata`.

### Slack Message Template: New Email from Contact

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📧 New Email from Contact"
      }
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*From:*\n{from_name} <{from_email}>"},
        {"type": "mrkdwn", "text": "*Subject:*\n{subject}"},
        {"type": "mrkdwn", "text": "*Related to:*\n<https://app.frontiercrm.com/contacts/{contact_id}|{contact_name}>"}
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "```{snippet}```"
      }
    },
    {
      "type": "context",
      "elements": [
        {"type": "mrkdwn", "text": "FrontierCRM · {timestamp}"}
      ]
    }
  ]
}
```

### Message Formatter Class

Location: `apps/slack/formatters.py`

```python
from __future__ import annotations

from typing import Any

from apps.activities.models import Activity


class SlackMessageFormatter:
    """Build Slack Block Kit payloads from Activity records."""

    FORMATTERS: dict[str, callable] = {}

    @classmethod
    def register(cls, activity_type: str):
        """Decorator to register a formatter for an activity type."""
        def wrapper(func):
            cls.FORMATTERS[activity_type] = func
            return func
        return wrapper

    @classmethod
    def format(cls, activity: Activity) -> dict[str, Any]:
        """Return a Slack-compatible block payload for the given activity."""
        formatter = cls.FORMATTERS.get(activity.activity_type)
        if formatter is None:
            # Fallback: generic text message
            return cls._generic_format(activity)
        return formatter(activity)

    @classmethod
    def _generic_format(cls, activity: Activity) -> dict[str, Any]:
        return {
            "text": f"[{activity.activity_type}] {activity.title}",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{activity.title}*\n{activity.description}"},
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"FrontierCRM · {activity.created_at.isoformat()}"}],
                },
            ],
        }


# ── Register built-in formatters ────────────────────────────────────────

@SlackMessageFormatter.register("deal_stage_change")
def _format_deal_stage_change(activity: Activity) -> dict[str, Any]:
    meta = activity.metadata
    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🔄 Deal Stage Changed"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Deal:*\n<https://app.frontiercrm.com/deals/{activity.entity_id}|{meta.get('deal_name', 'Unknown')}>"},
                    {"type": "mrkdwn", "text": f"*Value:*\n${meta.get('value', '—')}"},
                    {"type": "mrkdwn", "text": f"*From:*\n{meta.get('from_stage', '?')}"},
                    {"type": "mrkdwn", "text": f"*To:*\n{meta.get('to_stage', '?')}"},
                    {"type": "mrkdwn", "text": f"*Owner:*\n{meta.get('owner_name', '—')}"},
                    {"type": "mrkdwn", "text": f"*Pipeline:*\n{meta.get('pipeline_name', '—')}"},
                ],
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"FrontierCRM · {activity.created_at.isoformat()}"}],
            },
        ],
    }


@SlackMessageFormatter.register("deal_status_change")
def _format_deal_status_change(activity: Activity) -> dict[str, Any]:
    meta = activity.metadata
    new_status = meta.get("new_status", "")
    if new_status == "won":
        emoji = "🎉"
        title = "Deal Won!"
    elif new_status == "lost":
        emoji = "❌"
        title = "Deal Lost"
    else:
        emoji = "📋"
        title = f"Deal Status: {new_status}"

    fields = [
        {"type": "mrkdwn", "text": f"*Deal:*\n<https://app.frontiercrm.com/deals/{activity.entity_id}|{meta.get('deal_name', 'Unknown')}>"},
        {"type": "mrkdwn", "text": f"*Value:*\n${meta.get('value', '—')}"},
        {"type": "mrkdwn", "text": f"*Owner:*\n{meta.get('owner_name', '—')}"},
        {"type": "mrkdwn", "text": f"*Pipeline:*\n{meta.get('pipeline_name', '—')}"},
    ]

    if new_status == "lost" and meta.get("lost_reason"):
        fields.append({"type": "mrkdwn", "text": f"*Lost Reason:*\n{meta['lost_reason']}"})

    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} {title}"},
            },
            {"type": "section", "fields": fields},
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"FrontierCRM · {activity.created_at.isoformat()}"}],
            },
        ],
    }


@SlackMessageFormatter.register("email")
def _format_email(activity: Activity) -> dict[str, Any]:
    meta = activity.metadata
    direction = meta.get("direction", "inbound")
    if direction == "outbound":
        header = "📤 Email Sent"
    else:
        header = "📧 New Email"

    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": header},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*From:*\n{meta.get('from_name', '?')} <{meta.get('from_email', '?')}>"},
                    {"type": "mrkdwn", "text": f"*Subject:*\n{meta.get('subject', '(no subject)')}"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{meta.get('snippet', '')[:300]}```"},
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"FrontierCRM · {activity.created_at.isoformat()}"}],
            },
        ],
    }
```

### Activity Metadata Convention

For Slack formatters to work, `Activity.metadata` must contain these keys for each activity type:

| Activity Type | Required Metadata Keys |
|---|---|
| `deal_stage_change` | `deal_name`, `from_stage`, `to_stage`, `value`, `owner_name`, `pipeline_name`, `pipeline_id` |
| `deal_status_change` | `deal_name`, `new_status` ("won"/"lost"/"abandoned"), `value`, `owner_name`, `pipeline_name`, `lost_reason` (optional) |
| `email` | `from_name`, `from_email`, `subject`, `snippet`, `direction` ("inbound"/"outbound"), `contact_id` (optional) |

These keys should already be set when the `Activity` is created (checked in the existing `apps/pipelines/views.py` deal update handler and `apps/email/tasks.py` send handler). See **Verification step** in Acceptance Criteria.

---

## 5. API Contracts

### `GET /api/slack/webhooks/` — List configured webhooks

**Response:** Array of `SlackWebhook` objects

```json
[
  {
    "id": "uuid",
    "webhook_url": "https://hooks.slack.com/services/T00/B00/xxxx",
    "channel_override": "",
    "display_name": "Sales Team",
    "subscribed_events": ["deal_stage_change", "deal_status_change"],
    "pipeline_filter": {
      "id": "uuid",
      "name": "Sales Pipeline"
    },
    "is_active": true,
    "last_triggered_at": "2026-06-30T14:30:00Z",
    "failure_count": 0
  }
]
```

### `POST /api/slack/webhooks/` — Create webhook

**Request:**
```json
{
  "webhook_url": "https://hooks.slack.com/services/T00/B00/xxxx",
  "channel_override": "",
  "display_name": "Sales Team",
  "subscribed_events": ["deal_stage_change", "deal_status_change", "email"],
  "pipeline_filter_id": "uuid or null"
}
```

**Response:** `201 Created` with full `SlackWebhook` object

### `PATCH /api/slack/webhooks/{id}/` — Update webhook

Partial update — any field is optional. Use to toggle `is_active`, change subscriptions, or update the URL.

### `DELETE /api/slack/webhooks/{id}/` — Remove webhook

Hard-deletes the record. The notification service will no longer check it.

### `POST /api/slack/webhooks/{id}/test/` — Send test message

**Request:** (none, body empty)

**Response:**
```json
{
  "status": "delivered"
}
```

This triggers the notification service to send a "FrontierCRM Slack integration is working! 🎉" test message to the webhook URL. If it fails, return `{"status": "failed", "error": "..."}` so the UI can show the user the webhook URL is invalid.

### `POST /api/slack/webhooks/{id}/deactivate/` — Auto-deactivate

Sets `is_active=false`. Used when the failure count exceeds threshold. Can also be called manually from UI.

### URL Registration

Add to `config/urls.py`:

```python
path("slack/", include("apps.slack.urls")),
```

### ViewSet Pattern

The standard DRF `ModelViewSet` pattern, matching `apps/webhooks/views.py`:

```python
class SlackWebhookViewSet(viewsets.ModelViewSet):
    queryset = SlackWebhook.objects.all()
    serializer_class = SlackWebhookSerializer

    def get_queryset(self):
        return SlackWebhook.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        webhook = self.get_object()
        # Send test message synchronously
        result = send_test_slack_message(webhook)
        if result["status"] == "delivered":
            return Response({"status": "delivered"})
        return Response(result, status=400)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        webhook = self.get_object()
        webhook.is_active = False
        webhook.save(update_fields=["is_active", "updated_at"])
        return Response({"status": "deactivated"})
```

---

## 6. Settings UI: Slack Integration Page

### Location

New page at route `/settings/integrations/slack` in the frontend.

Add to the Settings navigation sidebar — a "Slack" entry under a new "Integrations" section:

```
Settings
├── General
├── Team
├── Pipeline Settings
├── Integrations
│   ├── Gmail (existing)
│   └── Slack (new)
└── Billing
```

### Page Layout

```
┌──────────────────────────────────────────────────────┐
│  Slack Integration                                    │
│  Send CRM notifications to your Slack channels.       │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  [Connected Webhooks]                             │ │
│  │                                                    │ │
│  │  ┌─ Webhook: Sales Team ───────────────────────┐ │ │
│  │  │  Channel: #sales-team          Status: ✅   │ │ │
│  │  │  Events: Stage Changes, Won/Lost, Emails    │ │ │
│  │  │  [Edit] [Test] [Remove]                     │ │ │
│  │  └────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │  [+ Add Slack Webhook]                            │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Need a webhook URL?                              │ │
│  │  1. Open Slack → Apps → Incoming Webhooks         │ │
│  │  2. Add to channel → Copy URL                     │ │
│  │  3. Paste it below                                │ │
│  │                                                    │ │
│  │  ┌─ Webhook URL: ──────────────────────────────┐ │ │
│  │  │  https://hooks.slack.com/services/...       │ │ │
│  │  └────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │  [Connect]                                        │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### Form: Add/Edit Webhook

| Field | Type | Description |
|---|---|---|
| Webhook URL | Text input (required) | Slack Incoming Webhook URL, validated `https://hooks.slack.com/services/*` |
| Display Name | Text input (optional) | Friendly label (defaults to "Slack Webhook #N") |
| Channel Override | Text input (optional) | e.g. `#general`, `#sales`. Leave empty to use webhook default. |
| Send Notifications For | Multi-select checkboxes | `deal_stage_change`, `deal_status_change`, `email`, `note`, `call`, `task` (pre-ticked: stage change + won/lost + email) |
| Pipeline Filter | Dropdown (optional) | Filter to a single pipeline, or "All Pipelines" |

### Frontend Components Required

| Component | Description |
|---|---|
| `SlackSettingsPage` | Page wrapper — fetches webhooks list, conditionally shows add form |
| `SlackWebhookList` | Lists connected webhooks with status badges |
| `SlackWebhookCard` | Single webhook row with edit/test/remove actions |
| `SlackWebhookForm` | Add/edit form (reused for both) |
| `SlackTestResultBanner` | Success/error banner after test message |
| `useSlackWebhooks` | API hook — CRUD + test + deactivate |

### States

| State | Behavior |
|---|---|
| **Loading** | Skeleton cards |
| **Empty** | "No Slack webhooks configured." + prompt to add one |
| **Error (load)** | Error banner + retry button |
| **Error (test)** | "Test message failed: {error}" with webhook URL validation hint |
| **Auto-deactivated** | Status badge shows "⚠️ Deactivated (10 failures)" with a "Reactivate" button |

---

## 7. Implementation Order

### Phase 5a: Backend Model + API (estimated: 0.5 day)

1. **Create `apps/slack/` app**
   - `python manage.py startapp slack`
   - Register in `INSTALLED_APPS` in `config/settings/base.py`
   - Create `apps/slack/__init__.py` with `default_app_config` (or explicitly add to settings)

2. **Model** — `apps/slack/models.py`
   - `SlackWebhook(TenantScopedModel)` with all fields from Section 2
   - `python manage.py makemigrations slack && python manage.py migrate`

3. **Serializer + ViewSet** — `apps/slack/views.py`
   - `SlackWebhookSerializer` (ModelSerializer, exclude field: none, read-only: `id`, `tenant_id`, `created_at`, `updated_at`, `last_triggered_at`, `failure_count`)
   - `SlackWebhookViewSet` with `@action(detail=True, methods=["post"])` for `test` and `deactivate`
   - `apps/slack/urls.py` with `DefaultRouter`

4. **Register URL** in `config/urls.py`:
   ```python
   path("slack/", include("apps.slack.urls")),
   ```

### Phase 5b: Notification Service (estimated: 0.5 day)

5. **Message Formatter** — `apps/slack/formatters.py`
   - `SlackMessageFormatter` class with `register()` decorator pattern
   - Built-in formatters for `deal_stage_change`, `deal_status_change`, `email`
   - Generic fallback formatter

6. **Notification Service** — `apps/slack/services.py`
   - `SlackNotificationService` with `notify()`, `_should_notify()`, `_send()`, `_handle_failure()`
   - Rate limiting (in-process sleep)
   - Auto-deactivation at 10 consecutive failures

7. **Signal Handler** — `apps/slack/signals.py`
   - `post_save` on `Activity` model → enqueue Celery task

8. **Celery Task** — `apps/slack/tasks.py`
   - `deliver_slack_notifications` task

9. **Test Message Helper** — add to `apps/slack/services.py`:
   ```python
   def send_test_message(webhook: SlackWebhook) -> dict:
       payload = {
           "text": "FrontierCRM Slack integration is working! 🎉",
           "blocks": [
               {
                   "type": "section",
                   "text": {"type": "mrkdwn", "text": "✅ *FrontierCRM Slack integration is working!* 🎉\nYou'll receive notifications when deals change stages, deals are won/lost, and new emails arrive from contacts."},
               },
               {
                   "type": "context",
                   "elements": [{"type": "mrkdwn", "text": f"Configured at {timezone.now().isoformat()}"}],
               },
           ],
       }
       resp = requests.post(webhook.webhook_url, json=payload, timeout=10)
       if resp.status_code == 200:
           return {"status": "delivered"}
       return {"status": "failed", "error": resp.text[:500]}
   ```

### Phase 5c: Frontend (estimated: 1 day)

10. **API hook** — `frontend/src/api/slack.ts`
    - `useSlackWebhooks()` — fetch list
    - `useCreateSlackWebhook()` — POST
    - `useUpdateSlackWebhook()` — PATCH
    - `useDeleteSlackWebhook()` — DELETE
    - `useTestSlackWebhook()` — POST to test endpoint
    - `useDeactivateSlackWebhook()` — POST to deactivate endpoint

11. **Page** — `frontend/src/pages/settings/slack-page.tsx`
    - Full page with loading → empty → list states
    - Inline add/edit form

12. **Components**
    - `SlackWebhookCard.tsx` — card with display name, channel, event badges, action buttons
    - `SlackWebhookForm.tsx` — form with validation (webhook URL pattern, required fields)
    - `SlackTestResultBanner.tsx` — success/error/toast notification

13. **Route registration** — Add to settings router in `frontend/src/routes.tsx`:
    ```tsx
    <Route path="integrations/slack" element={<SlackSettingsPage />} />
    ```

14. **Settings nav update** — Add "Slack" to the settings sidebar under "Integrations" section

---

## 8. Acceptance Criteria

### Backend

- [ ] `SlackWebhook` model creates table `slack_webhook` with all specified fields
- [ ] `GET /api/slack/webhooks/` returns tenant-scoped list (empty array when none configured)
- [ ] `POST /api/slack/webhooks/` creates a new webhook, rejects invalid URLs
- [ ] `PATCH /api/slack/webhooks/{id}/` updates individual fields
- [ ] `DELETE /api/slack/webhooks/{id}/` removes the webhook
- [ ] `POST /api/slack/webhooks/{id}/test/` sends a test message; returns `{"status": "delivered"}` on success, `{"status": "failed", "error": "..."}` on failure
- [ ] `POST /api/slack/webhooks/{id}/deactivate/` sets `is_active=false`
- [ ] Signal handler fires when an `Activity` is created (enqueues Celery task)
- [ ] Celery task loads Activity, calls `SlackNotificationService.notify()`
- [ ] Rate limiter prevents >1 POST/second to the same webhook URL
- [ ] After 10 consecutive failures, webhook auto-deactivates (`is_active=false`)
- [ ] Pipeline filter scopes notifications — deals not in the filtered pipeline are skipped
- [ ] Empty `subscribed_events` = notify on every activity type
- [ ] `Test user isolation:` tenant A's slack webhooks don't receive tenant B's activity notifications
- [ ] **Metadata verification:** `Activity.metadata` for existing deal stage change and email activities already contains the keys required by Slack formatters (`deal_name`, `from_stage`, `to_stage`, `value`, `owner_name` for deals; `from_name`, `from_email`, `subject`, `snippet`, `direction` for emails). If not, the relevant Activity creation code must be updated.

### Frontend

- [ ] Slack settings page renders at `/settings/integrations/slack`
- [ ] Empty state shows "No Slack webhooks configured" with add prompt
- [ ] Loading state shows skeleton cards
- [ ] Error state shows retryable error banner
- [ ] Add form validates webhook URL format (must match `https://hooks.slack.com/services/*`)
- [ ] Edit form pre-populates existing values
- [ ] Test button sends test message and shows success/error toast
- [ ] Remove button shows confirmation dialog, then deletes
- [ ] Auto-deactivated webhooks show warning badge with reactivate option
- [ ] Event checkboxes pre-ticked for defaults: stage change, won/lost, email
- [ ] Pipeline filter dropdown fetches available pipelines for the tenant

### Integration

- [ ] Creating a deal through the API → Activity created → Slack notification delivered (smoke test with a real Slack incoming webhook or mocked `requests.post`)
- [ ] Changing a deal stage → Activity created → Slack notification with block kit format
- [ ] Winning/losing a deal → Activity created → Slack notification with emoji + status
- [ ] Inbound email synced → Activity created → Slack notification with snippet
- [ ] Disabling a webhook → no further notifications for that webhook

---

## 9. Open Questions / Spike Items

| # | Question | Who | Decision |
|---|----------|-----|----------|
| 1 | Do existing deal update views (`apps/pipelines/views.py`) already populate `Activity.metadata` with `deal_name`, `from_stage`, `to_stage`, `value`, `owner_name`? If not, need to add those keys. | Atlas | Verify by inspecting `perform_update` in deal ViewSet |
| 2 | Same question for inbound email activity creation — does the Gmail sync code set `contact_id`, `from_name`, `from_email`, `snippet` in metadata? | Atlas | Verify in `apps/sync/tasks.py` |
| 3 | Should we use a Redis-backed rate limiter instead of in-process `time.sleep()` from the start? | Atlas | For P3, in-process is fine. Spike if >1 activity/sec per webhook is expected. |
| 4 | Should `subscribed_events` use the existing `Activity.ActivityType` enum values directly (string matching) or define a separate Slack event enum? | Atlas | Use the existing enum values. No need for another mapping layer. |
| 5 | How should we handle Slack webhook URL rotation (user revokes/recreates the webhook in Slack)? | Builder | User must update the webhook URL in the Slack settings page. No auto-detection of revoked URLs. |

---

**End of Phase 5 Slack Notifications Specification**