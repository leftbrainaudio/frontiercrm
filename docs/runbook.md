# Runbook — FrontierCRM Operations

All operations runbooks in **Symptom → Command → Expected Output → Failure Mode** format.

Environment facts:

| Resource | Production | Staging |
|----------|-----------|---------|
| API app | `frontiercrm-api` | `frontiercrm-api-staging` |
| Frontend app | `frontiercrm-web` | `frontiercrm-web-staging` |
| App URL | https://app.frontiercrm.com | https://staging.frontiercrm.com |
| API URL | https://api.frontiercrm.com | https://api-staging.frontiercrm.com |
| Database | Fly Postgres (or Neon) from `DATABASE_URL` | Same structure, staging DB |
| Cache/Queue | Fly.io Redis | Fly.io Redis |
| Search | Meilisearch on Fly.io | Meilisearch on Fly.io |
| Blob store | Cloudflare R2 | Cloudflare R2 (same bucket) |
| Errors | Sentry | Sentry |
| Uptime | Healthchecks.io | — |

---

## 1. Deploy API + Frontend

**Symptom**: "We need to deploy new code to production."

**Command**:

```bash
# From repo root, main branch
cd ~/frontiercrm
git checkout main && git pull
./scripts/deploy.sh
```

**Expected output** (abbreviated):

```
══════════════════════════════════════════════════════════════
  FrontierCRM Deploy
  Environment: production
  App:         all
══════════════════════════════════════════════════════════════

[deploy] Deploying API (frontiercrm-api)...
  (flyctl output: building, pushing, releasing)
[deploy] Running database migrations...
  Operations to perform:
    Apply all migrations: admin, auth, ...
  Running migrations:
    No migrations to apply.
[deploy] Waiting for API health check...
  {"status":"ok","service":"frontiercrm-api"}
[deploy] API ready.
[deploy] Deploying frontend (frontiercrm-web)...
  (flyctl output: building, pushing, releasing)
[deploy] Frontend ready.
══════════════════════════════════════════════════════════════
  Deploy complete!
  API:  https://api.frontiercrm.com
  Web:  https://app.frontiercrm.com
══════════════════════════════════════════════════════════════
```

**Failure mode**: If health check fails after deploy, the deploy script still returns exit 0 with a WARN message. Check manually:

```bash
flyctl logs -a frontiercrm-api --since 2m
flyctl ssh console -a frontiercrm-api -C "curl -s localhost:8000/api/health/"
```

---

## 2. Deploy API only

**Symptom**: "I only changed backend code and want to skip the frontend build."

**Command**:

```bash
./scripts/deploy.sh --app api
```

**Expected output**: Same as full deploy, but skips frontend.

**Failure mode**: Same as full deploy health check failure.

---

## 3. Deploy frontend only

**Symptom**: "I only changed frontend code."

**Command**:

```bash
./scripts/deploy.sh --app web
```

**Expected output**: Deploys frontend only, verifies with curl to app URL.

**Failure mode**: Frontend health check fails → check nginx config or build output.

---

## 4. Rollback to previous release

**Symptom**: "The deploy broke something. 5xx errors. Roll back."

**Command**:

```bash
./scripts/rollback.sh
# Type 'rollback' when prompted
```

**Expected output**:

```
⚠  ROLLBACK WARNING
   App:        frontiercrm-api
   Environment: production
   Target:     previous release

Blast radius:
  - Brief 503 during process swap (~5s)
  - WebSocket connections dropped
  - In-flight Celery tasks may be duplicated

Continue? (type 'rollback' to confirm): rollback
[rollback] Starting rollback of frontiercrm-api...
[rollback] Rolling back to previous release...
  (flyctl output)
[rollback] Waiting for app to stabilise...
[rollback] Verifying API health...
  {"status":"ok","service":"frontiercrm-api"}
[rollback] API health check passed
[rollback] Rollback of frontiercrm-api complete.
```

**Failure mode**: "No previous release to rollback to." Run `./scripts/rollback.sh --list` to see available versions, then `./scripts/rollback.sh --version <specific-version>`.

**IMPORTANT**: Rollback does NOT revert database migrations. If migration damage caused the incident, reverse the migration first:

```bash
flyctl ssh console -a frontiercrm-api -C "python manage.py migrate <app> <previous_migration>"
./scripts/rollback.sh
```

---

## 5. Database migration

**Symptom**: "We added a new model/field and need to migrate."

**Command**:

