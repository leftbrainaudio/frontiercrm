"""
Management command to seed FrontierCRM with rich demo data.

Usage:
    python manage.py seed_data              # seed Demo Corp (primary)
    python manage.py seed_data --tenant all  # seed all tenants
    python manage.py seed_data --clear       # clear existing seed data first

Creates realistic sample pipelines, stages, accounts, contacts, deals,
activities, tasks, notes, and email messages for demo purposes.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.activities.models import Activity
from apps.contacts.models import Account, Contact
from apps.email.models import EmailMessage
from apps.notes.models import Note
from apps.pipelines.models import Deal, Pipeline, Stage
from apps.tasks.models import TaskItem
from apps.teams.models import Membership, Role, Team, Tenant

# ── Pipelines and Stages ──────────────────────────────────────────────────────

SALES_PIPELINE_STAGES: list[tuple[str, float, str]] = [
    ("Lead Generated", 0.10, "#6B7280"),
    ("Qualified", 0.25, "#3B82F6"),
    ("Discovery", 0.50, "#8B5CF6"),
    ("Proposal", 0.75, "#F59E0B"),
    ("Negotiation", 0.90, "#F97316"),
    ("Closed Won", 1.00, "#10B981"),
    ("Closed Lost", 0.00, "#EF4444"),
]

SUPPORT_PIPELINE_STAGES: list[tuple[str, float, str]] = [
    ("New Ticket", 0.05, "#6B7280"),
    ("Triaged", 0.20, "#3B82F6"),
    ("In Progress", 0.50, "#8B5CF6"),
    ("Awaiting Customer", 0.40, "#F59E0B"),
    ("Resolved", 0.95, "#10B981"),
    ("Closed", 1.00, "#6B7280"),
]

# ── Demo Accounts ─────────────────────────────────────────────────────────────

ACCOUNTS: list[dict[str, Any]] = [
    {
        "name": "TechNova Solutions",
        "domain": "technova.io",
        "industry": "SaaS / Cloud Infrastructure",
        "description": "Leading provider of cloud-native infrastructure monitoring and observability platforms. Their flagship product, NovaWatch, serves over 2,000 enterprise customers worldwide.",
        "website": "https://technova.io",
        "phone": "+1-415-555-0101",
        "city": "San Francisco",
        "state": "CA",
        "country": "United States",
        "employees_count": 650,
        "annual_revenue": Decimal("85000000.00"),
        "tags": ["saas", "cloud", "infrastructure", "tech"],
    },
    {
        "name": "GreenLeaf Analytics",
        "domain": "greenleafanalytics.com",
        "industry": "Data Analytics / ESG",
        "description": "Sustainability-focused analytics platform helping enterprises measure, report, and reduce their carbon footprint. Recently closed Series B funding.",
        "website": "https://greenleafanalytics.com",
        "phone": "+1-512-555-0202",
        "city": "Austin",
        "state": "TX",
        "country": "United States",
        "employees_count": 180,
        "annual_revenue": Decimal("22000000.00"),
        "tags": ["analytics", "sustainability", "esg", "series-b"],
    },
    {
        "name": "Meridian Health Systems",
        "domain": "meridianhealth.org",
        "industry": "Healthcare / HealthTech",
        "description": "Regional healthcare network operating 12 hospitals and 80+ clinics across the Pacific Northwest. Expanding digital health initiatives and patient engagement platforms.",
        "website": "https://meridianhealth.org",
        "phone": "+1-503-555-0303",
        "city": "Portland",
        "state": "OR",
        "country": "United States",
        "employees_count": 3200,
        "annual_revenue": Decimal("450000000.00"),
        "tags": ["healthcare", "enterprise", "expansion"],
    },
    {
        "name": "Apex Robotics",
        "domain": "apexrobotics.com",
        "industry": "Manufacturing / Robotics",
        "description": "Industrial robotics manufacturer specializing in collaborative robots (cobots) for automotive and electronics assembly lines. Major expansion into European markets.",
        "website": "https://apexrobotics.com",
        "phone": "+1-248-555-0404",
        "city": "Detroit",
        "state": "MI",
        "country": "United States",
        "employees_count": 420,
        "annual_revenue": Decimal("120000000.00"),
        "tags": ["manufacturing", "robotics", "expansion", "europe"],
    },
    {
        "name": "Stellar Payments",
        "domain": "stellarpayments.com",
        "industry": "Fintech / Payments",
        "description": "Next-gen payment processing platform for e-commerce and SaaS businesses. Offers instant settlement and AI-powered fraud detection. Fast-growing with 300% YoY revenue growth.",
        "website": "https://stellarpayments.com",
        "phone": "+1-646-555-0505",
        "city": "New York",
        "state": "NY",
        "country": "United States",
        "employees_count": 85,
        "annual_revenue": Decimal("15000000.00"),
        "tags": ["fintech", "payments", "high-growth", "startup"],
    },
]

# ── Contacts for each account ─────────────────────────────────────────────────

CONTACTS_BY_ACCOUNT: dict[str, list[dict[str, Any]]] = {
    "TechNova Solutions": [
        {
            "first_name": "Sarah",
            "last_name": "Chen",
            "email": "sarah.chen@technova.io",
            "phone": "+1-415-555-0102",
            "mobile": "+1-415-555-0199",
            "job_title": "Chief Technology Officer",
            "department": "Engineering",
            "city": "San Francisco",
            "state": "CA",
            "source": "referral",
            "tags": ["decision-maker", "technical"],
        },
        {
            "first_name": "Marcus",
            "last_name": "Johnson",
            "email": "marcus.johnson@technova.io",
            "phone": "+1-415-555-0103",
            "job_title": "VP of Engineering",
            "department": "Engineering",
            "city": "San Francisco",
            "state": "CA",
            "source": "referral",
            "tags": ["decision-maker", "technical", "champion"],
        },
    ],
    "GreenLeaf Analytics": [
        {
            "first_name": "Priya",
            "last_name": "Patel",
            "email": "priya@greenleafanalytics.com",
            "phone": "+1-512-555-0203",
            "mobile": "+1-512-555-0299",
            "job_title": "Chief Executive Officer",
            "department": "Executive",
            "city": "Austin",
            "state": "TX",
            "source": "outbound",
            "tags": ["decision-maker", "executive"],
        },
        {
            "first_name": "David",
            "last_name": "Kim",
            "email": "david.kim@greenleafanalytics.com",
            "phone": "+1-512-555-0204",
            "job_title": "Lead Data Scientist",
            "department": "Data Science",
            "city": "Austin",
            "state": "TX",
            "source": "outbound",
            "tags": ["technical", "champion"],
        },
    ],
    "Meridian Health Systems": [
        {
            "first_name": "Jennifer",
            "last_name": "Walsh",
            "email": "jennifer.walsh@meridianhealth.org",
            "phone": "+1-503-555-0303",
            "mobile": "+1-503-555-0399",
            "job_title": "Director of Operations",
            "department": "Operations",
            "city": "Portland",
            "state": "OR",
            "source": "inbound",
            "tags": ["decision-maker"],
        },
        {
            "first_name": "Robert",
            "last_name": "Torres",
            "email": "robert.torres@meridianhealth.org",
            "phone": "+1-503-555-0304",
            "job_title": "IT Manager",
            "department": "Information Technology",
            "city": "Portland",
            "state": "OR",
            "source": "inbound",
            "tags": ["technical", "evaluator"],
        },
    ],
    "Apex Robotics": [
        {
            "first_name": "Emily",
            "last_name": "Nakamura",
            "email": "e.nakamura@apexrobotics.com",
            "phone": "+1-248-555-0403",
            "job_title": "Chief Operating Officer",
            "department": "Operations",
            "city": "Detroit",
            "state": "MI",
            "source": "event",
            "tags": ["decision-maker", "executive"],
        },
        {
            "first_name": "James",
            "last_name": "Whitfield",
            "email": "j.whitfield@apexrobotics.com",
            "phone": "+1-248-555-0404",
            "job_title": "Procurement Manager",
            "department": "Procurement",
            "city": "Detroit",
            "state": "MI",
            "source": "event",
            "tags": ["evaluator"],
        },
    ],
    "Stellar Payments": [
        {
            "first_name": "Olivia",
            "last_name": "Martinez",
            "email": "olivia.m@stellarpayments.com",
            "phone": "+1-646-555-0503",
            "job_title": "Chief Financial Officer",
            "department": "Finance",
            "city": "New York",
            "state": "NY",
            "source": "referral",
            "tags": ["decision-maker", "financial"],
        },
        {
            "first_name": "Tom",
            "last_name": "Baker",
            "email": "tom.baker@stellarpayments.com",
            "phone": "+1-646-555-0504",
            "job_title": "Head of Product",
            "department": "Product",
            "city": "New York",
            "state": "NY",
            "source": "referral",
            "tags": ["champion", "product"],
        },
    ],
}

# ── Deals ─────────────────────────────────────────────────────────────────────

DEALS: list[dict[str, Any]] = [
    # TechNova — various stages
    {"name": "Enterprise Observability Platform", "account": "TechNova Solutions", "contact": "Sarah Chen", "pipeline": "Sales Pipeline", "stage": "Proposal", "value": 180000, "status": "open", "probability": None, "close_in_days": 30, "tags": ["enterprise", "observability"]},
    {"name": "NovaWatch API Integration", "account": "TechNova Solutions", "contact": "Marcus Johnson", "pipeline": "Sales Pipeline", "stage": "Discovery", "value": 65000, "status": "open", "probability": None, "close_in_days": 60, "tags": ["integration", "api"]},
    {"name": "Monitoring Add-on License", "account": "TechNova Solutions", "contact": "Sarah Chen", "pipeline": "Sales Pipeline", "stage": "Negotiation", "value": 42000, "status": "open", "probability": None, "close_in_days": 14, "tags": ["expansion", "upsell"]},
    # GreenLeaf
    {"name": "ESG Reporting Suite", "account": "GreenLeaf Analytics", "contact": "Priya Patel", "pipeline": "Sales Pipeline", "stage": "Proposal", "value": 95000, "status": "open", "probability": None, "close_in_days": 21, "tags": ["esg", "reporting"]},
    {"name": "Carbon Footprint Dashboard", "account": "GreenLeaf Analytics", "contact": "David Kim", "pipeline": "Sales Pipeline", "stage": "Discovery", "value": 35000, "status": "open", "probability": None, "close_in_days": 45, "tags": ["sustainability", "dashboard"]},
    # Meridian Health
    {"name": "Patient Engagement Platform", "account": "Meridian Health Systems", "contact": "Jennifer Walsh", "pipeline": "Sales Pipeline", "stage": "Qualified", "value": 250000, "status": "open", "probability": None, "close_in_days": 90, "tags": ["healthcare", "patient-portal", "enterprise"]},
    {"name": "Clinic Management System", "account": "Meridian Health Systems", "contact": "Robert Torres", "pipeline": "Sales Pipeline", "stage": "Discovery", "value": 85000, "status": "open", "probability": None, "close_in_days": 60, "tags": ["healthcare", "management"]},
    # Apex Robotics
    {"name": "Cobot Fleet Monitoring", "account": "Apex Robotics", "contact": "Emily Nakamura", "pipeline": "Sales Pipeline", "stage": "Qualified", "value": 145000, "status": "open", "probability": None, "close_in_days": 75, "tags": ["manufacturing", "iot"]},
    {"name": "Supply Chain Integration", "account": "Apex Robotics", "contact": "James Whitfield", "pipeline": "Sales Pipeline", "stage": "Lead Generated", "value": 55000, "status": "open", "probability": None, "close_in_days": 120, "tags": ["supply-chain", "integration"]},
    # Stellar Payments
    {"name": "Payment Processing Upgrade", "account": "Stellar Payments", "contact": "Olivia Martinez", "pipeline": "Sales Pipeline", "stage": "Negotiation", "value": 78000, "status": "open", "probability": None, "close_in_days": 10, "tags": ["fintech", "payments"]},
    {"name": "Fraud Detection Module", "account": "Stellar Payments", "contact": "Tom Baker", "pipeline": "Sales Pipeline", "stage": "Proposal", "value": 125000, "status": "open", "probability": None, "close_in_days": 25, "tags": ["fintech", "ai", "fraud"]},
    # Closed deals
    {"name": "Infrastructure Monitoring Pilot", "account": "TechNova Solutions", "contact": "Marcus Johnson", "pipeline": "Sales Pipeline", "stage": "Closed Won", "value": 28000, "status": "won", "probability": None, "close_in_days": -45, "tags": ["pilot", "infrastructure"]},
    {"name": "Analytics PoC", "account": "GreenLeaf Analytics", "contact": "David Kim", "pipeline": "Sales Pipeline", "stage": "Closed Won", "value": 15000, "status": "won", "probability": None, "close_in_days": -30, "tags": ["poc", "analytics"]},
    {"name": "Legacy System Replacement", "account": "Meridian Health Systems", "contact": "Robert Torres", "pipeline": "Sales Pipeline", "stage": "Closed Lost", "value": 195000, "status": "lost", "close_reason": "Budget constraints — postponed to next fiscal year", "probability": None, "close_in_days": -60, "tags": ["healthcare", "lost"]},
    {"name": "Quick Invoice Integration", "account": "Apex Robotics", "contact": "James Whitfield", "pipeline": "Sales Pipeline", "stage": "Closed Won", "value": 12000, "status": "won", "probability": None, "close_in_days": -90, "tags": ["invoice", "integration"]},
    {"name": "Startup Discount Tier", "account": "Stellar Payments", "contact": "Tom Baker", "pipeline": "Sales Pipeline", "stage": "Closed Lost", "value": 8000, "status": "lost", "close_reason": "Chose competitor with lower pricing", "probability": None, "close_in_days": -15, "tags": ["startup", "lost"]},
]

# ── Activities ────────────────────────────────────────────────────────────────

ACTIVITY_TEMPLATES: list[dict[str, Any]] = [
    {"type": "call", "title": "Discovery call with {contact}", "duration": 30, "call_outcome": "Interested — scheduled demo"},
    {"type": "call", "title": "Follow-up call with {contact}", "duration": 15, "call_outcome": "Left voicemail"},
    {"type": "meeting", "title": "Product demo — {account}", "duration": 60, "call_outcome": ""},
    {"type": "meeting", "title": "Quarterly review with {account}", "duration": 45, "call_outcome": ""},
    {"type": "email", "title": "Sent proposal to {contact}", "duration": 0, "call_outcome": ""},
    {"type": "email", "title": "Follow-up on {deal}", "duration": 0, "call_outcome": ""},
    {"type": "call", "title": "Contract negotiation call with {contact}", "duration": 45, "call_outcome": "Agreed on pricing — pending legal review"},
    {"type": "meeting", "title": "Executive briefing — {account}", "duration": 90, "call_outcome": ""},
]

# ── Tasks ─────────────────────────────────────────────────────────────────────

TASK_TEMPLATES: list[dict[str, Any]] = [
    {"title": "Prepare demo environment for {account}", "priority": "high", "status": "done"},
    {"title": "Send follow-up email to {contact}", "priority": "medium", "status": "done"},
    {"title": "Draft proposal for {deal}", "priority": "high", "status": "in_progress"},
    {"title": "Schedule executive meeting with {account}", "priority": "medium", "status": "todo"},
    {"title": "Research {account} competitors", "priority": "low", "status": "done"},
    {"title": "Prepare pricing quote for {deal}", "priority": "urgent", "status": "todo"},
    {"title": "Send NDA to {contact}", "priority": "medium", "status": "done"},
    {"title": "Review contract terms with {account}", "priority": "high", "status": "in_progress"},
    {"title": "Update CRM fields for {deal}", "priority": "low", "status": "done"},
    {"title": "Quarterly business review prep — {account}", "priority": "high", "status": "todo"},
    {"title": "Follow up on invoice for {deal}", "priority": "medium", "status": "pending"},
]

# ── Notes ─────────────────────────────────────────────────────────────────────

NOTE_TEMPLATES: list[dict[str, Any]] = [
    {"title": "Call notes — {contact}", "content": "Discussed their key requirements for our platform. They need:\n- Real-time monitoring dashboards\n- Custom alert thresholds\n- Integration with existing Slack and PagerDuty workflows\n- SSO/SAML authentication\n\nNext step: schedule technical deep-dive with their engineering team."},
    {"title": "Meeting notes — {account}", "content": "Quarterly business review with the {account} team. Key points:\n- Current satisfaction score: 8.5/10\n- Top pain point: onboarding time\n- Interest in premium tier features\n- Budget approved for Q3 expansion\n\nAction: Send proposal by end of week."},
    {"title": "Product feedback — {deal}", "content": "During the demo, the team was very impressed with:\n- API documentation quality\n- Webhook customization\n- Dashboard filtering options\n\nConcerns raised:\n- Data retention limits\n- Pricing at higher tiers\n\nFollow-up with product team on data retention roadmap."},
]


def _pick_random(items: list[Any], k: int = 1) -> list[Any]:
    """Pick k random items from a list."""
    return random.sample(items, min(k, len(items)))


class Command(BaseCommand):
    help = "Seed FrontierCRM with realistic demo data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove all existing seed data before seeding",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            default="demo",
            help="Tenant to seed: 'demo' (default), 'all', or a tenant UUID",
        )

    def _clear_data(self):
        """Remove all seed data (business entities) keeping only users/tenants."""
        self.stdout.write("Clearing existing seed data...")
        Note.objects.all().delete()
        TaskItem.objects.all().delete()
        Activity.objects.all().delete()
        EmailMessage.objects.all().delete()
        Deal.objects.all().delete()
        Stage.objects.all().delete()
        Pipeline.objects.all().delete()
        Contact.objects.all().delete()
        Account.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("  Cleared all seed data"))

    def _get_tenants(self, tenant_arg: str) -> list[Tenant]:
        """Resolve the tenant(s) to seed."""
        if tenant_arg == "all":
            return list(Tenant.objects.filter(is_active=True))
        if tenant_arg == "demo":
            tenant = Tenant.objects.filter(subdomain="demo-corp").first()
            if not tenant:
                tenant = Tenant.objects.order_by("created_at").first()
            return [tenant] if tenant else []
        # Try UUID
        try:
            from uuid import UUID
            tenant = Tenant.objects.get(id=UUID(tenant_arg))
            return [tenant]
        except (ValueError, Tenant.DoesNotExist):
            self.stderr.write(self.style.ERROR(f"Tenant '{tenant_arg}' not found"))
            return []

    def _get_or_create_user(self, tenant: Tenant, is_owner: bool = True) -> User:
        """Get the tenant's owner user (or first user)."""
        membership = Membership.objects.filter(
            tenant=tenant, is_owner=is_owner
        ).select_related("user").first()
        if not membership:
            membership = Membership.objects.filter(
                tenant=tenant
            ).select_related("user").first()
        return membership.user if membership else None

    def _seed_pipelines_and_stages(self, tenant_id: str) -> dict[str, Pipeline]:
        """Create pipelines and their stages. Returns {pipeline_name: pipeline}."""
        pipelines = {}

        # Sales Pipeline
        sales_pipeline, _ = Pipeline.objects.get_or_create(
            tenant_id=tenant_id,
            name="Sales Pipeline",
            defaults={
                "description": "Standard sales pipeline for tracking opportunities from lead to close",
                "is_default": True,
                "is_active": True,
            },
        )
        for order, (name, prob, color) in enumerate(SALES_PIPELINE_STAGES):
            Stage.objects.get_or_create(
                tenant_id=tenant_id,
                pipeline=sales_pipeline,
                name=name,
                defaults={
                    "display_order": order,
                    "probability": Decimal(str(prob)),
                    "color": color,
                    "is_active": True,
                },
            )
        pipelines["Sales Pipeline"] = sales_pipeline
        self.stdout.write(f"  Created Sales Pipeline with {len(SALES_PIPELINE_STAGES)} stages")

        # Support Pipeline
        support_pipeline, _ = Pipeline.objects.get_or_create(
            tenant_id=tenant_id,
            name="Support Pipeline",
            defaults={
                "description": "Support ticket pipeline for tracking customer issues",
                "is_default": False,
                "is_active": True,
            },
        )
        for order, (name, prob, color) in enumerate(SUPPORT_PIPELINE_STAGES):
            Stage.objects.get_or_create(
                tenant_id=tenant_id,
                pipeline=support_pipeline,
                name=name,
                defaults={
                    "display_order": order,
                    "probability": Decimal(str(prob)),
                    "color": color,
                    "is_active": True,
                },
            )
        pipelines["Support Pipeline"] = support_pipeline
        self.stdout.write(f"  Created Support Pipeline with {len(SUPPORT_PIPELINE_STAGES)} stages")

        return pipelines

    def _seed_accounts_and_contacts(self, tenant_id: str) -> dict[str, Account]:
        """Create accounts and contacts. Returns {account_name: account}."""
        accounts_map = {}

        for acct_data in ACCOUNTS:
            acct, created = Account.objects.get_or_create(
                tenant_id=tenant_id,
                name=acct_data["name"],
                defaults={
                    "domain": acct_data["domain"],
                    "industry": acct_data["industry"],
                    "description": acct_data["description"],
                    "website": acct_data["website"],
                    "phone": acct_data["phone"],
                    "city": acct_data["city"],
                    "state": acct_data["state"],
                    "country": acct_data["country"],
                    "employees_count": acct_data["employees_count"],
                    "annual_revenue": acct_data["annual_revenue"],
                    "tags": acct_data["tags"],
                },
            )
            accounts_map[acct_data["name"]] = acct

            if created:
                self.stdout.write(f"  Created account: {acct.name}")

            # Create contacts for this account
            for contact_data in CONTACTS_BY_ACCOUNT.get(acct_data["name"], []):
                contact, c_created = Contact.objects.get_or_create(
                    tenant_id=tenant_id,
                    email=contact_data["email"],
                    defaults={
                        "account": acct,
                        "first_name": contact_data["first_name"],
                        "last_name": contact_data["last_name"],
                        "phone": contact_data.get("phone", ""),
                        "mobile": contact_data.get("mobile", ""),
                        "job_title": contact_data.get("job_title", ""),
                        "department": contact_data.get("department", ""),
                        "city": contact_data.get("city", ""),
                        "state": contact_data.get("state", ""),
                        "country": contact_data.get("country", ""),
                        "source": contact_data.get("source", ""),
                        "tags": contact_data.get("tags", []),
                    },
                )
                if c_created:
                    self.stdout.write(f"  Created contact: {contact.full_name}")

        return accounts_map

    def _seed_deals(
        self,
        tenant_id: str,
        accounts_map: dict[str, Account],
        pipelines: dict[str, Pipeline],
        now: datetime,
    ) -> list[Deal]:
        """Create deals. Returns list of created deals."""
        deals_created: list[Deal] = []

        for deal_data in DEALS:
            account = accounts_map.get(deal_data["account"])
            if not account:
                continue

            contact_email_map = {}
            for c in Contact.objects.filter(tenant_id=tenant_id, account=account):
                contact_email_map[f"{c.first_name} {c.last_name}"] = c
            contact = contact_email_map.get(deal_data["contact"])

            pipeline = pipelines.get(deal_data["pipeline"])
            if not pipeline:
                continue

            stage_name = deal_data["stage"]
            stage = Stage.objects.filter(
                tenant_id=tenant_id, pipeline=pipeline, name=stage_name
            ).first()
            if not stage:
                continue

            close_date = (
                now.date() + timedelta(days=deal_data["close_in_days"])
                if deal_data["close_in_days"] >= 0
                else now.date() + timedelta(days=deal_data["close_in_days"])
            )

            deal, created = Deal.objects.get_or_create(
                tenant_id=tenant_id,
                name=deal_data["name"],
                defaults={
                    "pipeline": pipeline,
                    "stage": stage,
                    "contact": contact,
                    "account": account,
                    "value": Decimal(str(deal_data["value"])),
                    "currency": "USD",
                    "status": deal_data["status"],
                    "probability": (
                        Decimal(str(deal_data["probability"]))
                        if deal_data.get("probability") is not None
                        else None
                    ),
                    "expected_close_date": close_date,
                    "close_reason": deal_data.get("close_reason", ""),
                    "tags": deal_data.get("tags", []),
                    "description": "",
                    "entered_stage_at": now - timedelta(days=random.randint(1, 14)),
                    "closed_at": (
                        now - timedelta(days=abs(deal_data["close_in_days"]))
                        if deal_data["status"] in ("won", "lost")
                        else None
                    ),
                },
            )
            if created:
                deals_created.append(deal)
                self.stdout.write(f"  Created deal: {deal.name} ({stage_name}, ${deal.value:,})")

        return deals_created

    def _seed_activities(
        self,
        tenant_id: str,
        accounts_map: dict[str, Account],
        deals: list[Deal],
        user: User,
        now: datetime,
    ):
        """Create activity feed entries."""
        count = 0

        for deal in deals[:8]:  # Activities for first 8 deals
            contact = deal.contact
            account = deal.account
            for template in _pick_random(ACTIVITY_TEMPLATES, k=2):
                title = template["title"].format(
                    contact=contact.full_name if contact else "Prospect",
                    account=account.name if account else deal.name,
                    deal=deal.name,
                )
                # Random recent time
                activity_time = now - timedelta(
                    days=random.randint(1, 30),
                    hours=random.randint(0, 12),
                )

                Activity.objects.get_or_create(
                    tenant_id=tenant_id,
                    activity_type=template["type"],
                    title=title,
                    entity_type="deal",
                    entity_id=deal.id,
                    defaults={
                        "actor_id": user.id if user else None,
                        "duration_minutes": template["duration"],
                        "call_outcome": template["call_outcome"],
                        "created_at": activity_time,
                    },
                )
                count += 1

        # Some contact-level activities
        contacts = list(Contact.objects.filter(tenant_id=tenant_id))
        for contact in _pick_random(contacts, k=6):
            activity_time = now - timedelta(days=random.randint(1, 45), hours=random.randint(0, 12))
            a_type = random.choice(["call", "meeting", "email"])
            Activity.objects.get_or_create(
                tenant_id=tenant_id,
                activity_type=a_type,
                title=f"{'Call' if a_type == 'call' else 'Meeting' if a_type == 'meeting' else 'Email'} with {contact.full_name}",
                entity_type="contact",
                entity_id=contact.id,
                defaults={
                    "actor_id": user.id if user else None,
                    "duration_minutes": random.choice([15, 30, 45, 60]),
                    "call_outcome": "Completed" if a_type != "email" else "",
                    "created_at": activity_time,
                },
            )
            count += 1

        if count:
            self.stdout.write(f"  Created {count} activities")

    def _seed_tasks(
        self,
        tenant_id: str,
        accounts_map: dict[str, Account],
        deals: list[Deal],
        user: User,
        now: datetime,
    ):
        """Create task items."""
        count = 0
        contacts = list(Contact.objects.filter(tenant_id=tenant_id))

        for deal in deals:
            account = deal.account
            contact = deal.contact
            for template in _pick_random(TASK_TEMPLATES, k=2):
                title = template["title"].format(
                    contact=contact.full_name if contact else "Prospect",
                    account=account.name if account else deal.name,
                    deal=deal.name,
                )
                status = template["status"]
                due_at = None
                completed_at = None
                if status == "todo":
                    due_at = now + timedelta(days=random.randint(1, 14))
                elif status == "in_progress":
                    due_at = now + timedelta(days=random.randint(1, 7))
                elif status == "done":
                    completed_at = now - timedelta(days=random.randint(1, 14))

                TaskItem.objects.get_or_create(
                    tenant_id=tenant_id,
                    title=title,
                    entity_type="deal",
                    entity_id=deal.id,
                    defaults={
                        "description": f"Task related to {deal.name} at {account.name if account else 'Unknown'}",
                        "priority": template["priority"],
                        "status": status,
                        "due_at": due_at,
                        "completed_at": completed_at,
                        "owner_id": user.id if user else None,
                        "assignee_id": user.id if user else None,
                    },
                )
                count += 1

        # Some contact-level tasks
        for contact in _pick_random(contacts, k=5):
            TaskItem.objects.get_or_create(
                tenant_id=tenant_id,
                title=f"Follow up with {contact.full_name}",
                entity_type="contact",
                entity_id=contact.id,
                defaults={
                    "description": f"Follow-up call/email with {contact.full_name} at {contact.account.name if contact.account else 'N/A'}",
                    "priority": random.choice(["low", "medium", "high"]),
                    "status": "todo",
                    "due_at": now + timedelta(days=random.randint(2, 21)),
                    "owner_id": user.id if user else None,
                    "assignee_id": user.id if user else None,
                },
            )
            count += 1

        if count:
            self.stdout.write(f"  Created {count} tasks")

    def _seed_notes(
        self,
        tenant_id: str,
        accounts_map: dict[str, Account],
        deals: list[Deal],
        user: User,
        now: datetime,
    ):
        """Create notes for deals and contacts."""
        count = 0

        for deal in deals[:6]:
            contact = deal.contact
            account = deal.account
            template = random.choice(NOTE_TEMPLATES)
            title = template["title"].format(
                contact=contact.full_name if contact else "Prospect",
                account=account.name if account else deal.name,
                deal=deal.name,
            )
            content = template["content"].format(
                contact=contact.full_name if contact else "Prospect",
                account=account.name if account else deal.name,
                deal=deal.name,
            )

            Note.objects.get_or_create(
                tenant_id=tenant_id,
                title=title,
                entity_type="deal",
                entity_id=deal.id,
                defaults={
                    "content": content,
                    "content_html": content.replace("\n", "<br>"),
                    "owner_id": user.id if user else None,
                    "created_at": now - timedelta(days=random.randint(1, 20)),
                },
            )
            count += 1

        # Some contact notes
        contacts = list(Contact.objects.filter(tenant_id=tenant_id))
        for contact in _pick_random(contacts, k=4):
            Note.objects.get_or_create(
                tenant_id=tenant_id,
                title=f"Notes on {contact.full_name}",
                entity_type="contact",
                entity_id=contact.id,
                defaults={
                    "content": f"Initial contact with {contact.full_name} ({contact.job_title}) at {contact.account.name if contact.account else 'N/A'}.\n\nDiscussed their current CRM setup and pain points. Interested in scheduling a demo for their team.\n\n{contact.email} | {contact.phone if contact.phone else 'No phone on file'}",
                    "content_html": f"<p>Initial contact with {contact.full_name} ({contact.job_title}) at {contact.account.name if contact.account else 'N/A'}.</p><p>Discussed their current CRM setup and pain points. Interested in scheduling a demo for their team.</p>",
                    "owner_id": user.id if user else None,
                    "created_at": now - timedelta(days=random.randint(1, 30)),
                },
            )
            count += 1

        if count:
            self.stdout.write(f"  Created {count} notes")

    def _seed_emails(
        self,
        tenant_id: str,
        accounts_map: dict[str, Account],
        deals: list[Deal],
        user: User,
        now: datetime,
    ):
        """Create sample email messages."""
        if not user:
            return

        count = 0
        email_templates = [
            ("Re: Proposal — {deal}", "Thanks for sending over the proposal. We've reviewed it internally and have a few questions about the pricing structure. Could we schedule a quick call to discuss? \n\nBest,\n{contact}"),
            ("{deal} — Next Steps", "Hi team,\n\nFollowing up on our conversation yesterday. We're excited to move forward with this initiative. Please send over the implementation timeline and the technical requirements document.\n\nCheers,\n{contact}"),
            ("Re: Meeting Request — {account}", "Confirmed for next Tuesday at 2pm. I've invited the rest of our evaluation team so they can ask technical questions directly. Looking forward to it!\n\n{contact}"),
            ("Contract Review — {deal}", "Our legal team has reviewed the contract and has a few minor amendments. Attached is the redlined version. The changes are primarily around data processing terms and SLA definitions.\n\nRegards,\n{contact}"),
        ]

        for deal in deals[:6]:
            contact = deal.contact
            account = deal.account
            if not contact:
                continue
            subject_template, body_template = random.choice(email_templates)
            body = body_template.format(
                deal=deal.name,
                contact=contact.full_name,
                account=account.name if account else deal.name,
            )
            subject = subject_template.format(
                deal=deal.name,
                contact=contact.full_name,
                account=account.name if account else deal.name,
            )

            sent_at = now - timedelta(days=random.randint(1, 20), hours=random.randint(0, 12))
            EmailMessage.objects.get_or_create(
                tenant_id=tenant_id,
                message_id=f"demo-{deal.id.hex[:12]}-{count}",
                defaults={
                    "thread_id": f"thread-{deal.id.hex[:12]}",
                    "direction": random.choice(["inbound", "outbound"]),
                    "from_email": contact.email,
                    "to_emails": [user.email],
                    "subject": subject,
                    "body_text": body,
                    "body_html": f"<p>{body.replace(chr(10), '<br>')}</p>",
                    "sent_at": sent_at,
                    "received_at": sent_at,
                    "is_read": random.choice([True, False]),
                    "is_starred": random.choice([True, False]),
                    "entity_type": "deal",
                    "entity_id": deal.id,
                },
            )
            count += 1

        if count:
            self.stdout.write(f"  Created {count} email messages")

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)  # Deterministic output
        now = timezone.now()

        clear = options["clear"]
        tenant_arg = options["tenant"]

        if clear:
            self._clear_data()

        tenants = self._get_tenants(tenant_arg)
        if not tenants:
            self.stderr.write(self.style.ERROR("No tenants found to seed"))
            return

        self.stdout.write(self.style.SUCCESS(f"\nSeeding data for {len(tenants)} tenant(s)..."))

        for tenant in tenants:
            self.stdout.write(self.style.SQL_FIELD(f"\n{'='*60}"))
            self.stdout.write(self.style.SQL_FIELD(f"  Tenant: {tenant.name} ({tenant.id})"))
            self.stdout.write(self.style.SQL_FIELD(f"{'='*60}"))

            tenant_id_str = str(tenant.id)
            user = self._get_or_create_user(tenant)

            # 1. Pipelines & Stages
            pipelines = self._seed_pipelines_and_stages(tenant_id_str)

            # 2. Accounts & Contacts
            accounts_map = self._seed_accounts_and_contacts(tenant_id_str)

            # 3. Deals
            deals = self._seed_deals(tenant_id_str, accounts_map, pipelines, now)

            # 4. Activities
            if deals and user:
                self._seed_activities(tenant_id_str, accounts_map, deals, user, now)

            # 5. Tasks
            if deals and user:
                self._seed_tasks(tenant_id_str, accounts_map, deals, user, now)

            # 6. Notes
            if deals and user:
                self._seed_notes(tenant_id_str, accounts_map, deals, user, now)

            # 7. Emails
            if deals and user:
                self._seed_emails(tenant_id_str, accounts_map, deals, user, now)

        # Summary
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS("  Seed Summary:"))
        self.stdout.write(self.style.SUCCESS(f"    Tenants:   {Tenant.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Users:     {User.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Accounts:  {Account.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Contacts:  {Contact.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Pipelines: {Pipeline.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Stages:    {Stage.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Deals:     {Deal.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Activities:{Activity.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Tasks:     {TaskItem.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Notes:     {Note.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Emails:    {EmailMessage.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"{'='*60}"))
        self.stdout.write(self.style.SUCCESS("\n✅ Demo data seeded successfully!"))
