"""File upload and attachment model."""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantScopedModel


class FileUpload(TenantScopedModel):
    """Uploaded file with S3/R2 signed URL support."""

    original_filename = models.CharField(max_length=500)
    file_key = models.CharField(max_length=1000, help_text="S3 object key or storage path")
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True, default="")
    bucket = models.CharField(max_length=255, blank=True, default="")
    entity_type = models.CharField(max_length=50, blank=True, default="", db_index=True)
    entity_id = models.UUIDField(null=True, blank=True, db_index=True)
    uploaded_by_id = models.UUIDField(null=True, blank=True, db_index=True)
    is_temporary = models.BooleanField(default=False, help_text="Auto-cleanup after expiry")

    class Meta:
        db_table = "files_upload"
        indexes = [
            models.Index(fields=["tenant_id", "entity_type", "entity_id"]),
            models.Index(fields=["tenant_id", "uploaded_by_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.original_filename
