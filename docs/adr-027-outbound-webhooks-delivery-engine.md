# ADR-027: Outbound Webhook Delivery Engine

**Status:** Proposed
**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)

## Context

FrontierCRM already has:

- `WebhookEndpoint` and `WebhookEvent` models with tenant scoping, event subscription, retry fields, and HMAC signature support
- A `dispatch_webhook` Celery task with exponential backoff (60s/120s/240s)
- A `webhook_receiver` public endpoint for *inbound* webhooks from external services
- The `SlackNotificationService` pattern — a dedicated service class + Celery task + Django signal for Activity-driven outbound delivery

What's missing for a complete outbound webhook delivery engine:

1. **No dedicated delivery service** — delivery logic lives in `views.py` as standalone functions, not a testable service class
2. **No outbound event triggers** — no signal handlers fire webhook deliveries when Deals change, Contacts update, or emails sync. The existing `dispatch_webhook` is only called from the inbound receiver
3. **No dead-letter queue** — failed events are simply marked `FAILED` with no retention policy, replay capability, or monitoring
4. **No Celery Beat retry sweep** — after a Celery task exhausts its own retries, there's no scheduled job to retry events whose `next_retry_at` has passed
5. **No signed payload spec for consumers** — the HMAC signature is computed but undocumented; consumers can't verify webhook origin
6. **No event enrichment** — payloads carry raw Activity JSON, not hydrated deal/contact data that consumers need

## Options Considered

### Option A — Extract delivery into a standalone service, add signal handlers, add dead-letter

Build a `WebhookDeliveryService` class (mirroring `SlackNotificationService`), add Django signal handlers for Deal, Contact, Activity models, add `WebhookDeadEvent` model, add Celery Beat retry sweep, and document the signed-payload format.

- **Pros:** Clean architecture; testable service; complete lifecycle (create → queue → deliver → retry → dead-letter); existing models reused without schema changes
- **Cons:** Significant migration of existing `views.py` logic; three new signal wiring points; new DB migration for dead-letter model

### Option B — Refactor views.py inline, add triggers as Celery tasks only (no signals)

Keep all delivery logic in `views.py`, add direct Celery task calls from Deal/Contact save methods. Skip dead-letter; keep existing `FAILED` status.

- **Pros:** Least code change; no new DB models; no signal wiring
- **Cons:** Delivery logic still untestable; no dead-letter replay; task-based triggers fragile; no signed-payload documentation

### Option C — Full event bus (Redis Streams / RabbitMQ)

Push all domain events onto a message broker. A dedicated consumer reads events and dispatches webhooks.

- **Pros:** Maximum decoupling; durability; multiple consumers possible
- **Cons:** Over-engineered for P2 scale; operational complexity (consumer groups, rebalancing, broker DLQ); adds system dependency with no current volume justification

## Decision

**Option A — Extract delivery into a standalone service, add signal handlers, add dead-letter.**

Rationale:

1. The existing `WebhookEndpoint`/`WebhookEvent` models are well-designed — they already have `status`, `attempt_count`, `next_retry_at`, `response_status`, `response_body`, `error_message`, and `max_retries`. The missing pieces each require minimal new code.
2. Extracting `WebhookDeliveryService` makes delivery logic unit-testable. Currently, testing requires mocking `requests.post` inside `views.py` — a service class lets tests inject a mock HTTP client.
3. Django signals are the established pattern (see `apps/slack/signals.py`). Adding `apps/webhooks/signals.py` with `post_save` handlers on Deal, Contact, and Activity keeps the pattern consistent.
4. A dead-letter model is cheap — one new table, no FK relationships to worry about. It makes failed deliveries inspectable and replayable from the admin.
5. The Celery Beat retry sweep is essential for reliability. When Celery restarts or a task fails to enqueue, PENDING events with stale `next_retry_at` dates accumulate. A periodic task sweeps these back into delivery.

**Rejected:** Option B (leaves developer experience and operational visibility poor). Option C (too much infrastructure for current scale).

## Consequences

- New file: `apps/webhooks/services.py` — `WebhookDeliveryService` class
- New file: `apps/webhooks/signals.py` — signal handlers for Deal, Contact, Activity
- New file: `apps/webhooks/tasks.py` — refactored Celery tasks (moved from views.py)
- New file: `apps/webhooks/admin.py` — admin registration for all webhook models
- New model: `WebhookDeadEvent` in `apps/webhooks/models.py`
- Migration: new `webhooks_dead_event` database table
- Celery Beat: one new periodic task every 5 minutes (`retry_stale_webhooks`) + daily cleanup (`prune_dead_events`)
- Updated docs: `api.md` and admin guide for consumer signature verification
- Existing `WebhookEndpoint` and `WebhookEvent` models — unchanged (backward compatible)
- Existing `views.py` — `webhook_receiver` untouched; `dispatch_webhook` and `_retry_or_fail` moved to tasks.py; `_compute_signature` moved to services.py and imported by both
- No recursive webhook loop risk — Activity signal handler can be gated on activity type

## Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Retry mechanism | Application-level via `next_retry_at` (not Celery task retries) | Observable, survives broker restart, no stack accumulation |
| Backoff formula | `60 * 2^(attempt-1)`, capped at 600s | Proven exponential backoff; cap prevents absurd delays |
| Payload enrichment | At delivery time, not enqueue time | Re-enrichment on retry picks up latest data |
| Signature header prefix | `X-FrontierCRM-` | Distinctive, namespaced, future-proof for multiple signing algos |
| Event subscription empties | Empty list = subscribe to all events | Same pattern as `SlackWebhook.subscribed_events` |
| Dead-event retention | 90 days, auto-pruned | Balances audit trail with storage hygiene |
