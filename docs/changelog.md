# Changelog — FrontierCRM MVP

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

- No CSV import/export
- No email templates
- No bulk operations
- No calendar integration
- No mobile app
- No webhook outbound events (webhook CRUD exists, delivery engine is future work) — UPDATE: Actually webhooks CRUD is available
- No two-factor authentication
- No audit log UI (API exists)
- No SSO/SAML
- No reporting/analytics beyond dashboard
- No API keys (user-bound auth only)
- No custom fields UI (API-only)
- No email compose UI (API-only for sending)
- No full managed billing — usage tracking API available