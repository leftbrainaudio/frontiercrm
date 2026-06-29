# ── FrontierCRM Runbooks ──────────────────────────────────────────────────────
# All operations runbooks for the FrontierCRM MVP deployment.
#
# Environment:
#   Production:   api=frontiercrm-api, web=frontiercrm-web, url=https://app.frontiercrm.com
#   Staging:      api=frontiercrm-api-staging, web=frontiercrm-web-staging, url=https://staging.frontiercrm.com
#   Database:     Fly Postgres (or Neon) — connection string in DATABASE_URL
#   Cache/Queue:  Fly.io Redis
#   Search:       Meilisearch on Fly.io
#   Blob store:   Cloudflare R2 (S3-compatible)
#   Monitoring:   Sentry (errors) + Healthchecks.io (cron) + Slack (alerts)

# ───────────────────────────────────────────────────────────────────────────────
# 1. DEPLOY RUNBOOK
# ───────────────────────────────────────────────────────────────────────────────

## 1.1 Deploy API + Web (Full Deploy)
#
# Blast radius: ~5s 503 during process swap per app. WebSocket reconnects.
# Rollback available via `scripts/rollback.sh` at any time.

# LOCAL (from main branch):
#   cd ~/frontiercrm
#   git checkout main && git pull
#   ./scripts/deploy.sh

# CI/CD (via GitHub Actions): push to `main` triggers automatic deploy.
#   git checkout main
#   git merge develop
#   git push origin main
#   # Monitor: https://github.com/<org>/frontiercrm/actions

## 1.2 Deploy API only
#   ./scripts/deploy.sh --app api

## 1.3 Deploy Web only
#   ./scripts/deploy.sh --app web

## 1.4 Deploy to Staging
#   ./scripts/deploy.sh --staging

## 1.5 Deploy a specific version
#   ./scripts/deploy.sh --version v1.2.3

## 1.6 Verify the deploy
#   curl -sSf https://api.frontiercrm.com/api/health/ | python -m json.tool
#   curl -sSf https://app.frontiercrm.com/ > /dev/null && echo "Frontend OK"
# Expected:
#   {"status":"ok","service":"frontiercrm-api"}
#
# If health check fails:
#   - Check flyctl logs:        flyctl logs -a frontiercrm-api
#   - Check Sentry dashboard:   https://sentry.io/organizations/<org>/issues/
#   - SSH in:                   flyctl ssh console -a frontiercrm-api

# ───────────────────────────────────────────────────────────────────────────────
# 2. ROLLBACK RUNBOOK
# ───────────────────────────────────────────────────────────────────────────────

## 2.1 Rollback to previous release
#   ./scripts/rollback.sh
#   # Enter 'rollback' to confirm

## 2.2 Rollback to a specific version
#   ./scripts/rollback.sh --version v1.2.0

## 2.3 Rollback frontend only
#   ./scripts/rollback.sh --app web

## 2.4 Rollback staging
#   ./scripts/rollback.sh --staging

## 2.5 List available releases
#   ./scripts/rollback.sh --list

# IMPORTANT: Rollback only reverts the application code. Database migrations
# are NOT reverted. If the rollback is caused by a bad migration (e.g. dropped
# column), first run the reverse migration manually, then rollback the code:
#   1. flyctl ssh console -a frontiercrm-api -C "python manage.py migrate <app> <previous_migration>"
#   2. ./scripts/rollback.sh

# ───────────────────────────────────────────────────────────────────────────────
# 3. DATABASE MIGRATION RUNBOOK
# ───────────────────────────────────────────────────────────────────────────────

## 3.1 Run pending migrations (normal operation)
#   # Deploy API first, THEN run migrations:
#   ./scripts/migrate.sh

## 3.2 Check what migrations are pending (dry run)
#   ./scripts/migrate.sh --check

## 3.3 Migrate only one app
#   ./scripts/migrate.sh --app accounts

## 3.4 Migrate staging
#   ./scripts/migrate.sh --staging

## 3.5 Manual migration (for long-running or risky operations)
#   flyctl ssh console -a frontiercrm-api
#   python manage.py migrate --noinput
#   exit

## 3.6 Reverse a migration
#   flyctl ssh console -a frontiercrm-api
#   python manage.py migrate <app_name> <previous_migration_name>
#   exit

# Migration safety checklist:
#   [ ] Deploy new code BEFORE running migrations (new code handles both schemas)
#   [ ] Reverse migrations MUST be tested on staging first
#   [ ] Large tables: add non-nullable columns with a default, not nullable
#   [ ] Bad rename: create new column + copy + drop old (not direct rename)

# ───────────────────────────────────────────────────────────────────────────────
# 4. SCALE RUNBOOK
# ───────────────────────────────────────────────────────────────────────────────

