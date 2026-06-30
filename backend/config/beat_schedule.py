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
# Rate-limited by Gmail API quotas.
EMAIL_SYNC_SCHEDULE = {
    "sync-all-gmail": {
        "task": "apps.email.tasks.sync_all_gmail",
        "schedule": timedelta(minutes=10),
        "options": {"expires": 200},
    },
}

# ── Gmail Delta Sync ─────────────────────────────────────────────────────────
# Per-connection delta sync via Gmail History API.
# Scheduled via Celery beat for all active gmail connections.
# Default 60s interval for Starter tier.
GMAIL_DELTA_SYNC_SCHEDULE = {
    "sync-gmail-deltas": {
        "task": "apps.sync.tasks.sync_email_delta",
        "schedule": timedelta(seconds=60),
        "options": {"expires": 55},
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

# ── Calendar Sync ─────────────────────────────────────────────────────────────
# Sync Google Calendar events for all connected users.
# 15-minute interval balances freshness with Google API quota.
CALENDAR_SYNC_SCHEDULE = {
    "sync-all-calendars": {
        "task": "apps.sync.tasks_calendar.sync_all_calendars",
        "schedule": timedelta(minutes=15),
        "options": {"expires": 300},  # Drop if previous run still active
    },
}

# ── Calendar Watch Channel Renewal ────────────────────────────────────────────
# Renew Google Calendar watch channels expiring within 24 hours.
# Runs every 6 hours (within the 24-hour grace window).
CALENDAR_WATCH_RENEWAL = {
    "renew-calendar-watch-channels": {
        "task": "apps.sync.tasks_calendar.renew_calendar_watch_channels",
        "schedule": timedelta(hours=6),
        "options": {"expires": 3600},
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
BEAT_SCHEDULE.update(GMAIL_DELTA_SYNC_SCHEDULE)
BEAT_SCHEDULE.update(BACKUP_SCHEDULE)
BEAT_SCHEDULE.update(CLEANUP_SCHEDULE)
BEAT_SCHEDULE.update(CALENDAR_SYNC_SCHEDULE)
BEAT_SCHEDULE.update(CALENDAR_WATCH_RENEWAL)
BEAT_SCHEDULE.update(HEARTBEAT_SCHEDULE)