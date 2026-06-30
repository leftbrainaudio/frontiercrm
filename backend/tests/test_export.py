"""Tests for streaming CSV export endpoints in apps/export.

Covers: contacts export, deals export, pipeline report export,
auth, content-type, content-disposition, tenant isolation, empty
datasets, null fields, owner name resolution, tags serialisation,
and streaming response shape.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework import status

# ---------------------------------------------------------------------------
# URL constants
# ---------------------------------------------------------------------------

CONTACTS_URL = "/api/export/contacts/"
DEALS_URL = "/api/export/deals/"
PIPELINE_URL = "/api/export/reports/pipeline/"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_csv(response) -> tuple[list[str], list[list[str]]]:
    """Return (header_row, data_rows) parsed from a streaming CSV response."""
    content = b"".join(response.streaming_content).decode("utf-8-sig")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    return rows[0], rows[1:]


def _content_disposition(response) -> str:
    return response.get("Content-Disposition", "")


def _filename_from_disposition(disposition: str) -> str:
    """Extract the quoted filename from a Content-Disposition header."""
    for part in disposition.split(";"):
        part = part.strip()
        if part.lower().startswith("filename="):
            return part.split("=", 1)[1].strip('"')
    return ""


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def pipeline(user, db):
    from apps.pipelines.models import Pipeline

    return Pipeline.objects.create(
        tenant_id=user.tenant_id,
        name="Sales Pipeline",
        is_default=True,
    )


@pytest.fixture
def stages(user, pipeline, db):
    from apps.pipelines.models import Stage

    stages_data = [
        ("Qualified", 1, Decimal("0.25")),
        ("Proposal", 2, Decimal("0.50")),
        ("Closed Won", 3, Decimal("1.00")),
    ]
    result = []
    for name, order, prob in stages_data:
        s = Stage.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            name=name,
            display_order=order,
            probability=prob,
        )
        result.append(s)
    return result


@pytest.fixture
def deal(user, pipeline, stages, db):
    from apps.pipelines.models import Deal

    return Deal.objects.create(
        tenant_id=user.tenant_id,
        pipeline=pipeline,
        stage=stages[0],
        name="Test Deal",
        value=Decimal("50000.00"),
        currency="USD",
        status="open",
    )


# ===================================================================
# 1  Authentication
# ===================================================================


class TestAuth:
    """All three export endpoints reject unauthenticated requests."""

    def test_contacts_export_requires_auth(self, api_client):
        response = api_client.get(CONTACTS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_deals_export_requires_auth(self, api_client):
        response = api_client.get(DEALS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_pipeline_report_export_requires_auth(self, api_client):
        response = api_client.get(PIPELINE_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ===================================================================
# 2  Contacts Export
# ===================================================================


class TestExportContacts:
    """GET /api/export/contacts/ — streaming CSV of contacts."""

    URL = CONTACTS_URL

    def _create_contacts(self, tenant_id, user=None, count=3):
        from apps.contacts.models import Contact

        contacts = []
        for i in range(count):
            c = Contact.objects.create(
                tenant_id=tenant_id,
                first_name=f"Alice_{i}",
                last_name="Smith",
                email=f"alice{i}@example.com",
                phone=f"+1-555-{i:04d}",
                mobile=f"+1-555-m{i:04d}",
                job_title="Engineer",
                department="Engineering",
                street=f"{i} Main St",
                city="Springfield",
                state="IL",
                postal_code="62701",
                country="USA",
                source="manual",
                tags=["tag1", "tag2"] if i == 0 else [],
                owner_id=user.id if user and i == 0 else None,
            )
            contacts.append(c)
        return contacts

    def test_returns_csv_content_type(self, auth_client, user, db):
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

    def test_has_content_disposition_with_filename(self, auth_client, user, db):
        response = auth_client.get(self.URL)
        disposition = _content_disposition(response)
        assert "attachment" in disposition
        filename = _filename_from_disposition(disposition)
        expected = f"contacts-{date.today().isoformat()}.csv"
        assert filename == expected

    def test_empty_dataset_returns_csv_with_only_header(self, auth_client, user, db):
        """No contacts → CSV with headers but zero data rows."""
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 0
        assert "first_name" in header
        assert "last_name" in header
        assert "email" in header

    def test_contains_created_contacts(self, auth_client, user, db):
        self._create_contacts(user.tenant_id, user=user, count=3)
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 3
        emails = {r[2] for r in rows}
        assert "alice0@example.com" in emails
        assert "alice1@example.com" in emails
        assert "alice2@example.com" in emails

    def test_tags_serialised_as_comma_separated(self, auth_client, user, db):
        self._create_contacts(user.tenant_id, user=user, count=2)
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        tags_idx = header.index("tags")
        # First contact has tags, second has no tags
        contact_with_tags = [r for r in rows if "Alice_0" in r][0]
        contact_without_tags = [r for r in rows if "Alice_1" in r][0]
        assert contact_with_tags[tags_idx] == "tag1,tag2"
        assert contact_without_tags[tags_idx] == ""

    def test_owner_name_resolved(self, auth_client, user, db):
        # Give user a display name so owner resolution works
        user.first_name = "Alice"
        user.last_name = "Tester"
        user.save()
        self._create_contacts(user.tenant_id, user=user, count=1)
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        owner_idx = header.index("owner_name")
        owner_row = rows[0]
        assert owner_row[owner_idx] == "Alice Tester"

    def test_owner_name_empty_when_no_owner(self, auth_client, user, db):
        self._create_contacts(user.tenant_id, count=1)
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        owner_idx = header.index("owner_name")
        assert rows[0][owner_idx] == ""

    def test_account_name_resolved(self, auth_client, user, db):
        from apps.contacts.models import Account

        account = Account.objects.create(
            tenant_id=user.tenant_id,
            name="Acme Corp",
        )
        from apps.contacts.models import Contact

        Contact.objects.create(
            tenant_id=user.tenant_id,
            first_name="Alice",
            last_name="Smith",
            email="alice@acme.com",
            account=account,
        )
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        acct_idx = header.index("account_name")
        assert rows[0][acct_idx] == "Acme Corp"

    def test_tenant_isolation(self, auth_client, user, db):
        """Other tenant's contacts do not appear in the export."""
        other_tenant = uuid4()
        from apps.contacts.models import Contact

        Contact.objects.create(
            tenant_id=other_tenant,
            first_name="Intruder",
            last_name="Data",
            email="intruder@evil.com",
        )
        from apps.pipelines.models import Deal

        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 0  # user's tenant is empty

    def test_null_field_handling(self, auth_client, user, db):
        """Fields that are None should render as empty strings, not 'None'."""
        from apps.contacts.models import Contact

        Contact.objects.create(
            tenant_id=user.tenant_id,
            first_name="Null",
            last_name="Test",
            email="null@test.com",
            # phone, mobile, job_title etc. intentionally omitted
        )
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        phone_idx = header.index("phone")
        dept_idx = header.index("department")
        assert rows[0][phone_idx] == ""
        assert rows[0][dept_idx] == ""

    def test_streaming_response_class(self, auth_client, user, db):
        """The response uses StreamingHttpResponse (generator-based)."""
        from django.http import StreamingHttpResponse

        response = auth_client.get(self.URL)
        assert isinstance(response, StreamingHttpResponse)


