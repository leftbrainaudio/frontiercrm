"""Webhook-related models with retry and dead-letter tracking."""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantScopedModel


class WebhookEndpoint(TenantScopedModel):
    """Registered webhook endpoint for a tenant."""

    url = models.URLField(max_length=2000)
    secret = models.CharField(max_length=255, help_text="HMAC secret for signature verification")
    events = models.JSONField(default=list, help_text="List of event types to subscribe to")
    description = models.CharField(max_length=500, blank=True, default="")
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    class Meta:
        db_table = "webhooks_endpoint"
        indexes = [
            models.Index(fields=["tenant_id", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.url[:50]}..."


class WebhookEvent(TenantScopedModel):
    """Record of a webhook delivery attempt."""

    class EventStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.PENDING)
    attempt_count = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")

    class Meta:
        db_table = "webhooks_event"
        indexes = [
            models.Index(fields=["status", "next_retry_at"]),
            models.Index(fields=["endpoint", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.event_type} / {self.status}"


class WebhookDeadEvent(TenantScopedModel):
    """Dead-letter record for a permanently failed webhook delivery.

    Created when a WebhookEvent exhausts its retries and is marked FAILED.
    Preserves the original event data for inspection and replay.
    """

    original_event = models.OneToOneField(
        WebhookEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dead_letter",
    )
    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name="dead_events",
    )
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    final_attempt_count = models.IntegerField()
    last_error = models.TextField(blank=True, default="")
    last_response_status = models.IntegerField(null=True, blank=True)
    last_response_body = models.TextField(blank=True, default="")
    failed_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "webhooks_dead_event"
        indexes = [
            models.Index(fields=["endpoint", "-failed_at"]),
            models.Index(fields=["resolved_at"]),  # sweep un-resolved
        ]
        ordering = ["-failed_at"]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.endpoint_id} - failed {self.failed_at}"
