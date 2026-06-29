"""Note model — rich-text notes attached to any entity."""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantScopedModel


class Note(TenantScopedModel):
    """Rich-text notes attached to any entity."""

    entity_type = models.CharField(max_length=50, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=500, blank=True, default="")
    content = models.TextField(blank=True, default="")
    content_html = models.TextField(blank=True, default="")
    is_pinned = models.BooleanField(default=False)
    owner_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "notes_note"
        indexes = [
            models.Index(fields=["tenant_id", "entity_type", "entity_id", "-created_at"]),
            models.Index(fields=["tenant_id", "owner_id"]),
            models.Index(fields=["tenant_id", "is_pinned"]),
        ]
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self) -> str:
        return self.title[:50] or f"Note ({self.id})"
