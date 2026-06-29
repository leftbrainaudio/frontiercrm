# FrontierCRM Ops

This directory contains operational documentation and configuration for the FrontierCRM MVP deployment.

## Contents

| File | Purpose |
|------|---------|
| `RUNBOOKS.md` | Complete operations reference: deploy, rollback, migrate, scale, incident response, backup/restore, secrets, monitoring |
| (FUTURE) `incident-reports/` | Post-mortems after incidents |

## Quick Links

- **Deploy**: `../scripts/deploy.sh`
- **Rollback**: `../scripts/rollback.sh`
- **Migrate**: `../scripts/migrate.sh`
- **Backup**: `../scripts/backup.sh`
- **Setup Fly.io**: `../scripts/setup-fly.sh`
- **Reindex**: `../scripts/reindex.sh`

## Infrastructure Map

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

## Key URLs

- Production app:  https://app.frontiercrm.com
- Production API:  https://api.frontiercrm.com
- Staging app:     https://staging.frontiercrm.com
- Staging API:     https://api-staging.frontiercrm.com
- Sentry:          https://sentry.io/organizations/<org>/frontiercrm/
- Health check:    https://api.frontiercrm.com/api/health/
- Ready check:     https://api.frontiercrm.com/api/health/ready/

## Deploy Pipeline

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