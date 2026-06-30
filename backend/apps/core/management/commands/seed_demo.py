"""
Management command to seed FrontierCRM with realistic demo data.

Usage:
    python manage.py seed_demo

Creates:
    - Demo tenant + admin user (demo@frontiercrm.com / password123)
    - 4 pipeline stages (Discovery, Proposal, Negotiation, Closed Won)
    - 17 deals across stages with realistic names and amounts ($5k-$500k)
    - 12 contacts linked to deals with names, emails, phone, company, title
    - 25 activities (call, email, meeting) spread over the last 30 days

Idempotent — running twice does not duplicate data.
Uses bulk_create for performance where possible.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.activities.models import Activity
from apps.contacts.models import Account, Contact
from apps.pipelines.models import Deal, Pipeline, Stage
from apps.teams.models import Membership, Role, Team, Tenant

# ── Constants ──────────────────────────────────────────────────────────────────

DEMO_TENANT_NAME = "FrontierCRM Demo"
DEMO_TENANT_SUBDOMAIN = "demo"
DEMO_USER_EMAIL = "demo@frontiercrm.com"
DEMO_USER_PASSWORD = "password123"

# ── Pipeline Stages ────────────────────────────────────────────────────────────

PIPELINE_STAGES: list[dict[str, Any]] = [
    {"name": "Discovery",     "display_order": 0, "probability": "0.20", "color": "#3B82F6"},
    {"name": "Proposal",      "display_order": 1, "probability": "0.50", "color": "#F59E0B"},
    {"name": "Negotiation",   "display_order": 2, "probability": "0.75", "color": "#F97316"},
    {"name": "Closed Won",    "display_order": 3, "probability": "1.00", "color": "#10B981"},
]

# ── Accounts ───────────────────────────────────────────────────────────────────

ACCOUNTS: list[dict[str, Any]] = [
    {"name": "Acme Corp",           "domain": "acme.com",           "industry": "Technology",       "website": "https://acme.com",          "city": "San Francisco", "state": "CA", "country": "United States"},
    {"name": "Starfleet Industries", "domain": "starfleet.io",      "industry": "Defense / Aerospace", "website": "https://starfleet.io",    "city": "Seattle",       "state": "WA", "country": "United States"},
    {"name": "NovaPay",             "domain": "novapay.com",       "industry": "Fintech",            "website": "https://novapay.com",       "city": "New York",      "state": "NY", "country": "United States"},
    {"name": "GreenScape Energy",   "domain": "greenscape.io",     "industry": "Clean Energy",       "website": "https://greenscape.io",     "city": "Denver",        "state": "CO", "country": "United States"},
    {"name": "Pinnacle Health",     "domain": "pinnaclehealth.org","industry": "Healthcare",         "website": "https://pinnaclehealth.org","city": "Chicago",       "state": "IL", "country": "United States"},
    {"name": "Atlas Retail",        "domain": "atlasretail.com",   "industry": "Retail / E-commerce","website": "https://atlasretail.com",   "city": "Atlanta",       "state": "GA", "country": "United States"},
]

# ── Contacts ───────────────────────────────────────────────────────────────────

CONTACTS: list[dict[str, Any]] = [
    {"first_name": "Alice",    "last_name": "Wong",     "email": "alice.wong@acme.com",           "phone": "+1-415-555-0101", "job_title": "CTO",                    "account": "Acme Corp"},
    {"first_name": "Bob",      "last_name": "Martinez",  "email": "bob.martinez@acme.com",        "phone": "+1-415-555-0102", "job_title": "VP Engineering",          "account": "Acme Corp"},
    {"first_name": "Carol",    "last_name": "Davis",     "email": "carol.davis@starfleet.io",     "phone": "+1-206-555-0201", "job_title": "Director of Operations",   "account": "Starfleet Industries"},
    {"first_name": "Dan",      "last_name": "Khan",      "email": "dan.khan@starfleet.io",        "phone": "+1-206-555-0202", "job_title": "Chief Information Officer", "account": "Starfleet Industries"},
    {"first_name": "Eve",      "last_name": "Chen",      "email": "eve.chen@novapay.com",         "phone": "+1-212-555-0301", "job_title": "Head of Product",          "account": "NovaPay"},
    {"first_name": "Frank",    "last_name": "Okafor",    "email": "frank.okafor@novapay.com",     "phone": "+1-212-555-0302", "job_title": "CFO",                     "account": "NovaPay"},
    {"first_name": "Grace",    "last_name": "Lee",       "email": "grace.lee@greenscape.io",      "phone": "+1-303-555-0401", "job_title": "CEO",                     "account": "GreenScape Energy"},
    {"first_name": "Henry",    "last_name": "Singh",     "email": "henry.singh@greenscape.io",    "phone": "+1-303-555-0402", "job_title": "VP Sustainability",        "account": "GreenScape Energy"},
    {"first_name": "Ivy",      "last_name": "Thompson",  "email": "ivy.thompson@pinnaclehealth.org","phone": "+1-312-555-0501", "job_title": "Chief Medical Officer",   "account": "Pinnacle Health"},
    {"first_name": "Jack",     "last_name": "Liu",       "email": "jack.liu@pinnaclehealth.org",  "phone": "+1-312-555-0502", "job_title": "IT Director",              "account": "Pinnacle Health"},
    {"first_name": "Kate",     "last_name": "Rodriguez", "email": "kate.rodriguez@atlasretail.com","phone": "+1-404-555-0601", "job_title": "VP Digital",              "account": "Atlas Retail"},
    {"first_name": "Leo",      "last_name": "Park",      "email": "leo.park@atlasretail.com",     "phone": "+1-404-555-0602", "job_title": "Head of Supply Chain",     "account": "Atlas Retail"},
]

# ── Deals ──────────────────────────────────────────────────────────────────────

DEALS: list[dict[str, Any]] = [
    # Acme Corp
    {"name": "Acme Corp - Q4 Platform",         "account": "Acme Corp",           "contact": "Alice Wong",    "stage": "Negotiation", "value": 250000, "status": "open"},
    {"name": "Acme Corp - API Integration",     "account": "Acme Corp",           "contact": "Bob Martinez",  "stage": "Discovery",   "value": 45000,  "status": "open"},
    {"name": "Acme Corp - Security Audit",      "account": "Acme Corp",           "contact": "Alice Wong",    "stage": "Proposal",    "value": 85000,  "status": "open"},
    # Starfleet Industries
    {"name": "Starfleet - Data Migration",      "account": "Starfleet Industries","contact": "Carol Davis",   "stage": "Proposal",    "value": 180000, "status": "open"},
    {"name": "Starfleet - Fleet Comms Suite",   "account": "Starfleet Industries","contact": "Dan Khan",      "stage": "Discovery",   "value": 350000, "status": "open"},
    {"name": "Starfleet - Compliance Module",   "account": "Starfleet Industries","contact": "Carol Davis",   "stage": "Negotiation", "value": 120000, "status": "open"},
    # NovaPay
    {"name": "NovaPay - Payment Hub",           "account": "NovaPay",             "contact": "Eve Chen",      "stage": "Discovery",   "value": 195000, "status": "open"},
    {"name": "NovaPay - Fraud Detection",       "account": "NovaPay",             "contact": "Frank Okafor",  "stage": "Proposal",    "value": 95000,  "status": "open"},
    {"name": "NovaPay - Merchant Portal",       "account": "NovaPay",             "contact": "Eve Chen",      "stage": "Negotiation", "value": 75000,  "status": "open"},
    # GreenScape Energy
    {"name": "GreenScape - Grid Monitor",       "account": "GreenScape Energy",   "contact": "Grace Lee",     "stage": "Discovery",   "value": 280000, "status": "open"},
    {"name": "GreenScape - Solar Analytics",    "account": "GreenScape Energy",   "contact": "Henry Singh",   "stage": "Proposal",    "value": 62000,  "status": "open"},
    # Pinnacle Health
    {"name": "Pinnacle - Patient Portal",       "account": "Pinnacle Health",     "contact": "Ivy Thompson",  "stage": "Proposal",    "value": 420000, "status": "open"},
    {"name": "Pinnacle - EHR Integration",      "account": "Pinnacle Health",     "contact": "Jack Liu",      "stage": "Discovery",   "value": 155000, "status": "open"},
    # Atlas Retail
    {"name": "Atlas - E-commerce Suite",        "account": "Atlas Retail",        "contact": "Kate Rodriguez","stage": "Negotiation", "value": 310000, "status": "open"},
    {"name": "Atlas - Inventory AI",            "account": "Atlas Retail",        "contact": "Leo Park",      "stage": "Discovery",   "value": 88000,  "status": "open"},
    {"name": "Atlas - Loyalty Platform",        "account": "Atlas Retail",        "contact": "Kate Rodriguez","stage": "Proposal",    "value": 65000,  "status": "open"},
    # Closed Won
    {"name": "Acme Corp - Quick Start Pilot",   "account": "Acme Corp",           "contact": "Bob Martinez",  "stage": "Closed Won",  "value": 25000,  "status": "won"},
]

# ── Activity templates ────────────────────────────────────────────────────────

ACTIVITY_TYPES = ["call", "email", "meeting"]
ACTIVITY_TITLES_CALL = [
    "Discovery call with {contact}",
    "Follow-up call with {contact}",
    "Contract negotiation call with {contact}",
    "Quarterly review call — {account}",
]
ACTIVITY_TITLES_EMAIL = [
    "Sent proposal to {contact}",
    "Follow-up email on {deal}",
    "Shared pricing doc with {contact}",
    "Sent contract to {contact}",
]
ACTIVITY_TITLES_MEETING = [
    "Product demo for {account}",
    "Executive briefing — {account}",
    "Technical deep-dive with {contact}",
    "Kickoff meeting — {deal}",
]

ACTIVITY_OUTCOMES = {
    "call": ["Left voicemail", "Interested — scheduled demo", "Discussion went well", "No answer"],
    "email": ["", "", "", ""],
    "meeting": ["", "", "", ""],
}


def _format_activity_title(template: str, contact_name: str, account_name: str, deal_name: str) -> str:
    return template.format(contact=contact_name, account=account_name, deal=deal_name)


class Command(BaseCommand):
    help = "Seed FrontierCRM with realistic demo data for evaluation and testing"

    def _get_or_create_tenant(self) -> Tenant:
        tenant, created = Tenant.objects.get_or_create(
            subdomain=DEMO_TENANT_SUBDOMAIN,
            defaults={
                "name": DEMO_TENANT_NAME,
                "is_active": True,
                "max_users": 100,
            },
        )
        if created:
            self.stdout.write(f"  Created tenant: {tenant.name}")
        else:
            self.stdout.write(f"  Using existing tenant: {tenant.name}")
        return tenant

    def _get_or_create_user(self, tenant: Tenant) -> User:
        user, created = User.objects.get_or_create(
            email=DEMO_USER_EMAIL,
            defaults={
                "username": "demo",
                "first_name": "Demo",
                "last_name": "User",
                "tenant_id": tenant.id,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "email_verified": True,
                "is_onboarded": True,
            },
        )
        if created:
            user.set_password(DEMO_USER_PASSWORD)
            user.save(update_fields=["password"])
            self.stdout.write(f"  Created user: {user.email}")
        else:
            # Ensure password and admin flags are always correct for the demo user
            user.set_password(DEMO_USER_PASSWORD)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save(update_fields=["password", "is_staff", "is_superuser", "is_active"])
            self.stdout.write(f"  Using existing user: {user.email} (updated)")

        # Ensure membership exists
        Membership.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={"is_owner": True, "is_active": True},
        )
        return user

    def _seed_default_roles(self, tenant: Tenant) -> dict[str, Role]:
        """Create all 4 default roles on the tenant and return {name: role}."""
        from apps.core.role_defaults import DEFAULT_ROLES

        roles: dict[str, Role] = {}
        for role_def in DEFAULT_ROLES:
            r, _ = Role.objects.get_or_create(
                tenant=tenant,
                name=role_def["name"],
                defaults={
                    "description": role_def["description"],
                    "permissions": role_def["permissions"],
                    "is_admin": role_def.get("is_admin", False),
                },
            )
            roles[role_def["name"]] = r

        # Set up inheritance (Manager -> Sales Rep)
        if "Manager" in roles and "Sales Rep" in roles:
            roles["Manager"].inherits_from = roles["Sales Rep"]
            roles["Manager"].save(update_fields=["inherits_from"])

        self.stdout.write(f"  Created/seeded {len(roles)} default roles: {', '.join(roles.keys())}")
        return roles

    def _seed_pipeline_and_stages(self, tenant_id: str) -> Pipeline:
        pipeline, created = Pipeline.objects.get_or_create(
            tenant_id=tenant_id,
            name="Sales Pipeline",
            defaults={
                "description": "Standard deal pipeline for tracking opportunities",
                "is_default": True,
                "is_active": True,
            },
        )

        existing_count = Stage.objects.filter(tenant_id=tenant_id, pipeline=pipeline).count()
        if existing_count >= len(PIPELINE_STAGES):
            self.stdout.write(f"  Pipeline stages already exist ({existing_count}), skipping")
            return pipeline

        # Remove any existing stages for this pipeline (e.g. from partial seed)
        Stage.objects.filter(tenant_id=tenant_id, pipeline=pipeline).delete()

        stages = [
            Stage(
                tenant_id=tenant_id,
                pipeline=pipeline,
                name=s["name"],
                display_order=s["display_order"],
                probability=Decimal(s["probability"]),
                color=s["color"],
                is_active=True,
            )
            for s in PIPELINE_STAGES
        ]
        Stage.objects.bulk_create(stages)
        self.stdout.write(f"  Created {len(stages)} pipeline stages: {', '.join(s['name'] for s in PIPELINE_STAGES)}")
        return pipeline

    def _seed_accounts(self, tenant_id: str) -> dict[str, Account]:
        """Create accounts. Returns {account_name: account}."""
        existing = Account.objects.filter(tenant_id=tenant_id).count()
        if existing >= len(ACCOUNTS):
            self.stdout.write(f"  Accounts already exist ({existing}), skipping")
            accounts = {a.name: a for a in Account.objects.filter(tenant_id=tenant_id)}
            return accounts

        # Check which accounts need to be created
        existing_names = set(
            Account.objects.filter(tenant_id=tenant_id).values_list("name", flat=True)
        )
        to_create = [a for a in ACCOUNTS if a["name"] not in existing_names]

        if not to_create:
            self.stdout.write("  All accounts already exist, skipping")
            accounts = {a.name: a for a in Account.objects.filter(tenant_id=tenant_id)}
            return accounts

        accounts = [
            Account(
                tenant_id=tenant_id,
                name=a["name"],
                domain=a["domain"],
                industry=a["industry"],
                website=a["website"],
                city=a.get("city", ""),
                state=a.get("state", ""),
                country=a.get("country", ""),
                tags=[a["industry"].lower().replace(" / ", "-")],
            )
            for a in to_create
        ]
        Account.objects.bulk_create(accounts)
        self.stdout.write(f"  Created {len(accounts)} accounts")

        return {a.name: a for a in Account.objects.filter(tenant_id=tenant_id)}

    def _seed_contacts(self, tenant_id: str, accounts_map: dict[str, Account]) -> dict[str, Contact]:
        """Create contacts. Returns {contact_email: contact}."""
        existing = Contact.objects.filter(tenant_id=tenant_id).count()
        if existing >= len(CONTACTS):
            self.stdout.write(f"  Contacts already exist ({existing}), skipping")
            return {c.email: c for c in Contact.objects.filter(tenant_id=tenant_id)}

        existing_emails = set(
            Contact.objects.filter(tenant_id=tenant_id).values_list("email", flat=True)
        )
        to_create = [c for c in CONTACTS if c["email"] not in existing_emails]

        if not to_create:
            self.stdout.write("  All contacts already exist, skipping")
            return {c.email: c for c in Contact.objects.filter(tenant_id=tenant_id)}

        contacts = [
            Contact(
                tenant_id=tenant_id,
                account=accounts_map.get(c["account"]),
                first_name=c["first_name"],
                last_name=c["last_name"],
                email=c["email"],
                phone=c.get("phone", ""),
                job_title=c.get("job_title", ""),
                city=accounts_map.get(c["account"]).city if accounts_map.get(c["account"]) else "",
                state=accounts_map.get(c["account"]).state if accounts_map.get(c["account"]) else "",
            )
            for c in to_create
        ]
        Contact.objects.bulk_create(contacts)
        self.stdout.write(f"  Created {len(contacts)} contacts")

        return {c.email: c for c in Contact.objects.filter(tenant_id=tenant_id)}

    def _seed_deals(
        self,
        tenant_id: str,
        accounts_map: dict[str, Account],
        contacts_map: dict[str, Contact],
        pipeline: Pipeline,
        now: datetime,
    ) -> list[Deal]:
        """Create deals. Returns list of created deals."""
        existing = Deal.objects.filter(tenant_id=tenant_id).count()
        if existing >= len(DEALS):
            self.stdout.write(f"  Deals already exist ({existing}), skipping")
            return list(Deal.objects.filter(tenant_id=tenant_id))

        existing_names = set(
            Deal.objects.filter(tenant_id=tenant_id).values_list("name", flat=True)
        )
        to_create_data = [d for d in DEALS if d["name"] not in existing_names]

        if not to_create_data:
            self.stdout.write("  All deals already exist, skipping")
            return list(Deal.objects.filter(tenant_id=tenant_id))

        # Build stage lookup
        stages_by_name = {
            s.name: s
            for s in Stage.objects.filter(tenant_id=tenant_id, pipeline=pipeline)
        }

        deals = []
        for d in to_create_data:
            stage = stages_by_name.get(d["stage"])
            if not stage:
                self.stderr.write(f"  Warning: Stage '{d['stage']}' not found for deal '{d['name']}'")
                continue

            account = accounts_map.get(d["account"])
            contact = contacts_map.get(d["contact"])

            close_days = random.randint(14, 120)
            expected_close = now.date() + timedelta(days=close_days)

            deals.append(
                Deal(
                    tenant_id=tenant_id,
                    name=d["name"],
                    pipeline=pipeline,
                    stage=stage,
                    contact=contact,
                    account=account,
                    value=Decimal(str(d["value"])),
                    currency="USD",
                    status=d["status"],
                    expected_close_date=expected_close,
                    entered_stage_at=now - timedelta(days=random.randint(1, 21)),
                    closed_at=now - timedelta(days=random.randint(1, 30)) if d["status"] == "won" else None,
                    owner_id=None,
                    description=f"{d['name']} — {d['value']:,} USD deal {'won' if d['status'] == 'won' else 'in progress'}",
                    tags=[d["account"].lower().replace(" ", "-"), d["stage"].lower().replace(" ", "-")],
                )
            )

        if deals:
            Deal.objects.bulk_create(deals)
            self.stdout.write(f"  Created {len(deals)} deals")
        else:
            self.stdout.write("  No new deals to create")

        return list(Deal.objects.filter(tenant_id=tenant_id))

    def _seed_activities(
        self,
        tenant_id: str,
        deals: list[Deal],
        now: datetime,
    ):
        """Create 25 activities spread over last 30 days."""
        existing = Activity.objects.filter(tenant_id=tenant_id).count()
        if existing >= 25:
            self.stdout.write(f"  Activities already exist ({existing}), skipping")
            return

        activities = []
        random.seed(42)

        for i in range(25):
            deal = random.choice(deals)
            contact = deal.contact
            account = deal.account

            contact_name = contact.full_name if contact else "Prospect"
            account_name = account.name if account else deal.name

            act_type = random.choice(ACTIVITY_TYPES)
            days_ago = random.randint(0, 29)
            hours_ago = random.randint(0, 23)
            activity_time = now - timedelta(days=days_ago, hours=hours_ago)

            if act_type == "call":
                title_template = random.choice(ACTIVITY_TITLES_CALL)
                duration = random.choice([15, 30, 45])
                outcome = random.choice(ACTIVITY_OUTCOMES["call"])
            elif act_type == "email":
                title_template = random.choice(ACTIVITY_TITLES_EMAIL)
                duration = 0
                outcome = ""
            else:  # meeting
                title_template = random.choice(ACTIVITY_TITLES_MEETING)
                duration = random.choice([30, 45, 60, 90])
                outcome = ""

            title = _format_activity_title(title_template, contact_name, account_name, deal.name)

            activities.append(
                Activity(
                    tenant_id=tenant_id,
                    activity_type=act_type,
                    title=title,
                    description="",
                    entity_type="deal",
                    entity_id=deal.id,
                    metadata={},
                    actor_id=None,
                    duration_minutes=duration,
                    call_outcome=outcome,
                    created_at=activity_time,
                )
            )

        if activities:
            # Use created_at override via bulk_create — need to set it manually
            # since TimeStampedModel has default=timezone.now
            Activity.objects.bulk_create(activities)
            self.stdout.write(f"  Created {len(activities)} activities")

    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()

        self.stdout.write(self.style.SUCCESS("\n🌱 Seeding FrontierCRM demo data...\n"))

        # 1. Tenant
        tenant = self._get_or_create_tenant()
        tenant_id_str = str(tenant.id)

        # 2. Default roles
        roles = self._seed_default_roles(tenant)

        # 3. User
        user = self._get_or_create_user(tenant)

        # Assign admin role to the demo user's membership
        membership = Membership.objects.filter(user=user, tenant=tenant).first()
        if membership and not membership.role_id:
            membership.role = roles.get("Admin")
            membership.save(update_fields=["role"])
        _ = user  # user available for future use

        # 3. Pipeline & Stages
        pipeline = self._seed_pipeline_and_stages(tenant_id_str)

        # 4. Accounts
        accounts_map = self._seed_accounts(tenant_id_str)

        # 5. Contacts
        contacts_map = self._seed_contacts(tenant_id_str, accounts_map)

        # 6. Deals
        deals = self._seed_deals(tenant_id_str, accounts_map, contacts_map, pipeline, now)

        # 7. Activities
        if deals:
            self._seed_activities(tenant_id_str, deals, now)

        # Summary
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"  ✅ Demo data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS(f"  {'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"    Tenant:       {DEMO_TENANT_NAME}"))
        self.stdout.write(self.style.SUCCESS(f"    Admin user:   {DEMO_USER_EMAIL} / {DEMO_USER_PASSWORD}"))
        self.stdout.write(self.style.SUCCESS(f"    {'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"    Accounts:     {Account.objects.filter(tenant_id=tenant_id_str).count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Contacts:     {Contact.objects.filter(tenant_id=tenant_id_str).count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Stages:       {Stage.objects.filter(tenant_id=tenant_id_str).count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Deals:        {Deal.objects.filter(tenant_id=tenant_id_str).count()}"))
        self.stdout.write(self.style.SUCCESS(f"    Activities:   {Activity.objects.filter(tenant_id=tenant_id_str).count()}"))
        self.stdout.write(self.style.SUCCESS(f"    {'='*60}"))
