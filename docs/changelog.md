# Changelog — FrontierCRM MVP

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
- No email templates
- No bulk operations
- No mobile app (PWA covers installability)
- No webhook outbound events (webhook CRUD exists, delivery engine is future work)
- No two-factor authentication
- No audit log UI (API exists)
- No SSO/SAML
- No API keys (user-bound auth only)
- No custom fields UI (API-only)
- No full managed billing (usage tracking API available)

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