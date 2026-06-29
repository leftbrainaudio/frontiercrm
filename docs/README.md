# FrontierCRM MVP

FrontierCRM is an open-source, multi-tenant CRM platform built for modern sales teams. Manage contacts, deals, pipelines, email, tasks, and teams — all behind a single API.

## Quick links

| What | Where |
|------|-------|
| Production app | https://app.frontiercrm.com |
| Production API | https://api.frontiercrm.com |
| Staging app | https://staging.frontiercrm.com |
| API health check | https://api.frontiercrm.com/api/health/ |
| API ready check | https://api.frontiercrm.com/api/health/ready/ |
| API schema | https://api.frontiercrm.com/api/schema/ |
| Docs index | `docs/` |

## Architecture

```
User ──► Cloudflare (DNS + R2)
              │
         Fly.io Proxy
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
  API ─── Postgres ─── Redis
  (4 gunicorn workers)  (cache + queue + WebSocket)
     │        │
     ▼        ▼
  Celery    Meilisearch
  (worker   (full-text search)
   + beat)
     │
  Frontend (Nginx SPA)
```

**API** — Django 5.2 REST framework, multi-tenant. JWT auth. WebSocket support via Channels.
**Frontend** — React 19 + TypeScript + Vite, TanStack Query, Zustand.
**Workers** — Celery 5.4 with Redis broker for async email sync, search indexing, backups.
**Search** — Meilisearch for full-text search across contacts, deals, and tasks.
**Storage** — Cloudflare R2 (S3-compatible) for file uploads.
**Infrastructure** — Fly.io: rolling deploys, zero-downtime, auto-scaling.

## Tech stack

| Layer | Stack |
|-------|-------|
| Backend | Python 3.11, Django 5.2, DRF 3.16 |
| Frontend | React 19, TypeScript 6, Vite 8, Tailwind 4 |
| Database | PostgreSQL 16 |
| Cache & Queue | Redis 7 |
| Search | Meilisearch 1.12 |
| Async | Celery 5.4 + Channels 4.2 |
| Auth | JWT (SimpleJWT), Magic Link, Google OAuth |
| Infrastructure | Fly.io, Docker |
| Object storage | Cloudflare R2 |
| CI/CD | GitHub Actions |
| Monitoring | Sentry, Healthchecks.io, Slack |

## Apps

| App | Endpoint | Description |
|-----|----------|-------------|
| Accounts | `/api/accounts/` | Users, roles, memberships |
| Contacts | `/api/contacts/` | Contacts + accounts |
| Pipelines | `/api/deals/` | Pipelines, stages, deals |
| Activities | `/api/activities/` | Activity timeline |
| Email | `/api/emails/` | Gmail sync (inbound/outbound) |
| Notes | `/api/notes/` | Free-form notes |
| Tasks | `/api/tasks/` | Task management |
| Teams | `/api/teams/` | Team management |
| Webhooks | `/api/webhooks/` | Outbound webhook delivery |
| Files | `/api/files/` | File uploads to R2 |
| Search | `/api/search/` | Full-text search via Meilisearch |

## Documentation index

| Document | Audience | What it covers |
|----------|----------|----------------|
| `ONBOARDING.md` | Everyone | One-page landing summary of the whole system |
| `developer-setup.md` | Developers | Prerequisites, local dev, env vars, Docker |
| `api.md` | API consumers | Endpoints, auth, rate limits, pagination |
| `deployment.md` | Operators | Deploy, rollback, migrate, scale |
| `user-guide.md` | End users | Quickstart, feature tour, FAQ |
| `admin-guide.md` | Administrators | Settings, teams, integrations, billing |
| `runbook.md` | On-call | Incident response, backup/restore, monitoring |
| `changelog.md` | Everyone | Release history |

## Project structure

```
frontiercrm/
├── backend/
│   ├── apps/             # Django apps (accounts, contacts, pipelines, ...)
│   ├── config/           # Django settings, URLs, ASGI, Celery
│   ├── tests/            # Backend test suite (411+ tests)
│   ├── docker-compose.yml
│   ├── Dockerfile        # Dev Dockerfile
│   └── Dockerfile.prod   # Production multi-stage build
├── frontend/
│   ├── src/              # React components, pages, API client, types
│   ├── nginx.conf        # SPA nginx config
│   └── Dockerfile.prod   # Production multi-stage build
├── scripts/              # Operational scripts
│   ├── deploy.sh
│   ├── rollback.sh
│   ├── backup.sh
│   ├── migrate.sh
│   ├── reindex.sh
│   └── setup-fly.sh
├── ops/                  # Operations documentation
│   ├── README.md
│   └── RUNBOOKS.md
├── docs/                 # Full documentation (you are here)
├── fly.toml              # Fly.io API config
└── .github/workflows/    # CI/CD pipelines
```

## Contributing

1. **Fork** the repo and create a feature branch from `develop`.
2. **Set up** your local environment (see `docs/developer-setup.md`).
3. **Run tests** before committing: `cd backend && pytest` (backend), `cd frontend && npm test` (frontend).
4. **Lint**: backend uses `ruff` (`ruff check .`), frontend uses `oxlint` (`npm run lint`).
5. **Open a PR** to `develop`. CI runs lint + test + build automatically.
6. Merge to `main` when approved. CI deploys to production.