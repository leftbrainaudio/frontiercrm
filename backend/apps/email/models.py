"""EmailMessage model — synced from Gmail or sent from FrontierCRM."""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantScopedModel


class EmailMessage(TenantScopedModel):
    """Email message synced from Gmail or sent from FrontierCRM."""

    class EmailDirection(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"

    message_id = models.CharField(max_length=255, db_index=True, help_text="Gmail message ID")
    thread_id = models.CharField(max_length=255, db_index=True)
    direction = models.CharField(max_length=10, choices=EmailDirection.choices)
    from_email = models.EmailField(max_length=255)
    to_emails = models.JSONField(default=list)
    cc_emails = models.JSONField(default=list, blank=True)
    bcc_emails = models.JSONField(default=list, blank=True)
    subject = models.CharField(max_length=1000, blank=True, default="")
    body_text = models.TextField(blank=True, default="")
    body_html = models.TextField(blank=True, default="")
    sent_at = models.DateTimeField()
    received_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    labels = models.JSONField(default=list, blank=True)
    entity_type = models.CharField(max_length=50, blank=True, default="", db_index=True)
    entity_id = models.UUIDField(null=True, blank=True, db_index=True)
    gmail_history_id = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        db_table = "email_messages"
        indexes = [
            models.Index(fields=["tenant_id", "thread_id", "-sent_at"]),
            models.Index(fields=["tenant_id", "from_email"]),
            models.Index(fields=["tenant_id", "-sent_at"]),
            models.Index(fields=["tenant_id", "message_id"]),
        ]
        ordering = ["-sent_at"]

    def __str__(self) -> str:
        return self.subject[:50] or f"Email {self.message_id}"
