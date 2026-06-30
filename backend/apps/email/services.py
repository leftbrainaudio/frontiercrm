"""Variable resolution service for email templates."""
from __future__ import annotations

import re
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Any

from django.utils import timezone

from apps.contacts.models import Account, Contact
from apps.pipelines.models import Deal
from apps.accounts.models import User

VARIABLE_PATTERN = re.compile(r"\{\{(\w+)\}\}")


class VariableResolver:
    """Resolves {{variable}} placeholders from CRM context.

    Resolution priority (high to low):
      1. Explicit context dict (request body)
      2. Entity-derived (linked contact/deal/account)
      3. Sender-derived (requesting user)
      4. Tenant-derived (tenant settings)
      5. Date-derived (dynamic date variables)
      6. Unresolved → left as-is
    """

    def __init__(self, user: User, tenant: Any) -> None:
        self.user = user
        self.tenant = tenant
        self._contact: Contact | None = None
        self._deal: Deal | None = None
        self._account: Account | None = None
        self._explicit_context: dict[str, str] = {}

    def set_explicit_context(self, context: dict[str, str]) -> None:
        """Set explicit variable overrides (highest priority)."""
        self._explicit_context = context or {}

    def set_contact(self, contact_id: str | None) -> None:
        """Load contact by id (tenant-scoped)."""
        if contact_id:
            self._contact = Contact.objects.filter(
                id=contact_id, tenant_id=self.user.tenant_id
            ).select_related("account").first()

    def set_deal(self, deal_id: str | None) -> None:
        """Load deal by id (tenant-scoped)."""
        if deal_id:
            self._deal = Deal.objects.filter(
                id=deal_id, tenant_id=self.user.tenant_id
            ).select_related("stage__pipeline", "contact", "account").first()

    def set_account(self, account_id: str | None) -> None:
        """Load account by id (tenant-scoped)."""
        if account_id:
            self._account = Account.objects.filter(
                id=account_id, tenant_id=self.user.tenant_id
            ).first()

    def resolve(self, text: str) -> tuple[str, list[str]]:
        """Replace all {{vars}} with resolved values.

        Returns (rendered_text, unresolved_variables).
        """
        unresolved: list[str] = []

        def _replace(match: re.Match) -> str:
            varname = match.group(1)
            value = self._get_value(varname)
            if value is None:
                unresolved.append(varname)
                return match.group(0)  # leave as-is
            return value

        rendered = VARIABLE_PATTERN.sub(_replace, text)
        return rendered, sorted(set(unresolved))

    def _get_value(self, name: str) -> str | None:
        """Resolve a single variable name following priority order."""
        # 1. Explicit context
        if name in self._explicit_context:
            return self._explicit_context[name]

        # 2. Contact-derived
        if name.startswith("contact_") and self._contact:
            value = self._resolve_contact(name)
            if value is not None:
                return value

        # 3. Deal-derived
        if name.startswith("deal_") and self._deal:
            value = self._resolve_deal(name)
            if value is not None:
                return value

        # 4. Account-derived
        if name.startswith("account_") and self._account:
            value = self._resolve_account(name)
            if value is not None:
                return value

        # Also check account via contact or deal if no explicit account set
        if name == "contact_company":
            company = self._get_contact_company()
            if company is not None:
                return company

        # 5. User-derived
        if name.startswith("user_"):
            return self._resolve_user(name)

        # 6. Tenant-derived
        if name.startswith("company_"):
            return self._resolve_tenant(name)

        # 7. Date-derived
        date_value = self._resolve_date(name)
        if date_value is not None:
            return date_value

        return None

    def _resolve_contact(self, name: str) -> str | None:
        if not self._contact:
            return None
        mapping: dict[str, str | None] = {
            "contact_name": self._contact.full_name,
            "contact_first_name": self._contact.first_name,
            "contact_last_name": self._contact.last_name,
            "contact_email": self._contact.email,
            "contact_phone": self._contact.phone,
            "contact_job_title": self._contact.job_title,
        }
        val = mapping.get(name)
        return str(val) if val else None

    def _get_contact_company(self) -> str | None:
        if self._contact and self._contact.account:
            return self._contact.account.name
        return None

    def _resolve_deal(self, name: str) -> str | None:
        if not self._deal:
            return None

        if name == "deal_name":
            return self._deal.name
        if name == "deal_value":
            return self._format_currency(self._deal.value, self._deal.currency)
        if name == "deal_currency":
            return self._deal.currency
        if name == "deal_stage":
            return self._deal.stage.name if self._deal.stage_id else None
        if name == "deal_pipeline":
            return self._deal.pipeline.name if self._deal.pipeline_id else None
        if name == "deal_owner":
            if self._deal.owner_id:
                owner = User.objects.filter(id=self._deal.owner_id).first()
                return owner.get_full_name() or owner.email if owner else None
            return None
        if name == "deal_expected_close":
            if self._deal.expected_close_date:
                return self._deal.expected_close_date.strftime("%b %d, %Y")
            return None
        if name == "deal_probability":
            prob = self._deal.win_probability
            return f"{int(prob * 100)}%"

        return None

    def _resolve_account(self, name: str) -> str | None:
        if not self._account:
            return None
        mapping: dict[str, str] = {
            "account_name": self._account.name,
            "account_domain": self._account.domain,
            "account_industry": self._account.industry,
        }
        return mapping.get(name)

    def _resolve_user(self, name: str) -> str | None:
        if name == "user_name":
            return self.user.get_full_name() or self.user.email
        if name == "user_email":
            return self.user.email
        if name == "user_first_name":
            return self.user.first_name or self.user.email.split("@")[0]
        if name == "user_signature":
            # User.email_signature does not exist yet — returns None (unresolved)
            return None
        return None

    def _resolve_tenant(self, name: str) -> str | None:
        """Resolve {{company_*}} variables from tenant settings."""
        try:
            settings = getattr(self.tenant, "settings", None) or {}
            if name == "company_name":
                return getattr(settings, "company_name", None) or getattr(self.tenant, "name", None) or str(self.tenant.id)
            if name == "company_phone":
                return getattr(settings, "company_phone", None) or ""
        except Exception:
            pass
        return None

    def _resolve_date(self, name: str) -> str | None:
        now = timezone.now()
        today = now.date()
        if name == "today":
            return today.strftime("%B %-d, %Y")
        if name == "tomorrow":
            return (today + timedelta(days=1)).strftime("%B %-d, %Y")
        if name == "next_week":
            return (today + timedelta(days=7)).strftime("%B %-d, %Y")
        if name == "next_month":
            return (today + timedelta(days=30)).strftime("%B %-d, %Y")
        if name == "current_time":
            return now.strftime("%-I:%M %p")
        return None

    @staticmethod
    def _format_currency(value: Decimal, currency: str) -> str:
        """Format a decimal value as a readable currency string."""
        try:
            value_float = float(value)
            if value_float >= 1_000_000:
                return f"{currency} ${value_float / 1_000_000:,.1f}M"
            if value_float >= 1_000:
                return f"{currency} ${value_float:,.0f}"
            return f"{currency} ${value_float:,.2f}"
        except (ValueError, TypeError):
            return f"{currency} $0.00"

    @staticmethod
    def get_variable_catalog() -> dict[str, list[dict[str, str]]]:
        """Return the full catalog of available variables grouped by category."""
        return {
            "contact": [
                {"name": "contact_name", "label": "Contact Full Name", "source": "contact.first_name + last_name"},
                {"name": "contact_first_name", "label": "Contact First Name", "source": "contact.first_name"},
                {"name": "contact_last_name", "label": "Contact Last Name", "source": "contact.last_name"},
                {"name": "contact_email", "label": "Contact Email", "source": "contact.email"},
                {"name": "contact_phone", "label": "Contact Phone", "source": "contact.phone"},
                {"name": "contact_job_title", "label": "Contact Job Title", "source": "contact.job_title"},
                {"name": "contact_company", "label": "Contact's Company", "source": "contact.account.name"},
            ],
            "deal": [
                {"name": "deal_name", "label": "Deal Name", "source": "deal.name"},
                {"name": "deal_value", "label": "Deal Value", "source": "deal.value (formatted)"},
                {"name": "deal_currency", "label": "Deal Currency", "source": "deal.currency"},
                {"name": "deal_stage", "label": "Deal Stage", "source": "deal.stage.name"},
                {"name": "deal_pipeline", "label": "Pipeline Name", "source": "deal.pipeline.name"},
                {"name": "deal_owner", "label": "Deal Owner", "source": "deal.owner.name"},
                {"name": "deal_expected_close", "label": "Expected Close Date", "source": "deal.expected_close_date (formatted)"},
                {"name": "deal_probability", "label": "Deal Probability", "source": "deal.stage.probability"},
            ],
            "account": [
                {"name": "account_name", "label": "Company Name", "source": "account.name"},
                {"name": "account_domain", "label": "Company Domain", "source": "account.domain"},
                {"name": "account_industry", "label": "Industry", "source": "account.industry"},
            ],
            "user": [
                {"name": "user_name", "label": "Your Full Name", "source": "user.get_full_name()"},
                {"name": "user_email", "label": "Your Email", "source": "user.email"},
                {"name": "user_first_name", "label": "Your First Name", "source": "user.first_name"},
                {"name": "user_signature", "label": "Your Email Signature", "source": "user.email_signature (new field)"},
            ],
            "date": [
                {"name": "today", "label": "Today's Date", "source": "current date (MMMM D, YYYY)"},
                {"name": "tomorrow", "label": "Tomorrow's Date", "source": "MMMM D, YYYY"},
                {"name": "next_week", "label": "Next Week (7 days)", "source": "MMMM D, YYYY"},
                {"name": "next_month", "label": "Next Month (30 days)", "source": "MMMM D, YYYY"},
                {"name": "current_time", "label": "Current Time", "source": "h:MM AM/PM"},
            ],
            "tenant": [
                {"name": "company_name", "label": "Company Name", "source": "tenant.settings.company_name"},
                {"name": "company_phone", "label": "Company Phone", "source": "tenant.settings.company_phone"},
            ],
        }
