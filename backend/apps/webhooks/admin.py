"""Django admin registration for webhook models — endpoint, event, dead-letter."""

from __future__ import annotations

import logging

from django.contrib import admin, messages
from django.http import HttpRequest
from django.utils import timezone

from apps.webhooks.models import WebhookDeadEvent, WebhookEndpoint, WebhookEvent

logger = logging.getLogger(__name__)


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = [
        "url",
        "tenant_id",
        "is_active",
        "last_triggered_at",
        "failure_count",
        "max_retries",
    ]
    list_filter = ["is_active", "tenant_id"]
    search_fields = ["url", "description"]
    readonly_fields = ["tenant_id", "created_at", "updated_at", "last_triggered_at", "failure_count"]


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = [
        "event_type",
        "endpoint",
        "status",
        "attempt_count",
        "last_attempt_at",
        "next_retry_at",
    ]
    list_filter = ["status", "event_type", "tenant_id"]
    search_fields = ["event_type", "error_message"]
    readonly_fields = [
        "tenant_id",
        "created_at",
        "updated_at",
        "event_type",
        "payload",
        "attempt_count",
        "last_attempt_at",
        "next_retry_at",
        "response_status",
        "response_body",
        "error_message",
    ]


@admin.register(WebhookDeadEvent)
class WebhookDeadEventAdmin(admin.ModelAdmin):
    list_display = [
        "event_type",
        "endpoint_link",
        "final_attempt_count",
        "last_error_short",
        "failed_at",
        "resolved_at",
    ]
    list_filter = ["event_type", "tenant_id", "resolved_at"]
    search_fields = ["event_type", "last_error"]
    readonly_fields = [
        "tenant_id",
        "created_at",
        "updated_at",
        "original_event",
        "endpoint",
        "event_type",
        "payload",
        "final_attempt_count",
        "last_error",
        "last_response_status",
        "last_response_body",
        "failed_at",
    ]
    actions = ["replay_dead_events", "resolve_dead_events"]

    def endpoint_link(self, obj: WebhookDeadEvent) -> str:
        return str(obj.endpoint_id)

    endpoint_link.short_description = "Endpoint"

    def last_error_short(self, obj: WebhookDeadEvent) -> str:
        return obj.last_error[:80] if obj.last_error else ""

    last_error_short.short_description = "Last Error"

    @admin.action(description="Replay selected dead events")
    def replay_dead_events(
        self, request: HttpRequest, queryset
    ) -> None:
        """Replay selected dead-letter events as fresh webhook deliveries."""
        from apps.webhooks.services import WebhookDeliveryService
        from apps.webhooks.tasks import deliver_webhook

        replayed = 0
        errors = 0
        for dead_event in queryset.filter(resolved_at__isnull=True):
            try:
                endpoint = dead_event.endpoint
                event = WebhookDeliveryService.enqueue(
                    endpoint, dead_event.event_type, dead_event.payload
                )
                deliver_webhook.delay(str(event.id))
                dead_event.resolved_at = timezone.now()
                dead_event.resolution_notes = "Replayed via admin action"
                dead_event.save(update_fields=["resolved_at", "resolution_notes"])
                replayed += 1
            except Exception as exc:
                errors += 1
                logger.error(
                    "Failed to replay dead event %s: %s", dead_event.id, exc
                )

        if replayed:
            self.message_user(
                request,
                f"Replayed {replayed} dead event(s). Errors: {errors}",
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request, "No events were replayed.", messages.WARNING
            )

    @admin.action(description="Resolve selected dead events")
    def resolve_dead_events(
        self, request: HttpRequest, queryset
    ) -> None:
        """Mark selected dead events as resolved."""
        now = timezone.now()
        updated = queryset.filter(resolved_at__isnull=True).update(
            resolved_at=now,
            resolution_notes="Resolved via admin bulk action",
        )
        self.message_user(
            request,
            f"Resolved {updated} dead event(s).",
            messages.SUCCESS,
        )
