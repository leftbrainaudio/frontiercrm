# Changelog — FrontierCRM MVP

## v1.3.0 (2026-06-30)

Post-Phase 5 release. Two-Factor Authentication, SSO/SAML, API Keys, Custom Fields UI, Audit Log UI, Bulk Operations, Outbound Webhook Delivery Engine, Calendar Event Creation, Email Templates.

### Features

**Two-Factor Authentication (P2)**
- TOTP-based 2FA setup with QR code scan → verification → recovery codes flow
- `POST /api/auth/2fa/setup/` — generates TOTP provisioning URI + QR code secret
- `POST /api/auth/2fa/confirm/` — verifies the setup with an initial TOTP token
- `POST /api/auth/2fa/verify/` — verifies a TOTP token at login (step 2 of 2FA challenge)
- `POST /api/auth/2fa/disable/` — disables 2FA on the current account
- `GET /api/auth/2fa/status/` — returns whether 2FA is enabled and recovery codes remaining count
- `POST /api/auth/2fa/recovery-codes/regenerate/` — regenerates recovery codes
- `POST /api/auth/2fa/admin/reset/{user_id}/` — admin endpoint to reset another user's 2FA
- Frontend: Settings → Security page with state machine: QR scan → verify → recovery codes → active
- `TwoFactorToken` JWT issued after password verification, consumed by 2FA verify step
- Recovery codes: 8 one-time-use codes, stored as bcrypt hashes
- Dependencies: `pyotp 2.10.0`, `bcrypt 5.0.0`

**SSO/SAML (P2)**
- `SamlProvider` model: entity ID, SSO URL, x509 certificate, JIT provisioning flag, default role, tenant-scoped
- `POST /api/auth/saml/login/` — initiates SP-initiated SAML login, returns IdP redirect URL
- `POST /api/auth/saml/{tenant_id}/acs/` — Assertion Consumer Service — processes SAML response, auto-provisions user on first login
- `GET /api/auth/saml/{tenant_id}/metadata/` — returns SP metadata XML for IdP configuration
- `GET /api/auth/saml/domain-check/` — checks if an email domain is linked to a SAML provider (for frontend redirect)
- `POST /api/auth/saml/logout/` — SAML single logout
- `GET/POST /api/auth/saml/providers/` — list or create SAML providers (tenant-scoped)
- `GET/PATCH/DELETE /api/auth/saml/providers/{id}/` — SAML provider CRUD
- SSO domain detection on login page — auto-redirects to IdP when email domain matches a SAML provider
- Frontend: SAML callback route at `/auth/saml/callback`
- JIT provisioning: new users auto-created with configurable default role on first SAML login
- Dependencies: `python3-saml 1.16.0`

**API Keys (P2)**
- New `apps.apikeys` Django app at `/api/apikeys/`
- `APIKey` model: prefixed key (`fcrm_`), SHA-256 hashed storage, name, scopes, active/revoked status, expiry date
- DRF authentication backend — authenticate API requests with `Authorization: Bearer fcrm_...`
- `POST /api/apikeys/` — creates an API key, returns plaintext key once (copy-on-create)
- `GET /api/apikeys/` — lists API keys (masked, no plaintext)
- `GET /api/apikeys/{id}/` — detail view (masked)
- `POST /api/apikeys/{id}/revoke/` — revokes an API key
- `PATCH /api/apikeys/{id}/` — update name or scopes
- `DELETE /api/apikeys/{id}/` — deletes an API key
- Frontend: Settings → API Keys page with CreateKeyModal (copy-once flow), KeyCard with revoke/delete
- All endpoints tenant-scoped

**Custom Fields UI (P2)**
- `CustomFieldDef` model at `/api/core/custom-fields/`: name, key, field type, entity type, required flag, options (for select), display order
- Entity types: contacts, deals, accounts
- Field types: text, number, date, select
- `GET/POST /api/core/custom-fields/` — list or create custom field definitions
- `GET/PATCH/DELETE /api/core/custom-fields/{id}/` — custom field CRUD
- Frontend: Settings → Custom Fields page with full CRUD table (add, edit, delete)
- Custom fields displayed on contact detail page and pipeline page deal cards
- Custom field values stored in `custom_fields` JSONField on existing models

**Audit Log UI (P2)**
- Frontend page at `/settings/audit-log` with paginated table:
  - 6 columns: timestamp, user, action, entity type, entity name, details
