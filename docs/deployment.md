# Deployment Guide — FrontierCRM

Infrastructure runs on [Fly.io](https://fly.io). Two apps: **API** (`frontiercrm-api`) and **Frontend** (`frontiercrm-web`).

## Environments

| Environment | API URL | App URL | Fly app (API) | Fly app (Web) |
|-------------|---------|---------|---------------|---------------|
| Production | https://api.frontiercrm.com | https://app.frontiercrm.com | `frontiercrm-api` | `frontiercrm-web` |
| Staging | https://api-staging.frontiercrm.com | https://staging.frontiercrm.com | `frontiercrm-api-staging` | `frontiercrm-web-staging` |

## CI/CD pipeline

Push-based deployment. GitHub Actions workflow: `.github/workflows/ci.yml`.

```
Push to develop ──► CI (lint + test + frontend build)
                         │
                    Deploy staging
                         │
PR to main ──► CI (lint + test + build + docker) ──► Deploy prod
                                                         │
                                                    Run migrations
                                                         │
                                                    Post-deploy health check
```

## Manual deploy

Prerequisites:

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Authenticate
flyctl auth login
# OR set FLY_API_TOKEN env var for headless
```

### Deploy both API + frontend

```bash
# From repo root, on main branch
./scripts/deploy.sh
```

### Deploy API only

```bash
./scripts/deploy.sh --app api
```

### Deploy frontend only

```bash
./scripts/deploy.sh --app web
```

### Deploy to staging

```bash
./scripts/deploy.sh --staging
```

### Deploy a specific version

```bash
git tag v1.2.3
git push origin v1.2.3
./scripts/deploy.sh --version v1.2.3
```

## Verify the deploy

```bash
# API health
curl -sSf https://api.frontiercrm.com/api/health/ | python -m json.tool
# Expected: {"status":"ok","service":"frontiercrm-api"}

# Frontend
curl -sSf -o /dev/null https://app.frontiercrm.com/ && echo "Frontend OK"

# Ready check (includes DB)
curl -sSf https://api.frontiercrm.com/api/health/ready/ | python -m json.tool
# Expected: {"status":"ok","database":"connected"}
```

## Rollback

### Rollback to previous release

```bash
./scripts/rollback.sh
# Type 'rollback' to confirm
```

### Rollback to a specific version

```bash
./scripts/rollback.sh --version v1.2.0
```

### Rollback frontend only

```bash
./scripts/rollback.sh --app web
```

### Rollback staging

```bash
./scripts/rollback.sh --staging
```

### List available releases

```bash
./scripts/rollback.sh --list
```

### Rollback blast radius

- API: ~5s 503 during process swap. WebSocket connections drop.
- Frontend: ~2s 503 during nginx restart. Refresh resolves.
- Rollback does NOT revert database migrations. If the rollback is caused by a bad migration:

```bash
# 1. Reverse the migration manually
# 2. Then rollback the code
flyctl ssh console -a frontiercrm-api -C "python manage.py migrate <app> <previous_migration>"
./scripts/rollback.sh
```

## Database migrations

Always deploy **code first**, then run migrations. Code should handle both old and new schemas.

### Run pending migrations

```bash
./scripts/migrate.sh
```

### Dry run (check what's pending)

```bash
./scripts/migrate.sh --check
```

### Migrate one app only

```bash
./scripts/migrate.sh --app accounts
```

### Manual migration (for long-running/risky operations)

```bash
flyctl ssh console -a frontiercrm-api
python manage.py migrate --noinput
exit
```

### Reverse a migration

```bash
flyctl ssh console -a frontiercrm-api
python manage migrate <app_name> <previous_migration_name>
exit
```

### Migration safety checklist

- [ ] Deploy code BEFORE running migrations (new code handles both schemas)
- [ ] Reverse migrations tested on staging first
- [ ] Large tables: add non-nullable columns with a default, not nullable
- [ ] Bad rename: create new column + copy + drop old (not direct rename)

## Scaling

### API — scale vertically

```bash
flyctl scale vm shared-cpu-2x --app frontiercrm-api
flyctl scale memory 1024 --app frontiercrm-api
```

### API — scale horizontally

```bash
flyctl scale count 3 --app frontiercrm-api
```

Auto-scaling target is 1 per region by default. Fly.io adds/removes machines based on concurrency `soft_limit` in `fly.toml`.

### Celery workers

```bash
flyctl scale count 2 --app frontiercrm-api --process-group worker
```

### Frontend

```bash
flyctl scale count 3 --app frontiercrm-web
flyctl scale vm shared-cpu-0.5x --app frontiercrm-web
```

### Check current resource usage

```bash
flyctl status -a frontiercrm-api
flyctl status -a frontiercrm-web
```

### Scaling decision guide

| Signal | Action |
|--------|--------|
| API p99 > 500ms | Scale CPU or add machines |
| Celery queue backlogging | Increase worker count |
| Frontend slow to serve | Scale web machines or increase nginx cache |
| Database CPU > 80% | Scale DB plan (`flyctl postgres update`) |

## Secrets management

All secrets set via `flyctl secrets` — never commit `.env` to git.

### Set a secret

```bash
flyctl secrets set DATABASE_URL=postgresql://... --app frontiercrm-api
```

### Set multiple secrets from a file

```bash
flyctl secrets import --app frontiercrm-api < .env.prod
```

### List secrets (names only)

```bash
flyctl secrets list --app frontiercrm-api
```

### Remove a secret

```bash
flyctl secrets unset SECRET_NAME --app frontiercrm-api
```

Rotating a secret requires a deploy (new release) to take effect. Setting secrets via the CLI triggers an auto-deploy on Fly.io.

## Infrastructure

```
                          ┌─────────────┐
                          │  Cloudflare  │
                          │  (DNS + R2)  │
                          └──────┬──────┘
                                 │
                    ┌────────────┴────────────┐
                    │       Fly.io Proxy       │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
     ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
     │  API Server  │   │  Frontend    │   │  Meilisearch │
     │  Gunicorn    │   │  Nginx SPA   │   │  (Search)    │
     │  :8000       │   │  :80/443     │   │              │
     └──────┬───────┘   └──────────────┘   └──────────────┘
            │
     ┌──────┴───────┐
     │  Postgres    │
     │  Fly Postgres│
     └──────────────┘
            │
     ┌──────┴───────┐
     │  Redis       │
     │  (Cache+Q)   │
     └──────────────┘
```

## Production Dockerfiles

- `backend/Dockerfile.prod` — Multi-stage: Python 3.11-slim build + runtime. Gunicorn with 4 workers, health check.
- `frontend/Dockerfile.prod` — Multi-stage: Node 22 build → nginx:1.27-alpine runtime. SPA config.

## VM specs (fly.toml defaults)

| Process | Size | Memory | CPUs |
|---------|------|--------|------|
| app (gunicorn) | shared-cpu-1x | 512 MB | 1 |
| worker (celery) | shared-cpu-0.25x | 256 MB | 1 |
| beat (celery) | shared-cpu-0.25x | 256 MB | 1 |

## Celery Beat schedule

| Task | Interval | Description |
|------|----------|-------------|
| Meilisearch reindex | Every 15 min | Sync contacts/deals to search index |
| Gmail sync | Every 10 min | Sync inboxes for all connected users |
| Database backup | Every 24h | pg_dump → R2 (02:00 UTC) |
| Token cleanup | Every 6h | Remove expired tokens |
| Uptime heartbeat | Every 5 min | Ping Healthchecks.io |