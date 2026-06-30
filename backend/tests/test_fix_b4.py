"""Tests for Phase 4 audit fix B4 — Deleted deals filter + duplicate hooks.

B4 added deleted_at__isnull=True to ExportDealsView queryset, preventing
soft-deleted deals from leaking into CSV exports.  Previously the view
only filtered by tenant_id.  The ExportContactsView already had this
filter, so the fix brings the deals export in line.

Also removed the unused duplicate hook at frontend/src/api/export.ts
(which was a copy of hooks/useExportCsv.ts) and its orphaned consumers.

The existing test test_deals_export_excludes_deleted was flipped from
asserting the bug was present to asserting it's fixed.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import csv
import io
import pytest
from django.utils import timezone
from rest_framework import status

DEALS_URL = "/api/export/deals/"
CONTACTS_URL = "/api/export/contacts/"


def _parse_csv(response) -> tuple[list[str], list[list[str]]]:
    content = b"".join(response.streaming_content).decode("utf-8-sig")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    return rows[0], rows[1:]


# ===================================================================
# 1  Backend: Deleted deals filter enforcement
# ===================================================================


class TestDealsExportDeletedFilter:
    """B4: ExportDealsView must apply deleted_at__isnull=True."""

    URL = DEALS_URL

    def test_active_deals_appear_normally(self, auth_client, user, db):
        """Non-deleted deals still appear in the export."""
        from apps.pipelines.models import Pipeline, Stage, Deal

        pipeline = Pipeline.objects.create(
            tenant_id=user.tenant_id, name="Active Pipe"
        )
        stage = Stage.objects.create(
            tenant_id=user.tenant_id, pipeline=pipeline, name="Active Stage"
        )
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Active Deal",
            value=Decimal("5000.00"),
            status="open",
        )
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        names = [r[header.index("name")] for r in rows]
        assert "Active Deal" in names

    def test_soft_deleted_deal_excluded_from_export(self, auth_client, user, db):
        """Soft-deleted deals (non-null deleted_at) are excluded."""
        from apps.pipelines.models import Pipeline, Stage, Deal

        pipeline = Pipeline.objects.create(
            tenant_id=user.tenant_id, name="Test Pipe"
        )
        stage = Stage.objects.create(
            tenant_id=user.tenant_id, pipeline=pipeline, name="S1"
        )
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Deleted Deal",
            value=Decimal("100.00"),
            status="open",
            deleted_at=timezone.now(),
        )
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        names = [r[header.index("name")] for r in rows]
        assert "Deleted Deal" not in names, (
            "B4 regression: soft-deleted deal leaked into CSV export. "
            "ExportDealsView must apply deleted_at__isnull=True."
        )

    def test_mixed_active_and_deleted_only_active_appear(self, auth_client, user, db):
        """When both active and deleted deals exist, only active appear."""
        from apps.pipelines.models import Pipeline, Stage, Deal

        pipeline = Pipeline.objects.create(
            tenant_id=user.tenant_id, name="Mixed Pipe"
        )
        stage = Stage.objects.create(
            tenant_id=user.tenant_id, pipeline=pipeline, name="S1"
        )

        now = timezone.now()
        # Active deal
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Remaining Deal",
            value=Decimal("200.00"),
            status="open",
        )
        # Deleted deal
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Removed Deal",
            value=Decimal("999.00"),
            status="open",
            deleted_at=now,
        )

        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        names = [r[header.index("name")] for r in rows]
        assert "Remaining Deal" in names, "Active deal must appear"
        assert "Removed Deal" not in names, "Deleted deal must not leak"

    def test_deleted_deal_with_other_tenant_filtering(self, auth_client, user, db):
        """Tenant isolation still works alongside deleted filter."""
        from apps.pipelines.models import Pipeline, Stage, Deal

        pipeline = Pipeline.objects.create(
            tenant_id=user.tenant_id, name="My Pipe"
        )
        stage = Stage.objects.create(
            tenant_id=user.tenant_id, pipeline=pipeline, name="S1"
        )
        now = timezone.now()

        # Active deal in own tenant
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="My Active Deal",
            value=Decimal("1000.00"),
            status="open",
        )
        # Deleted deal in own tenant
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="My Deleted Deal",
            value=Decimal("500.00"),
            status="open",
            deleted_at=now,
        )

        # Other tenant's active deal
        other_tenant = uuid4()
        other_pipe = Pipeline.objects.create(tenant_id=other_tenant, name="Other")
        other_stage = Stage.objects.create(
            tenant_id=other_tenant, pipeline=other_pipe, name="OS1"
        )
        Deal.objects.create(
            tenant_id=other_tenant,
            pipeline=other_pipe,
            stage=other_stage,
            name="Other Active",
            value=Decimal("999.00"),
            status="open",
        )

        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        names = [r[header.index("name")] for r in rows]
        assert "My Active Deal" in names
        assert "My Deleted Deal" not in names
        assert "Other Active" not in names

    def test_existing_export_deals_test_still_passes(self, auth_client, user, db):
        """The pre-existing test_deals_export_excludes_deleted in
        TestExportEdgeCases should still pass — this is a regression guard."""
        # Delegate to the existing test logic
        from apps.pipelines.models import Pipeline, Stage, Deal

        pipeline = Pipeline.objects.create(tenant_id=user.tenant_id, name="Regress Pipe")
        stage = Stage.objects.create(tenant_id=user.tenant_id, pipeline=pipeline, name="S1")
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Regression Check Deal",
            value=Decimal("100.00"),
            status="open",
            deleted_at=timezone.now(),
        )
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        deleted_names = [
            r[header.index("name")] for r in rows if "Regression Check Deal" in r
        ]
        assert len(deleted_names) == 0


# ===================================================================
# 2  Backend: Contacts export filter not regressed
# ===================================================================


class TestContactsExportDeletedFilter:
    """Contacts export already had deleted_at__isnull=True — verify it
    still works and wasn't affected by the B4 changes."""

    URL = CONTACTS_URL

    def test_active_contacts_still_appear(self, auth_client, user, db):
        from apps.contacts.models import Contact

        Contact.objects.create(
            tenant_id=user.tenant_id,
            first_name="Alice",
            last_name="Active",
            email="alice@test.com",
        )
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 1
        email_idx = header.index("email")
        assert rows[0][email_idx] == "alice@test.com"

    def test_soft_deleted_contact_excluded(self, auth_client, user, db):
        from apps.contacts.models import Contact

        Contact.objects.create(
            tenant_id=user.tenant_id,
            first_name="Bob",
            last_name="Gone",
            email="bob@test.com",
            deleted_at=timezone.now(),
        )
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) == 0