- Filters: entity type, action type, date range (start/end date)
- Loading skeleton, error state with retry, contextual empty state
- Action type colour badges (create=green, update=blue, delete=red)
- Filter chips with "Clear All" — active filters shown as removable chips
- Sidebar navigation entry under Settings

**Bulk Operations (P2)**
- Frontend bulk select and batch action toolbar for contacts, deals, and accounts
- `BulkSelect` component — checkbox column with indeterminate state for "some selected"
- `SelectAllBanner` — "All N items selected. Select all X items?" with one-click select-all
- `BatchActionToolbar` — contextual toolbar appears when items are selected
- `BulkProgressBar` — progress tracking for async bulk jobs
- Batch action dialogs:
  - `BulkConfirmDialog` — generic delete confirmation with item count
  - `BulkAssignDialog` — assign selected items to a user
  - `BulkChangeStageDialog` — move deals to a new pipeline stage
  - `BulkChangeStatusDialog` — bulk change deal status (won/lost/abandoned)
  - `BulkTagDialog` — add, remove, or replace tags on selected items
- 7 API mutation hooks: useBulkDelete, useBulkAssign, useBulkChangeStage, useBulkChangeStatus, useBulkAddTag, useBulkRemoveTag, useBulkReplaceTags
- useBulkJob polling hook for progress tracking
- useBulkExportUrl hook for bulk CSV export
- Entity types supported: contact, deal, account

**Outbound Webhook Delivery Engine (P2)**
- `WebhookDeliveryService` class — testable delivery service with payload enrichment
- Django signal handlers: `Deal.post_save`, `Contact.post_save`, `Activity.post_save` — fire webhook deliveries on create/update
- Payload enrichment — hydrated deal/contact data with all relevant fields, not raw JSON
- HMAC-SHA256 signed payloads with `X-Signature-256` header for consumer verification
- `WebhookDeadEvent` model — dead-letter queue for events that exhausted retries
- `GET /api/webhooks/dead-events/` — list dead events (paginated, filterable by status, webhook, date range)
- `GET /api/webhooks/dead-events/{id}/` — dead event detail
- `POST /api/webhooks/dead-events/{id}/replay/` — re-queue a dead event for delivery
- Celery Beat: `retry_stale_webhooks` runs every 5 minutes, retries events past `next_retry_at`
- Celery Beat: `prune_dead_events` runs daily at 03:00 UTC, removes resolved/stale dead events
- Migration 0002: WebhookDeadEvent model added

**Calendar Event Creation and Push (P2)**
- Create Google Calendar events from CRM — `POST /api/sync/connections/calendar/events/`
- Push event updates to Google Calendar — `PATCH /api/sync/connections/calendar/events/{id}/`
- Delete events from Google Calendar — `DELETE /api/sync/connections/calendar/events/{id}/`
- List calendar events — `GET /api/sync/connections/calendar/events/`
- CalendarWatchChannel — manages push notification channels for real-time event updates
- Celery Beat: watch channel renewal schedule
- Frontend modal for event creation linked to deals and contacts
- Frontend event list view showing synced and created events

**Email Templates (P2)**
- 8 API endpoints for email template CRUD
- Frontend template editor with subject, body, and variable insertion
- Variable picker — insert contact/deal/account fields into template (e.g. `{{contact.first_name}}`, `{{deal.name}}`)
- `VariableResolver` — resolves template variables at send time with actual data
- Templates selectable from the compose modal — pick a template, populate from current entity
- Template library page at `/email/templates`

### Breaking Changes

- Deals and Contacts now fire webhook events on create/update via Django signals — existing WebhookEndpoint configurations receive enriched payloads automatically
- API Key authentication (`Authorization: Bearer fcrm_*`) bypasses 2FA verification — API keys are a separate auth path from session tokens
- Login flow now checks 2FA status — users with 2FA enabled must complete TOTP verification after password
- SAML JIT provisioning creates users on first login — ensure default role is configured before enabling

### New Celery Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `apps.webhooks.tasks.retry_stale_webhooks` | Every 5 min (Beat) | Retries webhook events past `next_retry_at` |
| `apps.webhooks.tasks.prune_dead_events` | Daily 03:00 UTC | Removes resolved/stale dead-letter events |
| Watch channel renewal | Per-channel schedule | Renews Google Calendar watch channels for push notifications |