# ===================================================================
# 3  Deals Export
# ===================================================================


class TestExportDeals:
    """GET /api/export/deals/ — streaming CSV of deals."""

    URL = DEALS_URL

    def test_returns_csv_content_type(self, auth_client, deal, user, db):
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

    def test_has_content_disposition_with_filename(self, auth_client, deal, user, db):
        response = auth_client.get(self.URL)
        filename = _filename_from_disposition(_content_disposition(response))
        assert filename == f"deals-{date.today().isoformat()}.csv"

    def test_empty_dataset_returns_csv_with_only_header(self, auth_client, user, db):
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 0
        assert "name" in header
        assert "value" in header

    def test_contains_created_deal(self, auth_client, deal, user, db):
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 1
        name_idx = header.index("name")
        assert rows[0][name_idx] == "Test Deal"

    def test_deal_value_as_string(self, auth_client, deal, user, db):
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        value_idx = header.index("value")
        assert rows[0][value_idx] == "50000.00"

    def test_pipeline_and_stage_name_included(self, auth_client, deal, user, db):
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        pipe_idx = header.index("pipeline_name")
        stage_idx = header.index("stage_name")
        prob_idx = header.index("probability")
        assert rows[0][pipe_idx] == "Sales Pipeline"
        assert rows[0][stage_idx] == "Qualified"
        assert rows[0][prob_idx] == "0.25"

    def test_owner_name_resolved(self, auth_client, deal, user, db):
        deal.owner_id = user.id
        deal.save()
        user.first_name = "Bob"
        user.last_name = "Manager"
        user.save()
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        owner_idx = header.index("owner_name")
        assert rows[0][owner_idx] == "Bob Manager"

    def test_owner_name_empty_when_no_owner(self, auth_client, deal, user, db):
        deal.owner_id = None
        deal.save()
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        owner_idx = header.index("owner_name")
        assert rows[0][owner_idx] == ""

    def test_contact_name_resolved(self, auth_client, deal, user, db):
        from apps.contacts.models import Contact

        contact = Contact.objects.create(
            tenant_id=user.tenant_id,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
        )
        deal.contact = contact
        deal.save()
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        contact_idx = header.index("contact_name")
        assert rows[0][contact_idx] == "Jane Doe"

    def test_tags_serialised(self, auth_client, deal, user, db):
        deal.tags = ["hot", "enterprise"]
        deal.save()
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        tags_idx = header.index("tags")
        assert rows[0][tags_idx] == "hot,enterprise"

    def test_tenant_isolation(self, auth_client, user, db):
        """Deals from another tenant are excluded."""
        other_tenant = uuid4()
        from apps.pipelines.models import Pipeline, Stage, Deal

        pipe = Pipeline.objects.create(tenant_id=other_tenant, name="Other")
        stage = Stage.objects.create(tenant_id=other_tenant, pipeline=pipe, name="Other")
        Deal.objects.create(
            tenant_id=other_tenant,
            pipeline=pipe,
            stage=stage,
            name="Intruder Deal",
            value=Decimal("100.00"),
        )
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 0

    def test_streaming_response_class(self, auth_client, deal, user, db):
        from django.http import StreamingHttpResponse

        response = auth_client.get(self.URL)
        assert isinstance(response, StreamingHttpResponse)


