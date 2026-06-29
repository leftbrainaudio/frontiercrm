"""Activity model — unified activity feed entry."""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantScopedModel


class Activity(TenantScopedModel):
    """Unified activity feed entry — captures any action on any entity."""

    class ActivityType(models.TextChoices):
        NOTE = "note", "Note"
        CALL = "call", "Call"
        EMAIL = "email", "Email"
        MEETING = "meeting", "Meeting"
        TASK = "task", "Task"
        DEAL_STAGE_CHANGE = "deal_stage_change", "Deal Stage Change"
        DEAL_STATUS_CHANGE = "deal_status_change", "Deal Status Change"
        FILE_UPLOAD = "file_upload", "File Upload"
        SYSTEM = "system", "System"

    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    title = models.CharField(max_length=500, blank=True, default="")
    description = models.TextField(blank=True, default="")
    entity_type = models.CharField(max_length=50, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    actor_id = models.UUIDField(null=True, blank=True, db_index=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    call_outcome = models.CharField(max_length=100, blank=True, default="")
    call_recording_url = models.URLField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "activities_activity"
        indexes = [
            models.Index(fields=["tenant_id", "entity_type", "entity_id", "-created_at"]),
            models.Index(fields=["tenant_id", "activity_type"]),
            models.Index(fields=["tenant_id", "actor_id"]),
            models.Index(fields=["tenant_id", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.activity_type}] {self.title[:50]}"
