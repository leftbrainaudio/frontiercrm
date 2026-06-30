"""Signal handlers — fire outbound webhooks when entities change."""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.activities.models import Activity
from apps.contacts.models import Contact
from apps.pipelines.models import Deal

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Deal)
def deal_changed_handler(sender, instance, created, **kwargs):
    """Fire webhooks when a Deal is created or updated.

    Triggers:
      - deal.created
      - deal.updated
    """
    if not instance.is_active:
        return  # skip archived/inactive deals

    event_type = "deal.created" if created else "deal.updated"
    _fire_webhooks(instance.tenant_id, event_type, _build_deal_payload(instance))


@receiver(post_save, sender=Contact)
def contact_changed_handler(sender, instance, created, **kwargs):
    """Fire webhooks when a Contact is created or updated."""
    event_type = "contact.created" if created else "contact.updated"
    _fire_webhooks(
        instance.tenant_id, event_type, _build_contact_payload(instance)
    )


@receiver(post_save, sender=Activity)
def activity_created_handler(sender, instance, created, **kwargs):
    """Fire webhooks when an Activity is created (email, note, etc.)."""
    if not created:
        return

    # Map activity type to event type
    activity_to_event = {
        Activity.ActivityType.EMAIL: "email.received",
        Activity.ActivityType.NOTE: "activity.created",
        Activity.ActivityType.TASK: "activity.created",
        Activity.ActivityType.CALL: "activity.created",
        Activity.ActivityType.MEETING: "activity.created",
        Activity.ActivityType.FILE_UPLOAD: "activity.created",
    }
    event_type = activity_to_event.get(instance.activity_type)
    if event_type is None:
        return  # only fire for user-facing activity types

    _fire_webhooks(
        instance.tenant_id, event_type, _build_activity_payload(instance)
    )


# ── Helpers ────────────────────────────────────────────────────────────────────


def _fire_webhooks(tenant_id, event_type, payload):
    """Find matching endpoints and enqueue events.

    Runs synchronously but only does DB writes (no HTTP calls).
    The actual HTTP delivery happens in the Celery task.
    """
    from apps.webhooks.models import WebhookEndpoint
    from apps.webhooks.services import WebhookDeliveryService

    endpoints = WebhookEndpoint.objects.filter(
        tenant_id=tenant_id,
        is_active=True,
    )
    matched = 0
    for endpoint in endpoints:
        if not _matches_event(endpoint, event_type):
            continue
        try:
            event = WebhookDeliveryService.enqueue(endpoint, event_type, payload)
            from apps.webhooks.tasks import deliver_webhook

            deliver_webhook.delay(str(event.id))
            matched += 1
        except Exception as exc:
            logger.error(
                "Failed to enqueue webhook %s for event %s: %s",
                endpoint.id,
                event_type,
                exc,
            )

    if matched:
        logger.debug("Enqueued %d webhook(s) for event %s", matched, event_type)


def _matches_event(endpoint, event_type: str) -> bool:
    """Check if the endpoint subscribes to this event type.

    Empty events list = subscribe to everything.
    Otherwise, check for exact match or wildcard prefix.
    """
    if not endpoint.events:
        return True
    for pattern in endpoint.events:
        if pattern == event_type:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            if event_type.startswith(prefix):
                return True
    return False


def _build_deal_payload(deal) -> dict:
    """Build a standardized Deal payload for webhook delivery."""
    payload = {
        "deal_id": str(deal.id),
        "deal_name": deal.name,
        "value": str(deal.value),
        "currency": deal.currency,
        "status": deal.status,
        "pipeline_id": str(deal.pipeline_id),
        "stage_id": str(deal.stage_id),
        "owner_id": str(deal.owner_id) if deal.owner_id else None,
        "contact_id": str(deal.contact_id) if deal.contact_id else None,
    }
    # Resolve related names (may fail if FK is stale)
    try:
        payload["pipeline_name"] = deal.pipeline.name
        payload["stage_name"] = deal.stage.name
    except Exception:
        payload["pipeline_name"] = ""
        payload["stage_name"] = ""
    return payload


def _build_contact_payload(contact) -> dict:
    """Build a standardized Contact payload for webhook delivery."""
    return {
        "contact_id": str(contact.id),
        "name": f"{contact.first_name} {contact.last_name}",
        "email": contact.email,
        "phone": contact.phone,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "account_id": str(contact.account_id) if contact.account_id else None,
        "owner_id": str(contact.owner_id) if contact.owner_id else None,
    }


def _build_activity_payload(activity) -> dict:
    """Build an Activity payload for webhook delivery."""
    return {
        "activity_id": str(activity.id),
        "activity_type": activity.activity_type,
        "title": activity.title,
        "description": activity.description,
        "entity_type": activity.entity_type,
        "entity_id": str(activity.entity_id) if activity.entity_id else None,
        "actor_id": str(activity.actor_id) if activity.actor_id else None,
        "metadata": activity.metadata,
    }