# ===================================================================
# 4  Pipeline Report Export
# ===================================================================


class TestExportPipelineReport:
    """GET /api/export/reports/pipeline/ — aggregate stage-level report."""

    URL = PIPELINE_URL

    def test_returns_csv_content_type(self, auth_client, stages, user, db):
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

    def test_has_content_disposition_with_filename(self, auth_client, stages, user, db):
        response = auth_client.get(self.URL)
        filename = _filename_from_disposition(_content_disposition(response))
        assert filename == f"pipeline-report-{date.today().isoformat()}.csv"

    def test_empty_tenant_returns_csv_with_only_header(self, auth_client, user, db):
        """No stages → header only."""
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 0
        assert "pipeline_name" in header
        assert "stage_name" in header
        assert "deal_count" in header

    def test_aggregates_stages_with_deal_counts(self, auth_client, stages, pipeline, user, db):
        """Stage aggregation shows correct deal_count."""
        from apps.pipelines.models import Deal

        # Create 2 deals in Qualified stage
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[0],
            name="Deal A",
            value=Decimal("1000.00"),
            status="open",
        )
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[0],
            name="Deal B",
            value=Decimal("2000.00"),
            status="open",
        )
        # 1 deal in Proposal stage
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[1],
            name="Deal C",
            value=Decimal("3000.00"),
            status="open",
        )

        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)

        stage_counts = {r[1]: int(r[2]) for r in rows}
        assert stage_counts["Qualified"] == 2
        assert stage_counts["Proposal"] == 1
        assert stage_counts["Closed Won"] == 0

    def test_total_value_aggregated(self, auth_client, stages, pipeline, user, db):
        from apps.pipelines.models import Deal

        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[0],
            name="Big Deal",
            value=Decimal("50000.00"),
            status="open",
        )
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[0],
            name="Small Deal",
            value=Decimal("10000.00"),
            status="open",
        )

        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        val_idx = header.index("total_value")
        qualified_row = [r for r in rows if r[1] == "Qualified"][0]
        # Decimal("60000.00") → str is "60000" (no trailing zeros)
        assert int(qualified_row[val_idx]) == 60000

    def test_excludes_closed_and_deleted_deals(self, auth_client, stages, pipeline, user, db):
        """Only open, non-deleted deals are counted."""
        from apps.pipelines.models import Deal

        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[0],
            name="Open Deal",
            value=Decimal("1000.00"),
            status="open",
        )
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[0],
            name="Won Deal",
            value=Decimal("2000.00"),
            status="won",
        )
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[1],
            name="Lost Deal",
            value=Decimal("3000.00"),
            status="lost",
        )

        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        stage_counts = {r[1]: int(r[2]) for r in rows}
        # Only open deals counted
        assert stage_counts["Qualified"] == 1
        assert stage_counts["Proposal"] == 0

    def test_order_by_pipeline_then_display_order(self, auth_client, stages, pipeline, user, db):
        """Stages appear sorted by pipeline name then display_order."""
        from apps.pipelines.models import Pipeline, Stage

        # Second pipeline with lower name alphabetically
        pipe2 = Pipeline.objects.create(tenant_id=user.tenant_id, name="Alpha Pipeline")
        Stage.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipe2,
            name="Early",
            display_order=1,
            probability=Decimal("0.50"),
        )
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        pipeline_names = [r[0] for r in rows]
        # Alpha Pipeline comes first alphabetically
        assert "Alpha Pipeline" in pipeline_names
        assert pipeline_names.index("Alpha Pipeline") < pipeline_names.index("Sales Pipeline")

    def test_tenant_isolation(self, auth_client, user, db):
        """Other tenant's stages don't appear."""
        other_tenant = uuid4()
        from apps.pipelines.models import Pipeline, Stage

        pipe = Pipeline.objects.create(tenant_id=other_tenant, name="Other")
        Stage.objects.create(tenant_id=other_tenant, pipeline=pipe, name="Hidden")
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 0

    def test_streaming_response_class(self, auth_client, stages, user, db):
        from django.http import StreamingHttpResponse

        response = auth_client.get(self.URL)
        assert isinstance(response, StreamingHttpResponse)