### New Python Packages

- `pyotp==2.10.0` — TOTP generation and verification for 2FA
- `bcrypt==5.0.0` — recovery code hashing
- `python3-saml==1.16.0` — SAML SSO protocol implementation

### New Apps

- `apps.apikeys` registered in `INSTALLED_APPS` — API Keys at `/api/apikeys/`
- `apps.core` registered in `INSTALLED_APPS` — Custom Fields at `/api/core/custom-fields/`

### New URL Namespaces

- `/api/auth/2fa/` — 2FA setup, confirm, verify, disable, status, recovery codes, admin reset
- `/api/auth/saml/` — SAML login, ACS, metadata, domain check, logout, provider CRUD
- `/api/apikeys/` — API key CRUD + revoke
- `/api/core/custom-fields/` — Custom field definition CRUD
- `/api/webhooks/dead-events/` — Dead event list, detail, replay
- `/api/sync/connections/calendar/events/` — Calendar event CRUD
- `/email/templates` — email template library (frontend)
- `/settings/custom-fields` — custom fields settings (frontend)
- `/settings/audit-log` — audit log viewer (frontend)
- `/settings/security` — 2FA settings (frontend)
- `/settings/api-keys` — API key management (frontend)

### Documentation

- Updated changelog with post-Phase 5 entries (v1.3.0)
- Updated API docs with 2FA, SAML, API Keys, Custom Fields, Webhook Dead Events, Calendar Events, and Email Templates endpoints
- Updated user guide with 2FA setup, custom fields UI, bulk operations, email templates, calendar event creation, API keys
- Updated admin guide with 2FA admin reset, API keys management, outbound webhook delivery engine, audit log

### Resolved Limitations

The following limitations from v1.2.0 are now resolved:

- ~~No email templates~~ **Resolved in v1.3.0** — Email template editor, variable picker, and compose integration
- ~~No bulk operations~~ **Resolved in v1.3.0** — Full bulk select, edit, assign, tag, stage change on contacts, deals, and accounts
- ~~No webhook outbound events~~ **Resolved in v1.3.0** — Outbound Webhook Delivery Engine with signal-based triggers, enriched payloads, HMAC signatures, dead-letter queue, and replay
- ~~No two-factor authentication~~ **Resolved in v1.3.0** — TOTP-based 2FA with QR setup, recovery codes, admin reset
- ~~No audit log UI~~ **Resolved in v1.3.0** — Audit log page with filters, pagination, and action badges
- ~~No SSO/SAML~~ **Resolved in v1.3.0** — SAML provider CRUD, JIT provisioning, domain-based auto-redirect
- ~~No API keys~~ **Resolved in v1.3.0** — Key generation with `fcrm_` prefix, SHA-256 storage, copy-once flow
- ~~No custom fields UI~~ **Resolved in v1.3.0** — Custom field definition CRUD with 4 field types, displayed on contact detail and pipeline cards

### Remaining Limitations

- No CSV import (export only)
- No mobile app (PWA covers installability)
- No full managed billing (usage tracking API available)

---

## v1.2.0 (2026-06-30)

Phase 5 release. Calendar Sync, Slack Notifications, API Documentation (PWA), Progressive Web App.

### Features

**Calendar Sync (P2)**
- Google Calendar integration with OAuth 2.0 — connect calendar from Settings → Integrations
- Event sync via Google Calendar API with syncToken delta sync for efficient incremental updates
- Time-range fallback: full sync for the last 90 days if syncToken expires (HTTP 410)
- Per-user calendar OAuth: auth URL, callback, and auth status endpoints
- Automatically creates Activity entries for synced events — stored in `Activity.metadata` JSONField
- Events linked to contacts by email address match (participant → contact lookup within tenant)
- Sync window: 90 days past, 30 days future
- Celery Beat: `sync_all_calendars` task runs every 15 minutes
- Manual sync trigger: `POST /api/sync/connections/{id}/sync/` dispatches `sync_calendar_delta`
- Token refresh handled automatically — expired tokens trigger refresh before sync
- Frontend: Calendar OAuth in Settings → Integrations, auth status indicator with event count

