# FrontierCRM

Multi-tenant CRM platform for modern sales teams. Open-source. Dockerized. Deployed on Fly.io.

Manage contacts, deals, pipelines, email, tasks, and activities — all in one place.

## Quick links

|| What | Link |
||------|------|
|| Production app | https://app.frontiercrm.com |
|| Production API | https://api.frontiercrm.com |
|| API health | https://api.frontiercrm.com/api/health/ |
|| API schema (OpenAPI) | https://api.frontiercrm.com/api/docs/schema/ |
|| Swagger UI | https://api.frontiercrm.com/api/docs/swagger/ |
|| ReDoc | https://api.frontiercrm.com/api/docs/redoc/ |
|| **Documentation** | `docs/README.md` |
|| **One-page onboarding** | `docs/ONBOARDING.md` |

## Start here

- **New to the project?** Read `docs/ONBOARDING.md` (5-minute overview)
- **Setting up locally?** Read `docs/developer-setup.md`
- **Using the API?** Read `docs/api.md`
- **Deploying?** Read `docs/deployment.md`
- **On call?** Read `docs/runbook.md`
- **Administering?** Read `docs/admin-guide.md`
- **Using the app?** Read `docs/user-guide.md`
- **What changed?** Read `docs/changelog.md`

## Stack

- **Backend**: Python 3.11, Django 5.2, DRF 3.16, Celery 5.4, Channels 4.2
- **Frontend**: React 19, TypeScript 6, Vite 8, Tailwind 4, TanStack Query, Zustand
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Search**: Meilisearch 1.12
- **Infrastructure**: Docker, Fly.io, GitHub Actions, Cloudflare R2

## Project structure

```
backend/          Django REST API + Celery workers
frontend/         React SPA
scripts/          Deploy, rollback, backup, migrate, reindex
ops/              Operations documentation + runbooks
docs/             Full documentation suite
.github/          CI/CD pipelines
fly.toml          Fly.io API config
```

## License

Proprietary — all rights reserved.