## 4.1 Scale API vertically (CPU/memory)
#   flyctl scale vm shared-cpu-2x --app frontiercrm-api
#   flyctl scale memory 1024 --app frontiercrm-api

## 4.2 Scale API horizontally (add machines)
#   flyctl scale count 3 --app frontiercrm-api
#   # Auto-scaling target is 1 per region by default; Fly.io adds/removes
#   # machines based on concurrency soft_limit (see fly.toml)

## 4.3 Scale Celery workers
#   flyctl scale count 2 --app frontiercrm-api --process-group worker

## 4.4 Scale web frontend
#   flyctl scale count 3 --app frontiercrm-web
#   flyctl scale vm shared-cpu-0.5x --app frontiercrm-web

## 4.5 Check current resource usage
#   flyctl status -a frontiercrm-api
#   flyctl status -a frontiercrm-web

# Decision guide:
#   - API p99 > 500ms: scale CPU or add machines
#   - Celery queue backlog: scale worker count
#   - Frontend slow to serve: scale web machines or increase nginx cache
#   - Database CPU > 80%: scale DB plan (Fly Postgres: flyctl postgres update)

# ───────────────────────────────────────────────────────────────────────────────
# 5. INCIDENT RESPONSE RUNBOOK
# ───────────────────────────────────────────────────────────────────────────────

## 5.1 Severity Levels
#
#   SEV-1: Site down or major feature broken for all users.
#          Response time: < 5 min, Page DRI (Directly Responsible Individual)
#   SEV-2: Feature broken for subset of users or degraded performance.
#          Response time: < 30 min
#   SEV-3: Minor issue, cosmetic, one-user bug.
#          Response time: next business day

## 5.2 SEV-1: Site Down
#
#   1. DETECT
#      - Alert via Slack (#ops-alerts) or PagerDuty
#      - Check: is it just you? https://downforeveryoneorjustme.com/app.frontiercrm.com
#      - Check: https://status.fly.io for platform outage
#
#   2. TRIAGE
#      flyctl logs -a frontiercrm-api --since 5m | tail -50
#      flyctl status -a frontiercrm-api
#      flyctl ssh console -a frontiercrm-api -C "curl -s localhost:8000/api/health/"
#
#   3. DECIDE: Rollback or Fix Forward?
#      - Rollback if: < 15 min since deploy, no schema changes
#      - Fix forward if: schema already changed, or root cause understood
#
#      ./scripts/rollback.sh
#
#   4. COMMUNICATE
#      - Post in #ops-alerts: "SEV-1: [description]. Rolling back to [version]."
#      - If ETA > 15 min: update status page
#
#   5. RESOLVE
#      - Once stable, investigate root cause
#      - File a bug/issue
#      - Post-mortem within 48h for SEV-1

## 5.3 SEV-2: Degraded Performance (p99 > 1s, 5xx > 1%)
#
#   1. Check Sentry for error spikes: https://sentry.io/<org>/frontiercrm/
#   2. Check flyctl metrics:
#      flyctl metrics -a frontiercrm-api
#   3. Check database:
#      flyctl postgres db stats -a frontiercrm-db
#   4. Check Redis:
#      flyctl redis status -a frontiercrm-redis
#   5. Check Celery:
#      flyctl ssh console -a frontiercrm-api -C "celery -A config inspect active"
#   6. Scale up if resource-bound:
#      flyctl scale vm shared-cpu-2x --app frontiercrm-api

## 5.4 SEV-3: Minor Issue
#
#   1. File a GitHub issue with reproduction steps
#   2. Assign to sprint
#   3. No immediate action required

## 5.5 Common Incidents

# 5xx errors after deploy:
#   - Rollback first: ./scripts/rollback.sh
#   - Then investigate root cause
#   - Common causes: missing env vars, model changes without migrations, import errors

# Database connection pool exhausted:
#   - Check CONN_MAX_AGE in settings (default 600s = 10 min)
#   - Scale DB: flyctl postgres update -a frontiercrm-db
#   - Worst case: restart DB (drops all connections)
#     flyctl postgres restart -a frontiercrm-db

# Redis OOM (out of memory):
#   - Connect to Redis: flyctl redis connect -a frontiercrm-redis
#   - Check memory:  INFO memory
#   - Flush cache:   FLUSHALL (only for cache db)
#   - Scale up:      flyctl redis update -a frontiercrm-redis --size 1

# Celery task backlog:
#   - Check queue depth:
#     flyctl ssh console -a frontiercrm-api -C "celery -A config inspect active"
#     flyctl ssh console -a frontiercrm-api -C "celery -A config inspect reserved"
#   - Purge stuck tasks:
#     flyctl ssh console -a frontiercrm-api -C "celery -A config purge -f"
#   - Scale workers: flyctl scale count 4 --app frontiercrm-api --process-group worker