**Slack Notifications**
- New `apps.slack` Django app with webhook CRUD at `/api/slack/webhooks/`
- `SlackWebhook` model: webhook URL, channel override, display name, subscribed event types, pipeline filter
- Signal-based delivery — activity creation auto-fires notifications to matching webhooks
- 4 Block Kit message templates: deal stage change, deal status change (won/lost), new activity, system alert
- Rate-limited delivery: 1 request/second per webhook, auto-deactivate after 10 consecutive failures
- Frontend: Slack settings page at Settings → Integrations → Slack, webhook URL input + validation
- Sidebar navigation entry to Slack integration page

**API Documentation (P3)**
- drf-spectacular 0.29.0 installed and configured with SPECTACULAR_SETTINGS + API tags
- Generated OpenAPI 3.0.3 schema at `GET /api/docs/schema/`
- Interactive Swagger UI at `GET /api/docs/swagger/`
- Auto-generated ReDoc documentation at `GET /api/docs/redoc/`
- 86 endpoints documented, 93 component schemas
- JWT bearer auth auto-documented; cookie auth as secondary scheme
- All three UI endpoints verified returning 200

**Progressive Web App (P3)**
- vite-plugin-pwa integration with `autoUpdate` register type
- Web app manifest: name "FrontierCRM", short name "Frontier", theme colour `#2563EB`, standalone display
- Service worker: NetworkFirst strategy for `/api/*` calls (24-hour TTL, 100-entry cap, 5s network timeout)
- Cache-first strategy for static assets (52 precached entries, ~2.7MB)
- iOS meta tags: `apple-mobile-web-app-capable`, `apple-touch-icon`, `theme-color`
- Installable on mobile home screens — no app store required
- Icon PNGs (192x192, 512x512) generated from logo-mark.svg

### Breaking Changes

- Gmail OAuth scope now shares Google Client ID with Calendar — no auth migration required
- SyncConnection trigger-sync endpoint now dispatches per-provider tasks (`sync_email_delta` for Gmail, `sync_calendar_delta` for Calendar)
- `sync_interval_seconds=0` behaviour fixed — now floors to 60s base instead of doubling

### New Celery Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `apps.sync.tasks_calendar.sync_all_calendars` | Every 15 min (Beat) | Polls all active Google Calendar connections for new/updated events |
| `apps.sync.tasks_calendar.sync_calendar_delta` | On-demand / Beat | Per-connection delta sync with syncToken + time-range fallback |
| `apps.slack.tasks.deliver_slack_notifications` | On activity create | Pushes Block Kit messages to matching Slack webhooks |

### New Python Packages

- `drf-spectacular==0.29.0` — OpenAPI schema generation, Swagger UI, ReDoc

### Frontend Dependencies

- `vite-plugin-pwa` — service worker + manifest generation
- `sharp` — build-time icon generation

### Infrastructure

- New app registered: `apps.slack` in `INSTALLED_APPS`
- New URL namespace: `/api/slack/` — Slack webhook CRUD
- New namespace: `apps.sync.connections.calendar` — Calendar OAuth + auth status endpoints
- New URL routes registered:

### Documentation

- Updated changelog with Phase 5 entries
- Updated API docs with calendar sync, Slack webhook, and OpenAPI schema endpoints
- Updated user guide with calendar integration, PWA install, Slack setup
- Updated admin guide with Slack webhook configuration and Calendar OAuth
- Updated roadmap with completed Phase 5 items

### Limitations (Post-Phase 5)

The following remain for post-MVP development:

- No CSV import (export only)
- No full managed billing (usage tracking API available)

*The following v1.2.0 limitations have been resolved in v1.3.0: Email Templates, Bulk Operations, Outbound Webhook Delivery Engine, Two-Factor Authentication, Audit Log UI, SSO/SAML, API Keys, Custom Fields UI.*

---

## v1.1.0 (2026-06-30)

Phase 4 release. Activity Timeline, Email Compose & Send, Pipeline Forecasting, CSV Export.

### Features

**Activity Timeline (P1)**
- Org-wide activity feed at `/timeline` with date-grouped cards, type icons, actor avatars, and entity links
- Filter by date range (presets: Today, This Week, This Month, Custom), activity type, and actor
- Dashboard widget showing latest 10 timeline items with "View full timeline" link
- Contact detail page links to filtered timeline (`?actor_id=`)
- Deal detail (via modal) links to filtered timeline (`?entity_type=deal&entity_id=`)
- Backend: `GET /api/activities/timeline/` — paginated, tenant-scoped, resolves actor names + entity references
- Infinite scroll + "Load more" pagination on the timeline page
- Skeleton loading states, empty states, error states on all views

