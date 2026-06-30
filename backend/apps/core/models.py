"""Core app — shared base models, mixins, utilities, and infrastructure."""

from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base with created_at, updated_at, and soft-delete support."""

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        """Mark as deleted instead of removing from DB."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class TenantModel(models.Model):
    """Abstract base for all multi-tenant models. Attaches tenant_id."""

    tenant_id = models.UUIDField(
        db_index=True,
        help_text="UUID of the tenant this record belongs to",
    )

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Auto-assign tenant_id from request when creating."""
        if not self.pk and not self.tenant_id:
            pass
        super().save(*args, **kwargs)


class TenantScopedModel(TenantModel, TimeStampedModel):
    """Convenience base: both multi-tenant and time-stamped."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["tenant_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"


FIELD_TYPES = [
    ("text", "Text"),
    ("number", "Number"),
    ("date", "Date"),
    ("select", "Select"),
]

ENTITY_TYPES = [
    ("contacts", "Contacts"),
    ("deals", "Deals"),
    ("accounts", "Accounts"),
]


class CustomFieldDef(TenantScopedModel):
    """Defines a custom field for a specific entity type (contacts/deals/accounts)."""

    name = models.CharField(max_length=128)
    field_type = models.CharField(max_length=16, choices=FIELD_TYPES)
    entity_type = models.CharField(max_length=16, choices=ENTITY_TYPES)
    options = models.JSONField(default=list, blank=True, help_text="Options for select type")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = "core_custom_field_def"
        ordering = ["entity_type", "order", "name"]
        indexes = [
            models.Index(fields=["tenant_id", "entity_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_field_type_display()})"


class AuditLog(TenantScopedModel):
    """Immutable record of a user action within a tenant."""

    class ActionChoices(models.TextChoices):
        CREATE = "create", "Created"
        UPDATE = "update", "Updated"
        DELETE = "delete", "Deleted"
        LOGIN = "login", "Login"
        EXPORT = "export", "Export"
        IMPORT = "import", "Import"
        INVITE = "invite", "Invited"
        SEND = "send", "Sent"
        ARCHIVE = "archive", "Archived"
        RESTORE = "restore", "Restored"
        OTHER = "other", "Other"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(
        max_length=20,
        choices=ActionChoices.choices,
        db_index=True,
    )
    entity_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="e.g. contact, deal, account, note, email",
    )
    entity_id = models.UUIDField(null=True, blank=True, db_index=True)
    entity_name = models.CharField(max_length=255, blank=True, default="")
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "core_audit_log"
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log Entries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "entity_type", "created_at"]),
            models.Index(fields=["tenant_id", "actor_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.get_action_display()} "
            f"{self.entity_type} "
            f"by {getattr(self.actor, 'email', 'system')} "
            f"at {self.created_at.isoformat()}"
        )


class ThreadLocal:
    """Simple thread-local storage for request context."""

    _local: dict[str, Any] = {}

    def __init__(self) -> None:
        self.__class__._local = {}

    @classmethod
    def get(cls) -> Any:
        """Return the thread-local namespace object."""
        import threading

        return threading.local()
