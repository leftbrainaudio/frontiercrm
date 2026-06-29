"""ImportJob model — tracks CSV import lifecycle."""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantScopedModel


class ImportJob(TenantScopedModel):
    """Tracks a single CSV import from preview through completion."""

    class EntityType(models.TextChoices):
        CONTACT = "contact", "Contact"
        DEAL = "deal", "Deal"
        ACCOUNT = "account", "Account"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PREVIEWED = "previewed", "Previewed"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class ConflictStrategy(models.TextChoices):
        SKIP = "skip", "Skip existing"
        UPDATE = "update", "Update existing"
        OVERWRITE = "overwrite", "Overwrite existing"

    created_by_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    original_filename = models.CharField(max_length=500)
    file_size = models.IntegerField(default=0)
    detected_columns = models.JSONField(default=list, blank=True)
    column_mapping = models.JSONField(null=True, blank=True)
    dedup_key = models.CharField(max_length=50, null=True, blank=True)
    file_content = models.TextField(blank=True, default="")
    conflict_strategy = models.CharField(
        max_length=20,
        choices=ConflictStrategy.choices,
        default=ConflictStrategy.SKIP,
    )
    preview = models.JSONField(null=True, blank=True)
    summary = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "imports_importjob"
        indexes = [
            models.Index(fields=["tenant_id", "-created_at"]),
            models.Index(fields=["tenant_id", "created_by_id"]),
            models.Index(fields=["tenant_id", "entity_type", "-created_at"]),
            models.Index(fields=["tenant_id", "status"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"ImportJob({self.entity_type}, {self.status})"