**Email Compose & Send (P2)**
- Compose modal now sends email via Gmail API instead of saving as draft only
- Asynchronous send: `POST /api/emails/` creates record with `status=SENDING`, enqueues Celery task
- Status polling endpoint: `GET /api/emails/{id}/send-status/` returns `status` (`sending`/`sent`/`failed`), `error_message`, `message_id`
- Frontend polls every 2s with 30s timeout — shows sending state, success toast, or inline error
- Failed sends display error message with "Retry" or "Save as Draft" actions
- Activity entries created for both sent and failed outbound emails
- `perform_create` fails fast with clear error if no Gmail connection configured

**Pipeline Forecasting (P2)**
- Dedicated forecast page at `/forecast` with three projection models:
  - **Simple weighted**: `Σ(deal.value × stage.probability)` for all open deals
  - **Win-rate adjusted**: weighted pipeline × historical win rate
  - **Velocity-based**: deals grouped by estimated close month based on historical stage velocity
- Scenario toggle: Conservative (×0.8), Medium (×1.0), Optimistic (×1.15)
- What-if scenario analysis: select a stage + hypothetical close rate to see projected upside
- Per-deal forecast breakdown table (deal-by-deal with probability weight, projected value, estimated close)
- Date range selector: 3 months / 6 months / 12 months
- Backend: `GET /api/reports/forecast/` with `pipeline_id`, `quarter`, `range`, `scenario_stage`, `scenario_close_rate`, `confidence_level` params
- Skeleton loading, empty, and error states on all forecast views
- Route registered in sidebar navigation

**CSV Export (P2)**
- New `apps/export` app with streaming CSV endpoints at `/api/export/`:
  - `GET /api/export/contacts/` — all non-deleted contacts with account name, owner name
  - `GET /api/export/deals/` — all deals with stage, value, probability, weighted value, owner
  - `GET /api/export/reports/pipeline/` — pipeline report (deals by stage, count, total value)
- All exports are tenant-scoped, streaming via `StreamingHttpResponse` + csv module
- Owner names resolved in batch for performance
- Frontend export buttons wired to correct URLs (pipeline page, contacts page)

### Breaking Changes

- Pipeline page export URL changed from `/deals/deals/export_csv/` (broken) to `/export/deals/` (working)
- `send_gmail_message` Celery task signature changed: now accepts `(user_id, email_id)` instead of raw message fields — enqueues via `send_gmail_message.delay(user_id, email_id)`
- `EmailViewSet.perform_create` now requires a Gmail connection — returns 400 if `google_refresh_token` is missing

### New Celery Tasks

- `send_gmail_message` — refactored: accepts `email_id` (UUID) instead of raw fields, updates existing `EmailMessage` status and creates `Activity` entries for sent/failed outcomes

### New Python Packages

(none — all new code uses existing dependencies)

### Infrastructure

- New app registered: `apps.export` in `INSTALLED_APPS`
- New URL namespace: `/api/export/` — registered at project-level `config/urls.py`

### Documentation

- Updated changelog with Phase 4 entries
- Updated API docs with new endpoints (timeline, send-status, forecast, export)
- Updated user guide with activity timeline, email compose, forecasting, and CSV export sections
- Updated admin guide with CSV export notes
- Updated roadmap with completed Phase 4 items

### Limitations (Post-Phase 4)

The following remain for post-MVP development:

- No CSV import (export only)
- No email templates
- No bulk operations
- No calendar integration
- No mobile app
- No webhook outbound events (webhook CRUD exists, delivery engine is future work)
- No two-factor authentication
- No audit log UI (API exists)
- No SSO/SAML
- No API keys (user-bound auth only)
- No custom fields UI (API-only)
- No full managed billing (usage tracking API available)

---

## v1.0.0 (2026-06-28)

Initial MVP release. Ready for production pilot.

### Features

**Contacts**
- Full CRUD for contacts and accounts (companies)
- Rich contact profile: name, email, phone, mobile, job title, department, LinkedIn, Twitter, address
- Company record: domain, industry, employees, revenue, website
- Tags and custom fields on both contacts and accounts
- Soft-delete support (30-day retention)

