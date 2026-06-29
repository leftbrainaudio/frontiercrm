"""Auto-link synced emails to CRM contacts, accounts, and deals.

4-pass matching strategy:
    Pass 1 — Direct email match
    Pass 2 — Domain match (if no direct match)
    Pass 3 — Thread-based deal linking
    Pass 4 — Lead creation (unknown external senders)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from apps.sync.adapters.base import EmailMessage

logger = logging.getLogger(__name__)


@dataclass
class LinkingResult:
    """Result of the contact linking process."""

    contact_matched: Any | None = None  # Contact or Lead
    account_matched: Any | None = None
    deal_matched: Any | None = None
    match_method: str = ""  # 'email', 'domain', 'thread', 'new_lead', 'none'


class ContactLinker:
    """Auto-links synced emails to CRM contacts, accounts, and deals.

    Operates on EmailMessage dataclass + CRM model fields.
    All DB lookups are tenant-scoped.
    """

    def __init__(self, tenant_id: str, user_id: str | None = None):
        self.tenant_id = tenant_id
        self.user_id = user_id

    def link(self, email: EmailMessage, crm_email: Any) -> LinkingResult:
        """Run all 4 matching passes, update crm_email in place.

        Args:
            email: The normalized EmailMessage from the adapter.
            crm_email: A Django EmailMessage instance (or compatible dict).

        Returns:
            LinkingResult with match details.
        """
        result = LinkingResult()

        # Pass 1: Direct email match
        from_contact = self._match_by_email(email.from_address)
        if from_contact:
            crm_email.contact_id = from_contact.id
            result.contact_matched = from_contact
            result.match_method = "email"

        # Pass 2: Domain match (inbound from unknown sender)
        if not result.contact_matched:
            account = self._match_by_domain(email.from_address)
            if account:
                crm_email.account_id = account.id
                result.account_matched = account
                result.match_method = "domain"

        # Pass 3: Thread-based deal linking
        if email.thread_id:
            deal_id = self._match_deal_by_thread(email.thread_id)
            if deal_id:
                crm_email.deal_id = deal_id
                result.deal_matched = deal_id
                result.match_method = result.match_method or "thread"

        # Pass 4: Lead creation for unknown external senders
        if not result.contact_matched:
            new_contact = self._create_lead_from_email(email)
            if new_contact:
                crm_email.contact_id = new_contact.id
                result.contact_matched = new_contact
                result.match_method = "new_lead"

        return result

    def _match_by_email(self, email_address: str) -> Any | None:
        """Pass 1: Direct email match against CRM contacts."""
        from apps.contacts.models import Contact

        normalized = email_address.lower().strip()
        try:
            return Contact.objects.filter(
                tenant_id=self.tenant_id,
                email__iexact=normalized,
                deleted_at__isnull=True,
            ).first()
        except Exception:
            return None

    def _match_by_domain(self, email_address: str) -> Any | None:
        """Pass 2: Match by email domain against accounts."""
        from apps.contacts.models import Account

        domain = email_address.split("@")[-1] if "@" in email_address else None
        if not domain:
            return None
        try:
            return Account.objects.filter(
                tenant_id=self.tenant_id,
                domain__iexact=domain,
                deleted_at__isnull=True,
            ).first()
        except Exception:
            return None

    def _match_deal_by_thread(self, external_thread_id: str) -> Any | None:
        """Pass 3: Find a deal linked to this email thread."""
        from apps.email.models import EmailMessage as CRMMessage

        last_email = (
            CRMMessage.objects.filter(
                tenant_id=self.tenant_id,
                thread_id=external_thread_id,
                deal_id__isnull=False,
            )
            .order_by("-sent_at")
            .first()
        )
        return last_email.deal_id if last_email else None

    def _create_lead_from_email(self, email: EmailMessage) -> Any | None:
        """Pass 4: Create a lead contact for unknown external senders."""
        from apps.contacts.models import Contact

        # Don't create leads for outbound emails (we sent them, we know the recipient)
        # Or for emails from the current user
        if self._is_outbound_from_user(email):
            return None

        first_name = self._extract_first_name(email.from_name)
        last_name = self._extract_last_name(email.from_name) or email.from_address.split("@")[0]

        try:
            contact = Contact.objects.create(
                tenant_id=self.tenant_id,
                first_name=first_name or "Unknown",
                last_name=last_name,
                email=email.from_address,
                source="email_inbound",
                owner_id=self.user_id,
            )
            logger.info(
                "Created lead contact %s %s from email %s",
                contact.first_name,
                contact.last_name,
                email.from_address,
            )
            return contact
        except Exception as e:
            logger.error("Failed to create lead from email %s: %s", email.from_address, e)
            return None

    def _is_outbound_from_user(self, email: EmailMessage) -> bool:
        """Check if this is a sent email from the current user (no lead needed)."""
        from apps.accounts.models import User

        if self.user_id:
            try:
                user = User.objects.get(id=self.user_id)
                if user.email and user.email.lower().strip() == email.from_address.lower().strip():
                    return True
            except User.DoesNotExist:
                pass
        return False

    @staticmethod
    def _extract_first_name(full_name: str | None) -> str | None:
        """Extract first name from a display name."""
        if not full_name:
            return None
        parts = full_name.strip().split(None, 1)
        return parts[0] if parts else None

    @staticmethod
    def _extract_last_name(full_name: str | None) -> str | None:
        """Extract last name from a display name."""
        if not full_name:
            return None
        parts = full_name.strip().split(None, 1)
        return parts[-1] if len(parts) > 1 else None