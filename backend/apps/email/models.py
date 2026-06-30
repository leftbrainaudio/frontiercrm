"""EmailMessage model — synced from Gmail or sent from FrontierCRM."""
from __future__ import annotations

import re
import uuid
from typing import Any

from django.db import models

from apps.core.models import TenantScopedModel


class EmailTemplate(TenantScopedModel):
    """Reusable email template with variable placeholders."""

    class Category(models.TextChoices):
        GENERAL = "general", "General"
        INTRODUCTION = "introduction", "Introduction"
        FOLLOW_UP = "follow_up", "Follow-up"
        MEETING = "meeting", "Meeting Confirmation"
        PROPOSAL = "proposal", "Proposal"
        THANK_YOU = "thank_you", "Thank You"
        REMINDER = "reminder", "Reminder"
        CUSTOM = "custom", "Custom"

    # Identity
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    # Template content (with {{variable}} placeholders)
    subject_template = models.CharField(max_length=1000)
    body_html = models.TextField(blank=True, default="")
    body_text = models.TextField(
        blank=True, default="",
        help_text="Plain text fallback. Auto-generated from HTML if empty.",
    )

    # Categorization
    category = models.CharField(
        max_length=50, choices=Category.choices,
        default=Category.GENERAL, db_index=True,
    )

    # Scope
    is_shared = models.BooleanField(
        default=True,
        help_text="Shared with entire team vs. personal only",
    )
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="email_templates",
    )

    # Introspection — populated on save by parsing the templates
    variables_used = models.JSONField(
        default=list, blank=True,
        help_text="List of variable names found in subject_template / body_html / body_text",
    )

    class Meta:
        db_table = "email_templates"
        indexes = [
            models.Index(fields=["tenant_id", "category"]),
            models.Index(fields=["tenant_id", "created_by"]),
            models.Index(fields=["tenant_id", "-updated_at"]),
        ]
        ordering = ["-updated_at"]
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        """Auto-populate variables_used by scanning template fields."""
        self.variables_used = self._extract_variables()
        super().save(*args, **kwargs)

    def _extract_variables(self) -> list[str]:
        """Scan template content for {{variable}} patterns."""
        pattern = r"\{\{(\w+)\}\}"
        found: set[str] = set()
        for field in [self.subject_template, self.body_html, self.body_text]:
            found.update(re.findall(pattern, field))
        return sorted(found)


class EmailMessage(TenantScopedModel):
    """Email message synced from Gmail or sent from FrontierCRM."""

    class EmailDirection(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"

    class EmailStatus(models.TextChoices):
        SYNCED = "synced", "Synced"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        DRAFT = "draft", "Draft"

    # Identity
    message_id = models.CharField(max_length=255, db_index=True, help_text="Gmail message ID")
    thread_id = models.CharField(max_length=255, db_index=True)
    external_id = models.CharField(max_length=512, blank=True, default="", help_text="Provider message ID for sent emails")
    external_thread_id = models.CharField(max_length=512, blank=True, default="", help_text="Provider's thread ID")

    # Direction and status
    direction = models.CharField(max_length=10, choices=EmailDirection.choices, db_index=True)
    status = models.CharField(max_length=10, choices=EmailStatus.choices, default=EmailStatus.SYNCED)
    error_message = models.TextField(blank=True, default="")

    # Headers
    from_email = models.EmailField(max_length=255)
    from_name = models.CharField(max_length=256, blank=True, default="")
    to_emails = models.JSONField(default=list)
    cc_emails = models.JSONField(default=list, blank=True)
    bcc_emails = models.JSONField(default=list, blank=True)
    reply_to = models.CharField(max_length=256, blank=True, default="")
    subject = models.CharField(max_length=1000, blank=True, default="")

    # Body
    body_text = models.TextField(blank=True, default="")
    body_html = models.TextField(blank=True, default="")
    snippet = models.CharField(max_length=512, blank=True, default="")

    # Flags
    is_read = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    labels = models.JSONField(default=list, blank=True)
    provider_labels = models.JSONField(default=list, blank=True, help_text="Gmail label IDs")

    # Dates
    sent_at = models.DateTimeField(db_index=True)
    received_at = models.DateTimeField(null=True, blank=True)

    # Size
    size_estimate = models.IntegerField(null=True, blank=True, help_text="Size in bytes")
    smtp_id = models.CharField(max_length=256, blank=True, default="")

    # Linking (CRM context)
    contact = models.ForeignKey(
        "contacts.Contact", on_delete=models.SET_NULL, null=True, blank=True, related_name="emails_set"
    )
    deal = models.ForeignKey(
        "pipelines.Deal", on_delete=models.SET_NULL, null=True, blank=True, related_name="emails_set"
    )
    account = models.ForeignKey(
        "contacts.Account", on_delete=models.SET_NULL, null=True, blank=True, related_name="emails_set"
    )
    connection = models.ForeignKey(
        "sync.SyncConnection", on_delete=models.SET_NULL, null=True, blank=True, related_name="emails"
    )
    crm_thread = models.ForeignKey(
        "sync.EmailThread", on_delete=models.SET_NULL, null=True, blank=True, related_name="emails",
        help_text="FK to CRM email_threads",
    )

    # Legacy fields for backward compat
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
            models.Index(fields=["tenant_id", "direction", "-sent_at"]),
            models.Index(fields=["tenant_id", "external_id"]),
        ]
        ordering = ["-sent_at"]

    def __str__(self) -> str:
        return self.subject[:50] or f"Email {self.message_id}"