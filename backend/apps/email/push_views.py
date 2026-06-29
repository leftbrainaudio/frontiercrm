"""Celery tasks for Gmail Pub/Sub push notifications."""

from __future__ import annotations

import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.accounts.models import User

from .tasks import sync_gmail_history


@csrf_exempt
@require_POST
def gmail_push_notification(request: HttpRequest) -> JsonResponse:
    """Handle Gmail Pub/Sub push notification."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Verify subscription (base64-encoded)
    message_data = body.get("message", {}).get("data", "")
    if not message_data:
        return JsonResponse({"error": "No data"}, status=400)

    import base64

    try:
        decoded = base64.urlsafe_b64decode(message_data).decode("utf-8")
        payload = json.loads(decoded)
    except Exception:
        return JsonResponse({"error": "Invalid push data"}, status=400)

    email_address = payload.get("emailAddress", "")
    history_id = payload.get("historyId", "")

    if not email_address or not history_id:
        return JsonResponse({"error": "Missing emailAddress or historyId"}, status=400)

    # Find user by email and trigger delta sync
    users = User.objects.filter(email=email_address)
    for user in users:
        sync_gmail_history.delay(str(user.id), history_id)

    return JsonResponse({"status": "queued"})
