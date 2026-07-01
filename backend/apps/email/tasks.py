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


from apps.activities.models import Activity


@shared_task(bind=True, max_retries=2)
def send_gmail_message(
    self,
    user_id: str,
    email_id: str,
) -> dict[str, Any]:
    """Send an email via Gmail API (preferred) or SMTP fallback.

    If the user has a Google OAuth access token, sends via Gmail API.
    Otherwise falls back to SMTP (requires SMTP_* settings in .env).
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found"}

    try:
        email_msg = EmailMessage.objects.get(id=email_id, tenant_id=user.tenant_id)
    except EmailMessage.DoesNotExist:
        return {"error": "EmailMessage not found"}

    # Build RFC-2822 message from the stored fields
    msg = email.message.EmailMessage()
    msg.set_content(email_msg.body_text)
    if email_msg.body_html:
        msg.add_alternative(email_msg.body_html, subtype="html")
    msg["To"] = ", ".join(email_msg.to_emails)
    msg["Subject"] = email_msg.subject
    msg["From"] = user.email

    # Route: Gmail API or SMTP fallback
    if user.google_access_token:
        return _send_via_gmail_api(user, email_msg, msg)
    return _send_via_smtp(user, email_msg, msg)


def _send_via_gmail_api(user, email_msg, msg) -> dict[str, Any]:
    """Send via Gmail API using user's OAuth access token."""
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
        return _mark_failed(email_msg, f"Send failed: {resp.text[:2000]}")

    sent_data = resp.json()
    gmail_id = sent_data.get("id", "")
    thread_id = sent_data.get("threadId", "")

    return _mark_sent(email_msg, user, gmail_id, thread_id)


def _send_via_smtp(user, email_msg, msg) -> dict[str, Any]:
    """Send via SMTP using app password from settings."""
    import smtplib
    from django.conf import settings

    smtp_host = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_user = settings.EMAIL_HOST_USER
    smtp_pass = settings.EMAIL_HOST_PASSWORD

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
        return _mark_failed(email_msg, "SMTP not configured — set EMAIL_HOST/USER/PASSWORD in .env")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        email_msg.smtp_id = f"smtp-{email_msg.id}"
        return _mark_sent(email_msg, user, email_msg.smtp_id, "")

    except Exception as exc:
        return _mark_failed(email_msg, f"SMTP send failed: {exc}")


def _mark_failed(email_msg, error_text: str) -> dict[str, Any]:
    """Mark an email as failed and create an activity entry."""
    email_msg.status = EmailMessage.EmailStatus.FAILED
    email_msg.error_message = error_text
    email_msg.save(update_fields=["status", "error_message", "updated_at"])

    Activity.objects.create(
        tenant_id=email_msg.tenant_id,
        activity_type=Activity.ActivityType.EMAIL,
        title=f"Email send failed: {email_msg.subject[:80] or '(no subject)'}",
        description=error_text[:500],
        entity_type="email",
        entity_id=email_msg.id,
        actor_id=None,
        metadata={
            "status": "failed",
            "error": error_text,
            "to": email_msg.to_emails,
            "subject": email_msg.subject,
        },
    )
    return {"status": "failed", "error": error_text}


def _mark_sent(email_msg, user, gmail_id: str, thread_id: str) -> dict[str, Any]:
    """Mark an email as sent and create an activity entry."""
    email_msg.status = EmailMessage.EmailStatus.SENT
    email_msg.message_id = gmail_id
    email_msg.external_id = gmail_id
    email_msg.thread_id = thread_id
    email_msg.is_read = True
    email_msg.sent_at = timezone.now()
    email_msg.save(update_fields=[
        "status", "message_id", "external_id", "thread_id",
        "is_read", "sent_at", "updated_at",
    ])

    Activity.objects.create(
        tenant_id=email_msg.tenant_id,
        activity_type=Activity.ActivityType.EMAIL,
        title=f"Email sent: {email_msg.subject[:100]}" if email_msg.subject else "Email sent",
        description=f"Sent email to {', '.join(email_msg.to_emails)[:200]}",
        entity_type="email",
        entity_id=email_msg.id,
        actor_id=user.id if user else None,
        metadata={
            "status": "sent",
            "subject": email_msg.subject,
            "to": email_msg.to_emails,
            "message_id": gmail_id,
        },
    )
    return {"status": "sent", "message_id": gmail_id}
