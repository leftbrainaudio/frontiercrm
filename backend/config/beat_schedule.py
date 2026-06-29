# ── Celery Beat Schedule: FrontierCRM ────────────────────────────────────────
# Scheduled tasks for periodic maintenance operations.
# Loaded via celery.py or settings.

from datetime import timedelta

# ── Meilisearch Index Sync ────────────────────────────────────────────────────
# Rebuild/reindex contacts, deals, and tasks in Meilisearch.
# Runs every 15 minutes during business hours. For production, consider
# splitting into: full reindex (nightly) + delta sync (every 5 min).
MEILISEARCH_REINDEX_SCHEDULE = {
    "reindex-meilisearch": {
        "task": "apps.search.tasks.reindex_all",
        "schedule": timedelta(minutes=15),
        "options": {"expires": 300},  # Drop if previous run still active
    },
}

# ── Email Sync ────────────────────────────────────────────────────────────────
# Sync Gmail inbox for all users with OAuth tokens.
# Rate-limited by Gmail API quotas. Runs every 10 minutes.
EMAIL_SYNC_SCHEDULE = {
    "sync-all-gmail": {
        "task": "apps.email.tasks.sync_all_gmail",
        "schedule": timedelta(minutes=10),
        "options": {"expires": 200},
    },
}

# ── Database Backups (Production only) ────────────────────────────────────────
# pg_dump to R2. Runs daily at 02:00 UTC.
BACKUP_SCHEDULE = {
    "daily-db-backup": {
        "task": "apps.core.tasks.run_backup",
        "schedule": timedelta(hours=24),
        "options": {"expires": 3600},
    },
}

# ── Cleanup Expired Tokens ───────────────────────────────────────────────────
# Remove expired JWT refresh tokens and expired magic link tokens.
CLEANUP_SCHEDULE = {
    "cleanup-expired-tokens": {
        "task": "apps.accounts.tasks.cleanup_expired_tokens",
        "schedule": timedelta(hours=6),
    },
}

# ── Monitoring Pings ──────────────────────────────────────────────────────────
# Heartbeat to uptime monitoring service (Better Uptime / Healthchecks.io).
HEARTBEAT_SCHEDULE = {
    "uptime-heartbeat": {
        "task": "apps.core.tasks.send_heartbeat",
        "schedule": timedelta(minutes=5),
        "options": {"expires": 120},
    },
}

# ── Combined schedule ─────────────────────────────────────────────────────────
BEAT_SCHEDULE = {}
BEAT_SCHEDULE.update(MEILISEARCH_REINDEX_SCHEDULE)
BEAT_SCHEDULE.update(EMAIL_SYNC_SCHEDULE)
BEAT_SCHEDULE.update(BACKUP_SCHEDULE)
BEAT_SCHEDULE.update(CLEANUP_SCHEDULE)
BEAT_SCHEDULE.update(HEARTBEAT_SCHEDULE)