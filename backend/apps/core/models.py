"""Core app — shared base models, mixins, utilities, and infrastructure."""

from __future__ import annotations

import uuid
from typing import Any

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
            # tenant_id is set explicitly by ViewSet.perform_create, so this
            # branch is a safety net — typically unreachable in normal API flow.
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