```bash
# Deploy code first, then:
./scripts/migrate.sh
```

**Expected output**:

```
[migrate] Running migrations on frontiercrm-api...
Operations to perform:
  Apply all migrations: contacts, pipelines
Running migrations:
  Applying contacts.0002_add_phone_index... OK
[migrate] Migrations complete.
```

**Failure mode**: Migration fails with "column already exists" or "relation does not exist". The script exits non-zero. SSH in to see the error:

```bash
flyctl ssh console -a frontiercrm-api -C "python manage.py migrate --noinput 2>&1"
```

**Pre-flight check**:

```bash
./scripts/migrate.sh --check
```

Expected output:

```
[migrate] Pending migrations:
  [X] contacts.0002_add_phone_index
  [ ] pipelines (no pending)
  ...
```

---

## 6. SEV-1: Site down

**Symptom**: "app.frontiercrm.com returns 502/503 for all users."

**Panic?**: No. Follow the steps in order.

**Step 1 — Confirm it's not just you**:

```bash
curl -sSf --max-time 5 https://app.frontiercrm.com/ > /dev/null && echo "reaches browser" || echo "FAILS"
```

**Step 2 — Check Fly.io status**:

```bash
curl -sSf https://status.fly.io/ | grep -i "incident" || echo "No Fly.io incident"
```

**Step 3 — Check API health**:

```bash
curl -s https://api.frontiercrm.com/api/health/ | python -m json.tool
```

**Expected**: `{"status":"ok","service":"frontiercrm-api"}`

**Failure modes**:

- `curl: (7) Connection refused` → API process crashed. Check logs:

```bash
flyctl logs -a frontiercrm-api --since 5m | tail -40
flyctl status -a frontiercrm-api
```

- `{"status":"degraded","database":"unreachable"}` → Database down. Check:

```bash
flyctl postgres list
flyctl postgres status -a frontiercrm-db
```

**Step 4 — Rollback if recent deploy**:

```bash
./scripts/rollback.sh
```

**Step 5 — Communicate**:

```
Post in #ops-alerts:
  SEV-1: app.frontiercrm.com unreachable.
  Cause: [brief root cause from logs].
  Action: rolling back to [version].
  ETA: ~2 min.
```

**Step 6 — Resolve**:

- Once stable, investigate root cause.
- File a GitHub issue.
- Post-mortem within 48h.

---

## 7. SEV-2: Degraded performance

**Symptom**: "The app is slow. p99 > 1s, or 5xx > 1% of requests."

**Commands** (run in order):

```bash
# 1. Check Sentry for error spike
# Open https://sentry.io/organizations/<org>/frontiercrm/

# 2. Check Fly.io metrics
flyctl metrics -a frontiercrm-api

# 3. Check database
flyctl postgres db stats -a frontiercrm-db

# 4. Check Redis
flyctl redis status -a frontiercrm-redis

# 5. Check Celery queue depth
flyctl ssh console -a frontiercrm-api -C "celery -A config inspect active"
flyctl ssh console -a frontiercrm-api -C "celery -A config inspect reserved"

# 6. Scale up if resource-bound
flyctl scale vm shared-cpu-2x --app frontiercrm-api
```

**Expected output** (Fly metrics):

```
Requests:     120 req/s
p50:          45ms
p95:          280ms
p99:          850ms
Errors:       0.3%
```

**Failure mode**: If p99 > 1s or errors > 1%, escalate to SEV-1 and rollback.

---

## 8. Database backup (manual)

**Symptom**: "I need to take a backup before a risky migration."

**Command**:

```bash
./scripts/backup.sh
```

**Expected output**:

```
[20260628T020000Z] Starting database backup...
[20260628T020000Z] Full database dump (custom format)...
[20260628T020000Z] Backup size: 52428800 bytes
[20260628T020000Z] Uploading to s3://frontiercrm-backups/backups/database/frontiercrm_20260628T020000Z.sql.gz...
[20260628T020000Z] Upload complete.
[20260628T020000Z] Cleaning backups older than 30 days...
[20260628T020000Z] Backup complete: backups/database/frontiercrm_20260628T020000Z.sql.gz (52428800 bytes)
[20260628T020000Z] Retention: 30 days
```

**Failure modes**:

```
FATAL: pg_dump not found → Install postgresql-client
FATAL: DATABASE_URL is not set → Check env vars / flyctl secrets list
FATAL: AWS CLI not found → pip install awscli
```

---

## 9. Database restore

