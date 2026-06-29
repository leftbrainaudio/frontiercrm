"""Parse Gmail API message format into CRM EmailMessage dataclass."""
from __future__ import annotations

import base64
import email.utils
import re
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any

from apps.sync.adapters.base import AttachmentInfo, EmailMessage


def parse_gmail_message(raw: dict[str, Any]) -> EmailMessage:
    """Convert a Gmail API message response to a normalized EmailMessage.

    Handles both 'full' and 'minimal' format responses.
    Supports multipart/alternative, multipart/mixed, and simple text bodies.
    """
    payload = raw.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

    # Extract identifier fields
    provider_id = raw.get("id", "")
    thread_id = raw.get("threadId")
    message_id = headers.get("message-id", provider_id)
    subject = headers.get("subject", "(no subject)")
    snippet = raw.get("snippet")

    # Parse addresses
    from_address, from_name = _parse_from_header(headers.get("from", ""))
    to_addresses = _parse_address_list(headers.get("to", ""))
    cc_addresses = _parse_address_list(headers.get("cc", ""))
    bcc_addresses = _parse_address_list(headers.get("bcc", ""))

    # Extract body and attachments
    body_text, body_html = _extract_body(payload)
    attachments = _extract_attachments(payload, provider_id)

    # Parse dates
    sent_at = _parse_rfc2822_date(headers.get("date", ""))
    received_at = _parse_internal_date(raw.get("internalDate"))

    # Labels / flags
    label_ids = raw.get("labelIds", [])
    is_read = "UNREAD" not in label_ids
    is_starred = "STARRED" in label_ids

    # Size
    size_estimate = raw.get("sizeEstimate", 0)

    return EmailMessage(
        provider_id=provider_id,
        thread_id=thread_id,
        message_id=message_id,
        subject=subject,
        from_address=from_address,
        from_name=from_name,
        to_addresses=to_addresses,
        cc_addresses=cc_addresses,
        bcc_addresses=bcc_addresses,
        body_text=body_text,
        body_html=body_html,
        snippet=snippet,
        sent_at=sent_at,
        received_at=received_at,
        is_read=is_read,
        is_starred=is_starred,
        labels=label_ids,
        attachments=attachments,
        raw_headers=headers,
        size_estimate=size_estimate,
    )


# ── Body Extraction ─────────────────────────────────────────────────────────


def _extract_body(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Recursively extract plain text and HTML body from a Gmail payload."""
    body_text: str | None = None
    body_html: str | None = None

    def _walk(parts: list[dict[str, Any]]) -> None:
        nonlocal body_text, body_html
        for part in parts:
            mime_type = part.get("mimeType", "")
            part_body = part.get("body", {}) or {}
            data_enc = part_body.get("data", "")

            if data_enc:
                decoded = _decode_base64(data_enc)
                if mime_type == "text/plain":
                    body_text = body_text or decoded
                elif mime_type == "text/html":
                    body_html = body_html or decoded

            # Recurse into nested parts
            if part.get("parts"):
                _walk(part["parts"])

    if payload.get("parts"):
        _walk(payload["parts"])
    elif payload.get("body", {}).get("data"):
        decoded = _decode_base64(payload["body"]["data"])
        mime_type = payload.get("mimeType", "")
        if mime_type == "text/html":
            body_html = decoded
        else:
            body_text = decoded

    return body_text, body_html


def _extract_attachments(payload: dict[str, Any], message_id: str) -> list[AttachmentInfo]:
    """Extract attachment metadata from a Gmail message payload."""
    attachments: list[AttachmentInfo] = []

    def _walk(parts: list[dict[str, Any]]) -> None:
        for part in parts:
            part_body = part.get("body", {}) or {}
            filename = part.get("filename", "")
            if filename and part_body.get("attachmentId"):
                attachments.append(
                    AttachmentInfo(
                        attachment_id=part_body["attachmentId"],
                        filename=filename,
                        mime_type=part.get("mimeType", "application/octet-stream"),
                        size=part_body.get("size", 0),
                    )
                )
            if part.get("parts"):
                _walk(part["parts"])

    if payload.get("parts"):
        _walk(payload["parts"])

    return attachments


# ── Address Parsing ─────────────────────────────────────────────────────────


def _parse_from_header(header: str) -> tuple[str, str | None]:
    """Parse a From header into (address, display_name).

    Handles: 'Alice <alice@acme.com>', '<alice@acme.com>', 'alice@acme.com'
    """
    if not header:
        return "", None

    name, addr = email.utils.parseaddr(header)
    if addr:
        return addr, name or None
    # Fallback: raw extraction
    match = re.search(r"<?([\w.+-]+@[\w.-]+\.\w+)>?", header)
    if match:
        return match.group(1), name or None
    return header.strip(), None


def _parse_address_list(header: str) -> list[str]:
    """Parse a comma-separated address header into a list of email addresses."""
    if not header:
        return []
    addresses: list[str] = []
    for name, addr in email.utils.getaddresses([header]):
        if addr:
            addresses.append(addr)
        elif "@" in name:
            addresses.append(name.strip())
    return addresses


def _parse_name_header(header: str) -> str | None:
    """Extract display name from a header."""
    if not header:
        return None
    name, addr = email.utils.parseaddr(header)
    return name or None


# ── Date Parsing ────────────────────────────────────────────────────────────


def _parse_rfc2822_date(date_str: str) -> datetime | None:
    """Parse an RFC 2822 date string (e.g., 'Mon, 29 Jun 2026 10:30:00 +0000')."""
    if not date_str:
        return None
    with suppress(Exception):
        dt = email.utils.parsedate_to_datetime(date_str)
        if dt and not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    return None


def _parse_internal_date(internal_date_str: str | int | None) -> datetime | None:
    """Parse a Gmail internalDate (milliseconds since epoch)."""
    if not internal_date_str:
        return None
    try:
        ms = int(internal_date_str)
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    except (ValueError, TypeError):
        return None


# ── Encoding Helpers ────────────────────────────────────────────────────────


def _decode_base64(data_enc: str) -> str:
    """Decode a base64url-encoded string to UTF-8 text."""
    try:
        padded = data_enc + "=" * (4 - len(data_enc) % 4) if len(data_enc) % 4 else data_enc
        decoded = base64.urlsafe_b64decode(padded)
        return decoded.decode("utf-8", errors="replace")
    except Exception:
        return ""


def normalize_subject(subject: str) -> str:
    """Strip Re:/Fwd: prefixes and normalize whitespace for thread grouping."""
    if not subject:
        return ""
    s = subject.strip()
    # Remove common prefixes (case-insensitive)
    while True:
        new_s = re.sub(
            r"^(?:Re|Fwd|FWD|FW|Aw|Ant)\s*[:\u2013\u2014\-]+\s*",
            "",
            s,
            count=1,
            flags=re.IGNORECASE,
        )
        if new_s == s:
            break
        s = new_s
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()