"""Models for the sync engine — connections, state, encryption keys."""
from __future__ import annotations

import uuid
from typing import Any

from django.db import models

from apps.core.models import TenantScopedModel, TimeStampedModel


class SyncConnection(TenantScopedModel):
    """OAuth connection to an external sync provider (Gmail, Outlook, etc.)."""

    PROVIDER_CHOICES = [
        ("gmail", "Gmail"),
        ("outlook", "Outlook"),
        ("google_calendar", "Google Calendar"),
        ("outlook_calendar", "Outlook Calendar"),
        ("imap", "IMAP"),
        ("caldav", "CalDAV"),
    ]
    ACCOUNT_TYPE_CHOICES = [
        ("personal", "Personal"),
        ("shared", "Shared"),
        ("resource", "Resource"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("error", "Error"),
        ("expired", "Expired"),
        ("disconnected", "Disconnected"),
        ("pending", "Pending"),
    ]

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="sync_connections"
    )

    # Provider info
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES)
    provider_account = models.CharField(max_length=256, help_text="Email address or account identifier")
    account_type = models.CharField(max_length=16, choices=ACCOUNT_TYPE_CHOICES, default="personal")

    # OAuth tokens (encrypted at rest)
    access_token_encrypted = models.TextField(blank=True, default="")
    refresh_token_encrypted = models.TextField(blank=True, default="")
    token_expires_at = models.DateTimeField(null=True, blank=True)
    scopes = models.JSONField(default=list, blank=True)

    # Connection state
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_success = models.BooleanField(null=True)
    last_error_message = models.TextField(blank=True, default="")
    error_count = models.IntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active")

    # Tier config
    sync_interval_seconds = models.IntegerField(default=60)

    # Gmail-specific (added per design spec §12)
    watch_expires_at = models.DateTimeField(null=True, blank=True)
    watch_history_id = models.BigIntegerField(null=True, blank=True)
    gcp_project_id = models.CharField(max_length=256, blank=True, default="")
    encryption_key_id = models.UUIDField(null=True, blank=True)
    last_history_id_synced = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = "sync_connections"
        indexes = [
            models.Index(fields=["tenant_id", "user"]),
            models.Index(fields=["tenant_id", "provider"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "user", "provider", "provider_account"],
                name="uq_sync_connection",
            )
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.provider_account} ({self.status})"


class SyncState(TenantScopedModel):
    """Per-provider sync cursor/watermark for delta sync."""

    SYNC_TYPE_CHOICES = [
        ("email", "Email"),
        ("calendar_event", "Calendar Event"),
        ("contacts", "Contacts"),
    ]
    STATE_CHOICES = [
        ("pending", "Pending"),
        ("syncing", "Syncing"),
        ("complete", "Complete"),
        ("error", "Error"),
        ("needs_full_resync", "Needs Full Resync"),
    ]

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="sync_states"
    )
    connection = models.ForeignKey(
        SyncConnection, on_delete=models.CASCADE, related_name="sync_states"
    )

    sync_type = models.CharField(max_length=32, choices=SYNC_TYPE_CHOICES)
    provider = models.CharField(max_length=32)

    # Delta sync cursors (JSONB in Postgres, JSONField in Django)
    cursor_data = models.JSONField(default=dict, blank=True)

    last_full_sync_at = models.DateTimeField(null=True, blank=True)
    last_delta_sync_at = models.DateTimeField(null=True, blank=True)
    next_sync_at = models.DateTimeField(null=True, blank=True)
    sync_batch_size = models.IntegerField(default=100)

    state = models.CharField(max_length=24, choices=STATE_CHOICES, default="pending")
    error_details = models.TextField(blank=True, default="")

    total_synced_count = models.IntegerField(default=0)
    total_deleted_count = models.IntegerField(default=0)
    sync_duration_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "sync_states"
        indexes = [
            models.Index(fields=["next_sync_at"]),
            models.Index(fields=["tenant_id", "user"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["connection", "sync_type"], name="uq_sync_state"
            )
        ]

    def __str__(self) -> str:
        return f"{self.connection.provider}/{self.sync_type} [{self.state}]"


class SyncConflict(TenantScopedModel):
    """Log of sync conflicts and their resolution."""

    CONFLICT_TYPE_CHOICES = [
        ("concurrent_edit", "Concurrent Edit"),
        ("deleted_elsewhere", "Deleted Elsewhere"),
        ("version_mismatch", "Version Mismatch"),
    ]
    RESOLUTION_CHOICES = [
        ("last_write_wins", "Last Write Wins"),
        ("provider_wins", "Provider Wins"),
        ("crm_wins", "CRM Wins"),
        ("manual", "Manual"),
    ]
    RESOLVED_BY_CHOICES = [
        ("system", "System"),
        ("user", "User"),
    ]

    connection = models.ForeignKey(
        SyncConnection, on_delete=models.CASCADE, related_name="conflicts"
    )

    entity_type = models.CharField(max_length=32)
    entity_id = models.UUIDField(null=True, blank=True)
    external_id = models.CharField(max_length=512, blank=True, default="")

    conflict_type = models.CharField(max_length=32, choices=CONFLICT_TYPE_CHOICES)
    resolution_strategy = models.CharField(max_length=32, choices=RESOLUTION_CHOICES)

    crm_version = models.JSONField(default=dict, blank=True)
    provider_version = models.JSONField(default=dict, blank=True)
    resolved_data = models.JSONField(default=dict, blank=True)

    resolved_by = models.CharField(max_length=32, choices=RESOLVED_BY_CHOICES, default="system")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "sync_conflicts"
        indexes = [
            models.Index(fields=["tenant_id", "entity_type", "entity_id"]),
            models.Index(fields=["connection"]),
            models.Index(fields=["resolved_at"]),
        ]


class EmailThread(TenantScopedModel):
    """CRM grouping of emails into threads/subjects."""

    subject = models.CharField(max_length=512, blank=True, default="")
    normalized_subject = models.CharField(max_length=512, blank=True, default="")
    participants = models.JSONField(default=list, blank=True)

    contact = models.ForeignKey(
        "contacts.Contact", on_delete=models.SET_NULL, null=True, blank=True, related_name="email_threads"
    )
    deal = models.ForeignKey(
        "pipelines.Deal", on_delete=models.SET_NULL, null=True, blank=True, related_name="email_threads"
    )
    account = models.ForeignKey(
        "contacts.Account", on_delete=models.SET_NULL, null=True, blank=True, related_name="email_threads"
    )

    last_email_at = models.DateTimeField(null=True, blank=True)
    email_count = models.IntegerField(default=0)
    is_archived = models.BooleanField(default=False)

    class Meta:
        db_table = "email_threads"
        indexes = [
            models.Index(fields=["tenant_id"]),
            models.Index(fields=["contact"]),
            models.Index(fields=["deal"]),
            models.Index(fields=["tenant_id", "normalized_subject"]),
            models.Index(fields=["tenant_id", "last_email_at"]),
        ]

    def __str__(self) -> str:
        return self.normalized_subject or self.subject or "(no subject)"


class TenantEncryptionKey(TimeStampedModel):
    """Tenant-scoped AES-256-GCM encryption keys for OAuth token storage."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, unique=True)
    key_data = models.BinaryField()
    key_version = models.IntegerField(default=1)
    rotated_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tenant_encryption_keys"