**Pipeline & Deals**
- Visual kanban board with drag-and-drop
- Multiple pipelines with configurable stages
- Win probability tracking (stage-level default + per-deal override)
- Weighted pipeline value (deal value × win probability)
- Deal statuses: open, won, lost, abandoned
- Stage change tracking with timestamps

**Activities**
- Unified activity timeline across contacts, deals, and accounts
- Activity types: note, call, email, meeting, task, stage change, status change, file_upload, system
- Linked to specific entities

**Email**
- Gmail / Google Workspace integration via OAuth 2.0
- Inbound and outbound sync (every 10 minutes via Celery Beat)
- Thread view with read/starred tracking
- Email linked to contacts by sender/recipient matching

**Tasks**
- Priority levels: low, medium, high, urgent
- Status tracking: todo, in_progress, done, cancelled
- Assignee support
- Entity-linked tasks

**Teams & Roles**
- Multi-tenant isolation (each organization gets a private workspace)
- Role-based access control (Owner, Admin, Member, Viewer + custom roles)
- Team grouping
- Membership management with invite system

**Search**
- Full-text search via Meilisearch (contacts, deals, tasks)
- Prefix search support
- Auto-reindex every 15 minutes via Celery Beat

**Authentication**
- Email + password signup/login
- JWT tokens (30-min access, 7-day refresh)
- Magic link passwordless login
- Google OAuth with Gmail scope
- Token rotation on refresh

**Dashboard**
- Pipeline health metrics: total pipeline value, won value, win rate, active deals
- Deals-by-stage breakdown
- Tasks due count
- Recent activity

### Infrastructure

- **Deployment**: Fly.io — rolling deploys, zero-downtime, auto-scaling
- **CI/CD**: GitHub Actions — lint → test → build → deploy (staging + production)
- **Container**: Multi-stage Dockerfiles for backend (Python 3.11) and frontend (Node 22 → Nginx)
- **Process model**: Gunicorn (4 workers) + Celery worker + Celery Beat
- **Monitoring**: Sentry (errors), Healthchecks.io (uptime), Slack alerts
- **Backup**: Daily pg_dump to Cloudflare R2, 30-day retention
- **Storage**: Cloudflare R2 for file uploads

### API

- RESTful JSON API at `https://api.frontiercrm.com/api/`
- OpenAPI 3.0 schema at `/api/schema/`
- REST framework browsable API at `/api/docs/`
- Pagination: cursor-based (25 default, max 100)
- Filtering, search, and ordering on list endpoints
- Rate limiting: 100/hr anonymous, 1000/hr authenticated
- Multi-tenant isolation on all data endpoints
- WebSocket support via Django Channels

### Technical

- **Backend**: Python 3.11, Django 5.2, DRF 3.16, Celery 5.4, Channels 4.2
- **Frontend**: React 19, TypeScript 6, Vite 8, Tailwind 4, TanStack Query, Zustand
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Search**: Meilisearch 1.12
- **Auth**: argon2 password hashing, JWT (SimpleJWT), Magic Link, Google OAuth
- **Tests**: 411 backend tests passing, frontend component and render tests
- **Linting**: Ruff (backend), oxlint (frontend)

### Security

- HSTS preload (1 year), SSL redirect, secure cookies
- CORS restricted to configured origins
- XSS protection (DOMPurify on frontend)
- Multi-tenant data isolation
- Rate limiting on all endpoints
- Non-root containers
- Sentry error tracking (no PII collection)

### Limitations (MVP)

The following are recognized gaps for post-MVP development:

- ~~No CSV import/export~~ **Resolved in v1.1.0** — CSV export is now available (Pipeline, Contacts, and Pipeline Report)
- No email templates
- No bulk operations
- ~~No calendar integration~~ **Resolved in v1.2.0** — Google Calendar sync with OAuth, delta sync, and Activity integration
- No mobile app
- No webhook outbound events (webhook CRUD exists, delivery engine is future work) — UPDATE: Actually webhooks CRUD is available
- No two-factor authentication
- No audit log UI (API exists)
- No SSO/SAML
- ~~No reporting/analytics beyond dashboard~~ **Resolved in v1.1.0** — Pipeline Forecasting is now available
- No API keys (user-bound auth only)
- No custom fields UI (API-only)
- ~~No email compose UI (API-only for sending)~~ **Resolved in v1.1.0** — Email compose and send is now available in the UI
- No full managed billing — usage tracking API available