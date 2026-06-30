"""Celery tasks for outbound webhook delivery and maintenance."""

from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.webhooks.models import WebhookDeadEvent, WebhookEvent

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def deliver_webhook(self, event_id: str) -> dict | None:
    """Deliver a single webhook event asynchronously.

    Uses WebhookDeliveryService for the actual HTTP delivery.
    Application-level retry is managed via next_retry_at (not Celery task retries).
    """
    from apps.webhooks.services import WebhookDeliveryService

    try:
        event = WebhookEvent.objects.select_related("endpoint").get(id=event_id)
    except WebhookEvent.DoesNotExist:
        logger.warning("WebhookEvent %s not found for delivery", event_id)
        return None

    service = WebhookDeliveryService()
    result = service.deliver(event)
    logger.info(
        "Webhook delivery %s for event %s: %s",
        result.get("status"),
        event_id,
        result.get("error", ""),
    )
    return result


@shared_task(bind=True)
def retry_stale_webhooks(self) -> dict[str, int]:
    """Find PENDING events past their next_retry_at and re-deliver them.

    This is the safety net — catches events that were missed by the
    original Celery task (e.g. after broker restart, worker outage).
    """
    from apps.webhooks.services import WebhookDeliveryService

    now = timezone.now()
    stale = WebhookEvent.objects.filter(
        status=WebhookEvent.EventStatus.PENDING,
        next_retry_at__lte=now,
        endpoint__is_active=True,
    ).select_related("endpoint")[:500]  # batch limit

    service = WebhookDeliveryService()
    results: dict[str, int] = {
        "retried": 0,
        "delivered": 0,
        "dead_letter": 0,
        "errors": 0,
    }

    for event in stale:
        try:
            result = service.deliver(event)
            status = result.get("status", "unknown")
            results[status] = results.get(status, 0) + 1
        except Exception as exc:
            results["errors"] += 1
            logger.error(
                "Stale webhook retry error for event %s: %s", event.id, exc
            )

    logger.info(
        "Stale webhook sweep: %d retried, %d delivered, %d dead-letter, %d errors",
        results["retried"],
        results["delivered"],
        results["dead_letter"],
        results["errors"],
    )
    return results


@shared_task
def prune_dead_events() -> dict[str, int]:
    """Remove dead events older than the retention period."""
    retention = getattr(settings, "WEBHOOK_DEAD_EVENT_RETENTION_DAYS", 90)
    cutoff = timezone.now() - timedelta(days=retention)
    count, _ = WebhookDeadEvent.objects.filter(failed_at__lt=cutoff).delete()
    logger.info(
        "Pruned %s dead webhook events older than %s days", count, retention
    )
    return {"pruned": count}