# Meilisearch down:
#   - Check service: flyctl status -a frontiercrm-search
#   - Search falls back to DB LIKE queries (degraded, not broken)
#   - Restart: flyctl apps restart frontiercrm-search
#   - Rebuild index: ./scripts/reindex.sh --drop-and-rebuild

# ───────────────────────────────────────────────────────────────────────────────
# 6. BACKUP / RESTORE RUNBOOK
# ───────────────────────────────────────────────────────────────────────────────

## 6.1 Manual backup
#   ./scripts/backup.sh
#   # Uploads to s3://frontiercrm-backups/backups/database/YYYYMMDDTHHMMSSZ.sql.gz

## 6.2 Schema-only backup (fast, for CI checks)
#   ./scripts/backup.sh --schema-only

## 6.3 Download latest backup
#   aws s3 cp s3://frontiercrm-backups/backups/database/<filename> . \
#     --endpoint-url https://<account>.r2.cloudflarestorage.com

## 6.4 Restore from backup
#   # Download the backup file first
#   gunzip -c frontiercrm_20260628T120000Z.sql.gz | psql "$DATABASE_URL"
#   # or for custom format:
#   pg_restore -d "$DATABASE_URL" --no-owner --role=postgres frontiercrm.dump

## 6.5 Automated backup schedule
#   Runs daily at 02:00 UTC via Celery Beat (see backend/config/beat_schedule.py)

# ───────────────────────────────────────────────────────────────────────────────
# 7. DEBUGGING / TROUBLESHOOTING
# ───────────────────────────────────────────────────────────────────────────────

## 7.1 SSH into production
#   flyctl ssh console -a frontiercrm-api

## 7.2 Tail logs
#   flyctl logs -a frontiercrm-api
#   flyctl logs -a frontiercrm-web
#   flyctl logs -a frontiercrm-api --process-group worker

## 7.3 Run a Django management command
#   flyctl ssh console -a frontiercrm-api -C "python manage.py <command>"

## 7.4 Check Django settings (debug mode)
#   flyctl ssh console -a frontiercrm-api -C "python -c \"import os; print(os.environ.get('DJANGO_DEBUG'))\""

## 7.5 Test SMTP email delivery
#   flyctl ssh console -a frontiercrm-api -C \
#     "python -c \"from django.core.mail import send_mail; send_mail('Test','Body','noreply@frontiercrm.com',['admin@example.com'], fail_silently=False)\""

# ───────────────────────────────────────────────────────────────────────────────
# 8. SECRETS MANAGEMENT
# ───────────────────────────────────────────────────────────────────────────────

## 8.1 Set a secret
#   flyctl secrets set DATABASE_URL=postgresql://... --app frontiercrm-api
#   flyctl secrets set SENTRY_DSN=https://... --app frontiercrm-api

## 8.2 Set multiple secrets from .env
#   flyctl secrets import --app frontiercrm-api < .env.prod

## 8.3 List secrets (names only)
#   flyctl secrets list --app frontiercrm-api

## 8.4 Remove a secret
#   flyctl secrets unset SECRET_NAME --app frontiercrm-api

# NOTE: All secrets are set via `flyctl secrets` — never commit .env to git.
# Rotating a secret requires a deploy (new release) to take effect.
# Adding a new env var via fly.toml [env] section also requires a deploy.
# Setting secrets via CLI triggers an auto-deploy on Fly.io.

# ───────────────────────────────────────────────────────────────────────────────
# 9. MONITORING & ALERTING
# ───────────────────────────────────────────────────────────────────────────────

## 9.1 Sentry (error tracking)
#   Dashboard: https://sentry.io/organizations/<org>/frontiercrm/
#   Alerts configured for:
#     - 5xx errors: notify immediately
#     - New issue categories: group and notify
#     - Spike of 10+ errors in 5 min: notify

## 9.2 Healthchecks.io (uptime / cron monitoring)
#   - /api/health/ — checked every 30s from Fly.io
#   - Heartbeat from Celery Beat every 5 min
#   - Alert if no heartbeat for 15 min

## 9.3 Slack alerts
#   Channel: #ops-alerts
#   Alert triggers:
#     - 5xx error rate > 1% of requests in 5 min window
#     - p99 latency > 1s sustained for 5 min
#     - Celery task failure rate > 5%
#     - Database connection pool exhaustion
#     - Fly.io machine crash/restart

## 9.4 Manual alert test
#   # Trigger a test 500 error:
#   curl -X POST https://api.frontiercrm.com/api/test-500/ || true
#   # Or trigger via a non-existent endpoint:
#   curl -s https://api.frontiercrm.com/api/nonexistent/