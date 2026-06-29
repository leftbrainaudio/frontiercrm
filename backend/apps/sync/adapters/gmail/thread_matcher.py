"""Thread grouping logic — Gmail threadId vs subject-based matching."""
from __future__ import annotations

import re
from typing import Any

from apps.sync.adapters.base import EmailMessage
from apps.sync.adapters.gmail.mime_parser import normalize_subject
from apps.sync.models import EmailThread


class ThreadMatcher:
    """Groups emails into CRM threads using Gmail threadId or subject matching.

    Strategy:
    1. Primary: Gmail threadId (external_thread_id) — 1:1 with Gmail threads
    2. Fallback: Normalized subject match for sent/unsent emails
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def get_or_create_thread(self, email: EmailMessage) -> tuple[EmailThread, bool]:
        """Get or create an EmailThread for this email.

        Returns (thread, created_flag).
        """
        # Primary: match by Gmail threadId
        if email.thread_id:
            thread = self._match_by_external_thread(email.thread_id)
            if thread:
                self._update_thread(thread, email)
                return thread, False

        # Fallback: match by normalized subject
        subject = normalize_subject(email.subject)
        if subject:
            thread = self._match_by_subject(subject, email)
            if thread:
                self._update_thread(thread, email)
                return thread, False

        # Create new thread
        thread = EmailThread.objects.create(
            tenant_id=self.tenant_id,
            subject=email.subject[:512] if email.subject else "",
            normalized_subject=subject[:512] if subject else "",
            participants=self._collect_participants(email),
            last_email_at=email.sent_at,
            email_count=1,
        )
        return thread, True

    def _match_by_external_thread(self, external_thread_id: str) -> EmailThread | None:
        """Find a CRM thread by Gmail threadId."""
        # Threads are found via the emails table linking to EmailThread
        return (
            EmailThread.objects.filter(
                tenant_id=self.tenant_id,
                emails__external_thread_id=external_thread_id,
            )
            .order_by("-last_email_at")
            .first()
        )

    def _match_by_subject(self, normalized_subject: str, email: EmailMessage) -> EmailThread | None:
        """Find a thread by normalized subject, preferring participant overlap."""
        threads = EmailThread.objects.filter(
            tenant_id=self.tenant_id,
            normalized_subject=normalized_subject,
        ).order_by("-last_email_at")

        for thread in threads:
            participants = thread.participants or []
            # Check if any participant overlaps with this email's addresses
            email_addresses = self._collect_participants(email)
            if any(p in email_addresses for p in participants):
                return thread

        return threads.first() if threads.exists() else None

    def _update_thread(self, thread: EmailThread, email: EmailMessage) -> None:
        """Update thread metadata after adding a new email."""
        participants = set(thread.participants or [])
        participants.update(self._collect_participants(email))
        thread.participants = list(participants)
        thread.email_count = (thread.email_count or 0) + 1
        if email.sent_at and (not thread.last_email_at or email.sent_at > thread.last_email_at):
            thread.last_email_at = email.sent_at
        thread.save(update_fields=["participants", "email_count", "last_email_at"])

    @staticmethod
    def _collect_participants(email: EmailMessage) -> list[str]:
        """Collect all unique email addresses from an email."""
        participants: set[str] = {email.from_address.lower().strip()}
        for addr_list in [email.to_addresses, email.cc_addresses, email.bcc_addresses]:
            for addr in addr_list:
                participants.add(addr.lower().strip())
        return list(participants)