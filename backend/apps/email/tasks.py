"""Gmail API sync engine — bidirectional sync with delta tracking.

Uses Gmail API via OAuth2 tokens stored on the User model.
Supports both push (Pub/Sub) and delta sync (historyId) patterns.
"""

from __future__ import annotations

import base64
import email
from typing import Any

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.accounts.models import User
from apps.email.models import EmailMessage


def _refresh_google_token(user: User) -> bool:
    """Refresh a user's Google OAuth access token if needed."""
    if not user.google_refresh_token:
        return False

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": user.google_refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    if resp.status_code != 200:
        return False

    data = resp.json()
    user.google_access_token = data.get("access_token", user.google_access_token)
    user.save(update_fields=["google_access_token"])
    return True


def _gmail_get(user: User, path: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Make an authenticated GET request to the Gmail API."""
    headers = {"Authorization": f"Bearer {user.google_access_token}"}
    resp = requests.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/{path}",
        headers=headers,
        params=params,
        timeout=15,
    )
    if resp.status_code == 401 and _refresh_google_token(user):
        headers["Authorization"] = f"Bearer {user.google_access_token}"
        resp = requests.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/{path}",
            headers=headers,
            params=params,
            timeout=15,
        )
    if resp.status_code != 200:
        return None
    return resp.json()


def _parse_gmail_message(msg_data: dict[str, Any], tenant_id: str) -> dict[str, Any] | None:
    """Convert Gmail API message response to EmailMessage fields."""
    payload = msg_data.get("payload", {})
    headers_map = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

    subject = headers_map.get("subject", "")
    from_email = headers_map.get("from", "")
    to_raw = headers_map.get("to", "")
    cc_raw = headers_map.get("cc", "")
    date_str = headers_map.get("date", "")

    # Parse body from parts
    body_text = ""
    body_html = ""

    def _extract_parts(parts: list[dict[str, Any]]) -> None:
        nonlocal body_text, body_html
        for part in parts:
            mime_type = part.get("mimeType", "")
            data_enc = (part.get("body") or {}).get("data", "")
            if data_enc:
                decoded = base64.urlsafe_b64decode(data_enc.encode("ascii")).decode("utf-8", errors="replace")
                if mime_type == "text/plain":
                    body_text = decoded
                elif mime_type == "text/html":
                    body_html = decoded
            if part.get("parts"):
                _extract_parts(part["parts"])

    if payload.get("parts"):
        _extract_parts(payload["parts"])
    elif payload.get("body", {}).get("data"):
        raw = payload["body"]["data"]
        body_text = base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8", errors="replace")

    # Parse sent_at
    sent_at = timezone.now()
    if date_str:
        from contextlib import suppress
        from email.utils import parsedate_to_datetime

        with suppress(Exception):
            sent_at = parsedate_to_datetime(date_str)

    return {
        "tenant_id": tenant_id,
        "message_id": msg_data["id"],
        "thread_id": msg_data.get("threadId", ""),
        "direction": EmailMessage.EmailDirection.INBOUND,
        "from_email": from_email,
        "to_emails": [t.strip() for t in to_raw.split(",")] if to_raw else [],
        "cc_emails": [t.strip() for t in cc_raw.split(",")] if cc_raw else [],
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "sent_at": sent_at,
        "received_at": timezone.now(),
        "gmail_history_id": msg_data.get("historyId", ""),
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def sync_gmail_messages(self, user_id: str) -> dict[str, Any]:
    """Delta sync for a single user — fetches messages since last historyId."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found"}

    if not user.google_access_token:
        return {"error": "No Gmail access token"}

    params: dict[str, Any] = {"maxResults": 50}
    if user.gmail_history_id:
        params["labelIds"] = ["INBOX", "SENT"]

    # List messages
    result = _gmail_get(user, "messages", params)
    if not result:
        return {"error": "Failed to list messages"}

    messages = result.get("messages", [])
    synced = 0
    for msg_ref in messages:
        msg_id = msg_ref["id"]
        # Skip if already synced
        if EmailMessage.objects.filter(message_id=msg_id, tenant_id=user.tenant_id).exists():
            continue

        msg_data = _gmail_get(user, f"messages/{msg_id}", {"format": "full"})
        if not msg_data:
            continue

        parsed = _parse_gmail_message(msg_data, str(user.tenant_id))
        if parsed:
            EmailMessage.objects.create(**parsed)
            synced += 1

    # Update history ID for next delta sync
    profile = _gmail_get(user, "profile")
    if profile:
        user.gmail_history_id = profile.get("historyId", user.gmail_history_id)
        user.save(update_fields=["gmail_history_id"])

    return {"synced": synced, "total": len(messages)}


@shared_task(bind=True, max_retries=3)
def sync_gmail_history(self, user_id: str, history_id: str) -> dict[str, Any]:
    """Process Gmail Pub/Sub push notification — fetch history since a given historyId."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found"}

    result = _gmail_get(user, "history", {"startHistoryId": history_id, "historyTypes": "messageAdded"})
    if not result:
        return {"error": "Failed to fetch history"}

    histories = result.get("history", [])
    synced = 0
    for history in histories:
        for msg_added in history.get("messagesAdded", []):
            msg_data = msg_added.get("message", {})
            msg_id = msg_data.get("id")
            if not msg_id:
                continue
            if EmailMessage.objects.filter(message_id=msg_id, tenant_id=user.tenant_id).exists():
                continue

            full_msg = _gmail_get(user, f"messages/{msg_id}", {"format": "full"})
            if not full_msg:
                continue
            parsed = _parse_gmail_message(full_msg, str(user.tenant_id))
            if parsed:
                EmailMessage.objects.create(**parsed)
                synced += 1

    return {"synced": synced, "history_entries": len(histories)}


@shared_task(bind=True, max_retries=2)
def send_gmail_message(
    self,
    user_id: str,
    to: list[str],
    subject: str,
    body_text: str,
    body_html: str = "",
) -> dict[str, Any]:
    """Send an email via Gmail API."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found"}

    # Build RFC-2822 message
    msg = email.message.EmailMessage()
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg["From"] = user.email

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

    headers = {"Authorization": f"Bearer {user.google_access_token}", "Content-Type": "application/json"}
    resp = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers=headers,
        json={"raw": raw},
        timeout=15,
    )

    if resp.status_code == 401 and _refresh_google_token(user):
        headers["Authorization"] = f"Bearer {user.google_access_token}"
        resp = requests.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers=headers,
            json={"raw": raw},
            timeout=15,
        )

    if resp.status_code != 200:
        return {"error": f"Send failed: {resp.text}"}

    sent_data = resp.json()
    EmailMessage.objects.create(
        tenant_id=user.tenant_id,
        message_id=sent_data.get("id", ""),
        thread_id=sent_data.get("threadId", ""),
        direction=EmailMessage.EmailDirection.OUTBOUND,
        from_email=user.email,
        to_emails=to,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        sent_at=timezone.now(),
        is_read=True,
    )
    return {"status": "sent", "message_id": sent_data.get("id", "")}