**Symptom**: "We need to restore data from a backup."

**Commands**:

```bash
# 1. List available backups in R2
aws s3 ls s3://frontiercrm-backups/backups/database/ \
  --endpoint-url https://<account>.r2.cloudflarestorage.com

# 2. Download the chosen backup
aws s3 cp s3://frontiercrm-backups/backups/database/frontiercrm_20260628T020000Z.sql.gz . \
  --endpoint-url https://<account>.r2.cloudflarestorage.com

# 3. Restore
gunzip -c frontiercrm_20260628T020000Z.sql.gz | psql "$DATABASE_URL"
```

**Expected output**: PostgreSQL restore output listing tables and row counts.

**Failure mode**: `psql: FATAL: database "frontiercrm" does not exist`. Create the database first:

```bash
createdb frontiercrm
```

**Warning**: Restoring overwrites the database. No undo. Take a backup first.

---

## 10. Common incidents

### 5xx errors after deploy

**Symptom**: Fresh deploy returns 500 errors.

**Cause**: Missing env vars, model changes without migrations, import errors.

**Immediate action**: Rollback.

```bash
./scripts/rollback.sh
```

**Investigate after rollback**:

```bash
flyctl logs -a frontiercrm-api --since 10m | grep -i error
flyctl ssh console -a frontiercrm-api -C "python -c 'import config.settings.production' 2>&1"
flyctl ssh console -a frontiercrm-api -C "python manage.py check --deploy 2>&1"
```

### Database connection pool exhausted

**Symptom**: API returns 500s with "connection pool exhausted" in logs.

**Commands**:

```bash
# 1. Check current connections
flyctl postgres db stats -a frontiercrm-db

# 2. Scale DB
flyctl postgres update -a frontiercrm-db

# 3. Worst case: restart DB (drops all connections)
flyctl postgres restart -a frontiercrm-db
```

### Redis OOM

**Symptom**: Cache misses increase. Celery tasks timeout.

```bash
# Connect to Redis
flyctl redis connect -a frontiercrm-redis

# At Redis prompt:
INFO memory
# Check used_memory_human vs maxmemory

# Flush cache
FLUSHALL
exit

# Scale up
flyctl redis update -a frontiercrm-redis --size 1
```

### Celery task backlog

**Symptom**: Email not syncing. Search index stale.

```bash
# Check queue depth
flyctl ssh console -a frontiercrm-api -C "celery -A config inspect active"
flyctl ssh console -a frontiercrm-api -C "celery -A config inspect reserved"

# Purge stuck tasks
flyctl ssh console -a frontiercrm-api -C "celery -A config purge -f"

# Scale workers
flyctl scale count 4 --app frontiercrm-api --process-group worker
```

### Meilisearch down

**Symptom**: Search returns 0 results or connection refused.

**Impact**: Degraded only. Frontend falls back to DB LIKE queries.

```bash
# Check service
flyctl status -a frontiercrm-search

# Restart
flyctl apps restart frontiercrm-search

# Rebuild index
./scripts/reindex.sh --drop-and-rebuild
```

---

## 11. SSH into production

```bash
flyctl ssh console -a frontiercrm-api
```

## 12. Tail logs

```bash
# API
flyctl logs -a frontiercrm-api

# Frontend
flyctl logs -a frontiercrm-web

# Celery worker
flyctl logs -a frontiercrm-api --process-group worker

# Specific time window
flyctl logs -a frontiercrm-api --since 30m
```

## 13. Debug a Django management command

```bash
flyctl ssh console -a frontiercrm-api -C "python manage.py <command>"
```

## 14. Test SMTP delivery

```bash
flyctl ssh console -a frontiercrm-api -C \
  "python -c \"from django.core.mail import send_mail; send_mail('Test','Body','noreply@frontiercrm.com',['admin@example.com'],fail_silently=False)\""
```

## 15. Monitoring alerts

| Trigger | Channel | Response |
|---------|---------|----------|
| 5xx > 1% in 5min | Slack #ops-alerts | Check logs, rollback if needed |
| p99 > 1s sustained | Slack #ops-alerts | Check metrics, scale up |
| Celery failure > 5% | Slack #ops-alerts | Check queue depth, purge if needed |
| DB connection pool exhausted | Slack #ops-alerts | Scale DB, restart pools |
| Fly.io machine crash | Slack #ops-alerts | Check Fly.io dashboard |
| Healthchecks.io silence (15 min) | Email/SMS | SSH in, check Celery Beat process |