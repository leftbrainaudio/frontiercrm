"""Task model — trackable to-do items."""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantScopedModel


class TaskItem(TenantScopedModel):
    """Trackable task / to-do item."""

    class TaskPriority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class TaskStatus(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    priority = models.CharField(max_length=10, choices=TaskPriority.choices, default=TaskPriority.MEDIUM)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.TODO)
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    owner_id = models.UUIDField(null=True, blank=True, db_index=True)
    assignee_id = models.UUIDField(null=True, blank=True, db_index=True)
    entity_type = models.CharField(max_length=50, blank=True, default="", db_index=True)
    entity_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "tasks_task"
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["tenant_id", "assignee_id"]),
            models.Index(fields=["tenant_id", "due_at"]),
            models.Index(fields=["tenant_id", "priority", "due_at"]),
        ]
        ordering = ["-priority", "due_at", "-created_at"]

    def __str__(self) -> str:
        return self.title[:50]
