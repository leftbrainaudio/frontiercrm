"""Celery tasks for Gmail sync — delta sync, full sync, send email, backfill."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from celery import chain, shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone as tz

from apps.email.models import EmailMessage as CRMEmail
from apps.sync.adapters.base import EmailMessage, OutgoingEmail
from apps.sync.adapters.gmail.adapter import GmailAdapter
from apps.sync.adapters.gmail.client import SyncLock
from apps.sync.adapters.gmail.contact_linker import ContactLinker
from apps.sync.adapters.gmail.thread_matcher import ThreadMatcher
from apps.sync.models import SyncConnection, SyncState

logger = logging.getLogger(__name__)

# ── Helper: resolve adapter from connection ──────────────────────────────────


def _get_adapter(connection: SyncConnection) -> GmailAdapter | None:
    """Create a GmailAdapter from a SyncConnection with decrypted tokens.

    Currently reads raw tokens from connection fields.
    TODO: Integrate TenantEncryptionKey for AES-256-GCM decryption.
    """
    access_token = connection.access_token_encrypted
    refresh_token = connection.refresh_token_encrypted or None

    if not access_token:
        logger.error("Connection %s has no access token", connection.id)
        return None

    return GmailAdapter(access_token=access_token, refresh_token=refresh_token)


def _refresh_tokens_if_needed(connection: SyncConnection, adapter: GmailAdapter) -> bool:
    """Check token expiry and refresh if needed.

    Returns True if tokens are valid (possibly just refreshed), False on failure.
    """
    if connection.token_expires_at and connection.token_expires_at > tz.now():
        return True  # still valid

    result = adapter.refresh_token()
    if result.success:
        connection.access_token_encrypted = result.access_token
        connection.token_expires_at = tz.now() + tz.timedelta(seconds=result.expires_in or 3600)
        connection.save(update_fields=["access_token_encrypted", "token_expires_at"])
        return True

    connection.status = "expired"
    connection.last_error_message = "Token refresh failed"
    connection.save(update_fields=["status", "last_error_message"])
    return False


# ── Delta Sync Task ──────────────────────────────────────────────────────────


@shared_task(bind=True, max_retries=3, default_retry_delay=30, rate_limit="10/m")
def sync_email_delta(
    self,
    connection_id: str,
    trigger: str = "scheduled",
    notification_history_id: int | None = None,
) -> dict[str, Any]:
    """Delta sync for a single Gmail connection.

    Uses History API with Redis lock to prevent concurrent syncs.
    """
    result = {"connection_id": connection_id, "trigger": trigger, "synced": 0, "deleted": 0}

    def _do_sync():
        nonlocal result
        try:
            connection = SyncConnection.objects.get(id=connection_id, provider="gmail")
        except SyncConnection.DoesNotExist:
            return {"error": "Connection not found"}

        if connection.status in ("expired", "disconnected"):
            return {"error": f"Connection status is {connection.status}"}

        adapter = _get_adapter(connection)
        if not adapter:
            return {"error": "Failed to create adapter"}

        if not _refresh_tokens_if_needed(connection, adapter):
            return {"error": "Token refresh failed"}

        # Load cursor from sync_state
        sync_state, _ = SyncState.objects.get_or_create(
            connection=connection,
            sync_type="email",
            defaults={
                "tenant_id": connection.tenant_id,
                "user_id": connection.user_id,
                "provider": "gmail",
                "state": "pending",
                "cursor_data": {},
            },
        )

        # If push notification provides a historyId, use it instead of stored cursor
        cursor = sync_state.cursor_data or {}
        if notification_history_id:
            cursor = {"historyId": notification_history_id}

        # If no cursor at all, treat as full sync
        if not cursor.get("historyId"):
            return _run_full_sync(connection, adapter, sync_state)

        # Delta sync
        sync_state.state = "syncing"
        sync_state.save(update_fields=["state"])

        try:
            delta = adapter.get_email_delta(cursor)

            if delta.full_resync_required:
                sync_state.state = "needs_full_resync"
                sync_state.save(update_fields=["state"])
                # Enqueue full sync
                sync_email_full.delay(connection_id=str(connection.id))
                return {"action": "full_resync_required"}

            # Process changes
            linker = ContactLinker(tenant_id=str(connection.tenant_id), user_id=str(connection.user_id_id))
            threader = ThreadMatcher(tenant_id=str(connection.tenant_id))

            for email in delta.items:
                _process_new_email(connection, email, linker, threader)

            for deleted_id in delta.deleted_ids:
                _process_deleted_email(connection, deleted_id)

            # Update sync state
            sync_state.cursor_data = delta.new_cursor
            sync_state.last_delta_sync_at = tz.now()
            sync_state.total_synced_count = (sync_state.total_synced_count or 0) + len(delta.items)
            sync_state.total_deleted_count = (sync_state.total_deleted_count or 0) + len(delta.deleted_ids)
            sync_state.state = "complete"
            sync_state.save(update_fields=[
                "cursor_data", "last_delta_sync_at",
                "total_synced_count", "total_deleted_count", "state",
            ])

            # Update connection
            connection.last_sync_at = tz.now()
            connection.last_sync_success = True
            connection.error_count = 0
            connection.last_history_id_synced = delta.new_cursor.get("historyId")
            connection.save(update_fields=[
                "last_sync_at", "last_sync_success", "error_count", "last_history_id_synced",
            ])

            result["synced"] = len(delta.items)
            result["deleted"] = len(delta.deleted_ids)

            # If has_more, schedule backfill
            if delta.has_more:
                _schedule_backfill(connection, sync_state)

        except Exception as e:
            sync_state.state = "error"
            sync_state.error_details = str(e)
            sync_state.save(update_fields=["state", "error_details"])
            _handle_sync_error(connection, e)
            raise

    SyncLock.sync_with_lock(connection_id, _do_sync)
    return result


# ── Full Sync Task ───────────────────────────────────────────────────────────


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def sync_email_full(self, connection_id: str) -> dict[str, Any]:
    """Full sync — fetch recent emails (last 30 days) via time-range query."""
    try:
        connection = SyncConnection.objects.get(id=connection_id, provider="gmail")
    except SyncConnection.DoesNotExist:
        return {"error": "Connection not found"}

    adapter = _get_adapter(connection)
    if not adapter:
        return {"error": "Failed to create adapter"}

    if not _refresh_tokens_if_needed(connection, adapter):
        return {"error": "Token refresh failed"}

    sync_state, _ = SyncState.objects.get_or_create(
        connection=connection,
        sync_type="email",
        defaults={
            "tenant_id": connection.tenant_id,
            "user_id": connection.user_id,
            "provider": "gmail",
            "state": "syncing",
        },
    )

    return _run_full_sync(connection, adapter, sync_state)


def _run_full_sync(
    connection: SyncConnection,
    adapter: GmailAdapter,
    sync_state: SyncState,
) -> dict[str, Any]:
    """Execute full sync and save state."""
    linker = ContactLinker(tenant_id=str(connection.tenant_id), user_id=str(connection.user_id_id))
    threader = ThreadMatcher(tenant_id=str(connection.tenant_id))

    sync_state.state = "syncing"
    sync_state.last_full_sync_at = tz.now()
    sync_state.save(update_fields=["state", "last_full_sync_at"])

    try:
        delta = adapter.get_email_delta(None)  # triggers full sync

        for email in delta.items:
            _process_new_email(connection, email, linker, threader)

        sync_state.cursor_data = delta.new_cursor
        sync_state.state = "complete"
        sync_state.total_synced_count = (sync_state.total_synced_count or 0) + len(delta.items)
        sync_state.save(update_fields=[
            "cursor_data", "state", "total_synced_count",
        ])

        connection.last_sync_at = tz.now()
        connection.last_sync_success = True
        connection.error_count = 0
        connection.last_history_id_synced = delta.new_cursor.get("historyId")
        connection.save(update_fields=[
            "last_sync_at", "last_sync_success", "error_count", "last_history_id_synced",
        ])

        # If has_more, schedule backfill
        if delta.has_more:
            _schedule_backfill(connection, sync_state)

        return {"synced": len(delta.items), "full_sync": True}

    except Exception as e:
        sync_state.state = "error"
        sync_state.error_details = str(e)
        sync_state.save(update_fields=["state", "error_details"])
        _handle_sync_error(connection, e)
        raise


# ── Backfill Task ────────────────────────────────────────────────────────────


@shared_task(bind=True, max_retries=2, default_retry_delay=120, queue="low_priority")
def sync_email_backfill(self, connection_id: str, query: str) -> dict[str, Any]:
    """Background backfill of older emails in 6-month time windows."""
    try:
        connection = SyncConnection.objects.get(id=connection_id, provider="gmail")
    except SyncConnection.DoesNotExist:
        return {"error": "Connection not found"}

    adapter = _get_adapter(connection)
    if not adapter:
        return {"error": "Failed to create adapter"}

    linker = ContactLinker(tenant_id=str(connection.tenant_id), user_id=str(connection.user_id_id))
    threader = ThreadMatcher(tenant_id=str(connection.tenant_id))

    try:
        delta = adapter._backfill_time_range(query)
        for email in delta.items:
            _process_new_email(connection, email, linker, threader)
        return {"synced": len(delta.items)}
    except Exception as e:
        logger.error("Backfill failed for %s: %s", connection_id, e)
        raise


# ── Send Email Task ──────────────────────────────────────────────────────────


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_email_task(
    self,
    connection_id: str,
    email_id: str,
) -> dict[str, Any]:
    """Send an email via Gmail, updating CRM record on completion."""
    try:
        connection = SyncConnection.objects.get(id=connection_id, provider="gmail")
        email = CRMEmail.objects.get(id=email_id)
    except (SyncConnection.DoesNotExist, CRMEmail.DoesNotExist) as e:
        return {"error": str(e)}

    adapter = _get_adapter(connection)
    if not adapter:
        return {"error": "Failed to create adapter"}

    try:
        result = adapter.send_email(
            OutgoingEmail(
                to_addresses=email.to_emails or [],
                cc_addresses=email.cc_emails or [],
                bcc_addresses=email.bcc_emails or [],
                subject=email.subject or "",
                body_html=email.body_html or "",
                body_text=email.body_text or "",
            )
        )

        # Update email record
        email.external_id = result.provider_id
        email.thread_id = result.thread_id or ""
        email.direction = CRMEmail.EmailDirection.OUTBOUND
        email.is_read = True
        email.sent_at = tz.now()
        email.save(update_fields=["external_id", "thread_id", "direction", "is_read", "sent_at"])

        # Create CRM thread if needed
        from apps.sync.models import EmailThread

        thread, _ = EmailThread.objects.get_or_create(
            tenant_id=connection.tenant_id,
            emails__external_thread_id=result.thread_id,
            defaults={
                "subject": email.subject or "",
                "participants": email.to_emails or [],
                "last_email_at": tz.now(),
                "email_count": 1,
            },
        )

        # Create activity entry
        from apps.activities.models import Activity

        Activity.objects.create(
            tenant_id=connection.tenant_id,
            user_id=connection.user_id,
            source_type="email",
            action="emailed",
            description=f"Sent email: {(email.subject or '')[:100]}",
            occurred_at=tz.now(),
        )

        return {
            "status": "sent",
            "provider_id": result.provider_id,
            "thread_id": result.thread_id,
        }

    except Exception as e:
        email.status = "failed"
        email.error_message = str(e)
        email.save(update_fields=["status", "error_message"])
        raise


# ── Private Helpers ─────────────────────────────────────────────────────────


def _process_new_email(
    connection: SyncConnection,
    email: EmailMessage,
    linker: ContactLinker,
    threader: ThreadMatcher,
) -> CRMEmail:
    """Upsert an email into the CRM and run linking."""
    crm_email, created = CRMEmail.objects.get_or_create(
        tenant_id=connection.tenant_id,
        message_id=email.provider_id,
        defaults={
            "thread_id": email.thread_id or "",
            "direction": "inbound",
            "from_email": email.from_address,
            "to_emails": email.to_addresses,
            "cc_emails": email.cc_addresses,
            "bcc_emails": email.bcc_addresses,
            "subject": email.subject,
            "body_text": email.body_text or "",
            "body_html": email.body_html or "",
            "snippet": email.snippet or "",
            "sent_at": email.sent_at or tz.now(),
            "received_at": tz.now(),
            "is_read": email.is_read,
            "is_starred": email.is_starred,
            "labels": email.labels,
            "user_id": connection.user_id,
            "gmail_history_id": str(connection.last_history_id_synced or ""),
        },
    )

    if created:
        linker.link(email, crm_email)
        threader.get_or_create_thread(email)

    return crm_email


def _process_deleted_email(connection: SyncConnection, provider_id: str) -> None:
    """Soft-delete an email by provider ID."""
    CRMEmail.objects.filter(
        tenant_id=connection.tenant_id,
        message_id=provider_id,
    ).update(deleted_at=tz.now())


def _schedule_backfill(connection: SyncConnection, sync_state: SyncState) -> None:
    """Schedule background backfill for older emails."""
    # Calculate 6-month windows going backward
    now = datetime.now(timezone.utc)
    recent_cutoff = now - __import__("datetime").timedelta(days=getattr(settings, "GMAIL_FULL_SYNC_RECENT_DAYS", 30))
    window_days = getattr(settings, "GMAIL_FULL_SYNC_BACKFILL_WINDOW", 180)
    max_chunks = getattr(settings, "GMAIL_MAX_BACKFILL_CHUNKS", 4)

    for chunk in range(1, max_chunks + 1):
        window_end = recent_cutoff - __import__("datetime").timedelta(days=window_days * (chunk - 1) + 1)
        window_start = window_end - __import__("datetime").timedelta(days=window_days)
        query = f"after:{window_start.strftime('%Y/%m/%d')} before:{window_end.strftime('%Y/%m/%d')}"

        sync_email_backfill.delay(
            connection_id=str(connection.id),
            query=query,
        )


def _handle_sync_error(connection: SyncConnection, error: Exception) -> None:
    """Update connection state on sync failure with progressive backoff."""
    connection.error_count = (connection.error_count or 0) + 1
    connection.last_error_message = str(error)[:500]
    connection.last_sync_success = False

    if connection.error_count >= 5:
        connection.status = "error"
        connection.last_error_message = "5 consecutive sync failures — connection needs attention"
    elif connection.error_count >= 3:
        # Double the sync interval
        connection.sync_interval_seconds = min(
            connection.sync_interval_seconds * 2, 600
        )

    connection.save(update_fields=[
        "error_count", "last_error_message", "last_sync_success",
        "status", "sync_interval_seconds",
    ])