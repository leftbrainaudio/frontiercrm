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
