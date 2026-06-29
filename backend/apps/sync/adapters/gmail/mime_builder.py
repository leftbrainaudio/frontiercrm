"""RFC 2822 MIME composition for sending emails via Gmail."""
from __future__ import annotations

import email.utils
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid

from apps.sync.adapters.base import OutgoingEmail


def build_rfc2822_message(message: OutgoingEmail) -> MIMEMultipart:
    """Build a full RFC 2822 MIME message from an OutgoingEmail.

    Structure:
        multipart/mixed
          ├── multipart/alternative
          │   ├── text/plain (auto-generated from HTML)
          │   └── text/html
          └── attachments (if any)
    """
    msg = MIMEMultipart("mixed")
    msg["To"] = ", ".join(message.to_addresses)
    if message.cc_addresses:
        msg["Cc"] = ", ".join(message.cc_addresses)
    if message.bcc_addresses:
        msg["Bcc"] = ", ".join(message.bcc_addresses)
    msg["Subject"] = message.subject
    msg["Message-ID"] = make_msgid(domain="frontiercrm.com")
    msg["Date"] = email.utils.formatdate(localtime=True)

    # Alternative body (plain text + HTML)
    alt = MIMEMultipart("alternative")

    html_content = message.body_html or ""
    text_content = _strip_html_tags(html_content) or message.body_text or ""

    if text_content:
        alt.attach(MIMEText(text_content, "plain", "utf-8"))
    if html_content:
        alt.attach(MIMEText(html_content, "html", "utf-8"))

    msg.attach(alt)

    # Attachments
    for attachment in message.attachments:
        main_type, sub_type = (
            attachment.mime_type.split("/", 1)
            if "/" in attachment.mime_type
            else ("application", "octet-stream")
        )
        part = MIMEBase(main_type, sub_type)
        part.set_payload(attachment.storage_key or b"")
        from email import encoders

        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{attachment.filename}"')
        msg.attach(part)

    return msg


def _strip_html_tags(html: str) -> str:
    """Strip HTML tags and decode common entities for plain text fallback."""
    import re

    text = re.sub(r"<[^>]*>", "", html)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    return text.strip()