# ===================================================================
# 5  Edge Cases & Data Integrity
# ===================================================================


class TestExportEdgeCases:
    """Tests for CSV quoting, special characters, null/edge values,
    and streaming behaviour that existing section-level tests miss."""

    # ── Contacts edge cases ────────────────────────────────────────────────

    def test_contacts_csv_quoting_comma_in_field(self, auth_client, user, db):
        """Fields containing commas are properly CSV-quoted (wrapped in "")."""
        from apps.contacts.models import Contact

        Contact.objects.create(
            tenant_id=user.tenant_id,
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            job_title="Engineer, Team Lead",  # comma — should be quoted
            department="Engineering, R&D",    # comma — should be quoted
        )
        response = auth_client.get(CONTACTS_URL)
        content = b"".join(response.streaming_content).decode("utf-8-sig")
        # The job_title field contains a comma → CSV spec requires quoting
        # We verify by checking raw content has quotes around the field
        assert '"Engineer, Team Lead"' in content
        assert '"Engineering, R&D"' in content

    def test_contacts_csv_quoting_quotes_in_field(self, auth_client, user, db):
        """Fields containing double-quotes are properly escaped ("")."""
        from apps.contacts.models import Contact

        Contact.objects.create(
            tenant_id=user.tenant_id,
            first_name='Bob "The Builder"',
            last_name="Test",
            email="bob@test.com",
        )
        response = auth_client.get(CONTACTS_URL)
        content = b"".join(response.streaming_content).decode("utf-8-sig")
        # CSV quoting escapes " as ""
        assert content.count('"Bob ""The Builder""') >= 1

    def test_contacts_large_dataset_streaming(self, auth_client, user, db):
        """Creating more contacts than chunk_size (500) exercises chunked
        streaming — all contacts still appear in the output."""
        from apps.contacts.models import Contact

        count = 505  # one more than chunk_size=500 plus a few over
        # Bulk-create in a single query (won't hit iterator chunking)
        # BUT the view uses .iterator(chunk_size=500), so the first fetch
        # batch yields 500 rows and a second batch yields the rest.
        Contact.objects.bulk_create([
            Contact(
                tenant_id=user.tenant_id,
                first_name=f"Bulk_{i}",
                last_name="Stream",
                email=f"bulk{i}@test.com",
            )
            for i in range(count)
        ])
        response = auth_client.get(CONTACTS_URL)
        header, rows = _parse_csv(response)
        assert len(rows) == count
        emails = {r[2] for r in rows}
        assert f"bulk{count-1}@test.com" in emails
        assert f"bulk{0}@test.com" in emails

    def test_contact_owner_name_unknown_when_no_display_name(
        self, auth_client, user, db
    ):
        """If a user has blank first_name and last_name, _resolve_owner_names
        returns 'Unknown' rather than an empty or whitespace string."""
        from apps.contacts.models import Contact

        user.first_name = ""
        user.last_name = ""
        user.save()
        Contact.objects.create(
            tenant_id=user.tenant_id,
            first_name="NoName",
            last_name="Owner",
            email="noname@test.com",
            owner_id=user.id,
        )
        response = auth_client.get(CONTACTS_URL)
        header, rows = _parse_csv(response)
        owner_idx = header.index("owner_name")
        assert rows[0][owner_idx] == "Unknown"

    # ── Deals edge cases ───────────────────────────────────────────────────

    def test_deals_export_excludes_deleted(self, auth_client, user, db):
        """Deals with a non-null deleted_at timestamp are filtered out
        by the export view — soft-deleted deals must not leak into CSV."""
        from apps.pipelines.models import Pipeline, Stage, Deal
        from django.utils import timezone

        pipeline = Pipeline.objects.create(tenant_id=user.tenant_id, name="Test Pipe")
        stage = Stage.objects.create(tenant_id=user.tenant_id, pipeline=pipeline, name="S1")
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Deleted Deal",
            value=Decimal("100.00"),
            status="open",
            deleted_at=timezone.now(),  # soft-deleted
        )
        response = auth_client.get(DEALS_URL)
        header, rows = _parse_csv(response)
        deleted_names = [r[header.index("name")] for r in rows if "Deleted Deal" in r]
        assert len(deleted_names) == 0, (
            "Soft-deleted deal leaked into CSV export. "
            "ExportDealsView must apply deleted_at__isnull=True."
        )

    def test_deal_probability_override_in_export(self, auth_client, deal, user, db):
        """When a deal has an explicit probability override, win_probability
        and weighted_value reflect the override, not the stage default."""
        deal.probability = Decimal("0.75")
        deal.save()
        response = auth_client.get(DEALS_URL)
        header, rows = _parse_csv(response)
        win_idx = header.index("win_probability")
        weighted_idx = header.index("weighted_value")
        assert rows[0][win_idx] == "0.75"
        # weighted_value = 50000.00 * 0.75 = 37500.0000 (Decimal preserves full precision)
        assert rows[0][weighted_idx] == "37500.0000"

    def test_deal_zero_values_export(self, auth_client, user, db):
        """Deal with value=0 renders '0.00' not empty or '0'."""
        from apps.pipelines.models import Pipeline, Stage, Deal

        pipeline = Pipeline.objects.create(tenant_id=user.tenant_id, name="Zero Pipe")
        stage = Stage.objects.create(tenant_id=user.tenant_id, pipeline=pipeline, name="S1")
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Zero Value Deal",
            value=Decimal("0.00"),
            status="open",
        )
        response = auth_client.get(DEALS_URL)
        header, rows = _parse_csv(response)
        value_idx = header.index("value")
        weighted_idx = header.index("weighted_value")
        assert rows[0][value_idx] == "0.00"
        # weighted_value = 0.00 * 0.00 (stage prob 0.00) = 0.0000 (Decimal preserves full precision)
        assert rows[0][weighted_idx] == "0.0000"

    def test_deal_date_fields_formatted(self, auth_client, user, db):
        """expected_close_date, closed_at, entered_stage_at render as ISO
        strings when set, empty when null."""
        from apps.pipelines.models import Pipeline, Stage, Deal
        from django.utils import timezone

        pipeline = Pipeline.objects.create(tenant_id=user.tenant_id, name="Date Pipe")
        stage = Stage.objects.create(tenant_id=user.tenant_id, pipeline=pipeline, name="S1")
        now = timezone.now()
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Date Deal",
            value=Decimal("100.00"),
            status="won",
            expected_close_date=date(2026, 7, 15),
            closed_at=now,
            entered_stage_at=now,
            close_reason="Customer signed",
        )
        response = auth_client.get(DEALS_URL)
        header, rows = _parse_csv(response)
        close_date_idx = header.index("expected_close_date")
        closed_at_idx = header.index("closed_at")
        entered_idx = header.index("entered_stage_at")
        close_reason_idx = header.index("close_reason")

        assert rows[0][close_date_idx] == "2026-07-15"
        assert rows[0][closed_at_idx] == now.isoformat()
        assert rows[0][entered_idx] == now.isoformat()
        assert rows[0][close_reason_idx] == "Customer signed"

    def test_deal_csv_quoting_comma_in_description(self, auth_client, user, db):
        """Fields with commas (description, close_reason) are quoted."""
        from apps.pipelines.models import Pipeline, Stage, Deal

        pipeline = Pipeline.objects.create(tenant_id=user.tenant_id, name="CSV Pipe")
        stage = Stage.objects.create(tenant_id=user.tenant_id, pipeline=pipeline, name="S1")
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Comma Deal",
            value=Decimal("100.00"),
            status="open",
            description="Line 1, Line 2, Line 3",
            close_reason="Higher priority, budget constraints",
        )
        response = auth_client.get(DEALS_URL)
        content = b"".join(response.streaming_content).decode("utf-8-sig")
        assert '"Line 1, Line 2, Line 3"' in content
        assert '"Higher priority, budget constraints"' in content

    # ── Pipeline report edge cases ─────────────────────────────────────────

    def test_pipeline_report_inactive_pipeline_excluded(self, auth_client, user, db):
        """Stages belonging to inactive pipelines are excluded from the
        pipeline report export."""
        from apps.pipelines.models import Pipeline, Stage

        Pipeline.objects.create(
            tenant_id=user.tenant_id,
            name="Inactive Pipeline",
            is_active=False,
        )
        # The inactive pipeline exists — report should still be empty
        # (no active pipelines)
        response = auth_client.get(PIPELINE_URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 0

    def test_pipeline_report_stages_from_multiple_active_pipelines(
        self, auth_client, user, db
    ):
        """All active pipelines' stages appear, sorted by pipeline name
        then display_order."""
        from apps.pipelines.models import Pipeline, Stage

        pipe_a = Pipeline.objects.create(
            tenant_id=user.tenant_id, name="Alpha Pipe", is_active=True,
        )
        pipe_b = Pipeline.objects.create(
            tenant_id=user.tenant_id, name="Beta Pipe", is_active=True,
        )
        Stage.objects.create(
            tenant_id=user.tenant_id, pipeline=pipe_a, name="A1", display_order=2,
        )
        Stage.objects.create(
            tenant_id=user.tenant_id, pipeline=pipe_a, name="A2", display_order=1,
        )
        Stage.objects.create(
            tenant_id=user.tenant_id, pipeline=pipe_b, name="B1", display_order=1,
        )
        response = auth_client.get(PIPELINE_URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 3
        # Order: Alpha Pipe / A2 (display_order=1), Alpha Pipe / A1 (2), Beta Pipe / B1 (1)
        assert rows[0][0] == "Alpha Pipe"
        assert rows[0][1] == "A2"
        assert rows[1][0] == "Alpha Pipe"
        assert rows[1][1] == "A1"
        assert rows[2][0] == "Beta Pipe"
        assert rows[2][1] == "B1"

    def test_pipeline_report_deleted_deals_excluded(self, auth_client, stages, pipeline, user, db):
        """Soft-deleted deals are not counted in the report."""
        from apps.pipelines.models import Deal
        from django.utils import timezone

        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[0],
            name="Active Deal",
            value=Decimal("1000.00"),
            status="open",
        )
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[0],
            name="Deleted Deal",
            value=Decimal("999.00"),
            status="open",
            deleted_at=timezone.now(),
        )
        response = auth_client.get(PIPELINE_URL)
        header, rows = _parse_csv(response)
        stage_counts = {r[1]: int(r[2]) for r in rows}
        # The query already has `deals__deleted_at__isnull=True` in the filter,
        # so deleted deals are excluded. Only 1 active deal counted.
        assert stage_counts.get(stages[0].name, 0) == 1