# ===================================================================
# 3  Frontend: Duplicate hook removed
# ===================================================================


class TestDuplicateHookRemoved:
    """B4 removed the unused duplicate hook at api/export.ts.

    The frontend already had an ExportButton component using
    hooks/useExportCsv.ts.  The api/export.ts (and its test)
    were duplicates that should not be imported anywhere.
    """

    def test_api_export_ts_replaced(self):
        """api/export.ts should contain only the removal notice."""
        import os

        path = "/Users/chriskilloran/FrontierCRM/frontend/src/api/export.ts"
        if os.path.exists(path):
            with open(path) as f:
                content = f.read().strip()
            # Should be a comment saying it's removed, not a real module
            assert "Removed" in content or "removed" in content, (
                "api/export.ts should contain only a removal notice, "
                "not a real module.  B4 replaced it with a comment."
            )
        else:
            # File was fully deleted — also acceptable
            pass

    def test_use_export_csv_hook_still_exists(self):
        """The canonical hook still exists at hooks/useExportCsv.ts."""
        import os

        path = "/Users/chriskilloran/FrontierCRM/frontend/src/hooks/useExportCsv.ts"
        assert os.path.exists(path), (
            "hooks/useExportCsv.ts must still exist — it's the canonical hook"
        )

    def test_export_button_uses_correct_hook(self):
        """ExportButton imports from hooks/useExportCsv, not api/export."""
        import os

        path = "/Users/chriskilloran/FrontierCRM/frontend/src/components/ui/export-button.tsx"
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert "hooks/useExportCsv" in content, (
            "ExportButton must import from hooks/useExportCsv"
        )
        assert "api/export" not in content, (
            "ExportButton should not import from api/export (duplicate hook)"
        )
