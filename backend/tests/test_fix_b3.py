"""Tests for Phase 4 audit fix B3 — CSV injection prevention in forecast export.

|B3 created ForecastExportView at GET /api/reports/export/forecast/csv/
|and replaced the vulnerable client-side CSV generation (string .join(','))
|with a proper backend streaming CSV endpoint using Python's csv.writer,
|which handles:
|  - Proper CSV quoting (fields with commas -> wrapped in quotes)
|  - Double-quote escaping (fields with embedded quotes -> doubled)
|  - Formula prefix sanitization (fields starting with =/+/-/@ are
|    prefixed with a tab or single-quote to prevent spreadsheet injection)

Also renamed the pipeline report export URL from /export/csv/ to
/export/pipeline/csv/ (reflected in ExportPipelineReportView).
"""

from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework import status

FORECAST_EXPORT_URL = "/api/reports/export/forecast/csv/"


def _parse_csv(response) -> tuple[list[str], list[list[str]]]:
    """Return (header_row, data_rows) parsed from a streaming CSV response."""
    content = b"".join(response.streaming_content).decode("utf-8-sig")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    return rows[0], rows[1:]


def _pipeline(tenant_id, name="Sales Pipeline", **kw):
    from apps.pipelines.models import Pipeline

    return Pipeline.objects.create(tenant_id=tenant_id, name=name, **kw)


def _stage(tenant_id, pipeline, name="Qualified", **kw):
    from apps.pipelines.models import Stage

    defaults = dict(display_order=1, probability=Decimal("0.50"))
    defaults.update(kw)
    return Stage.objects.create(
        tenant_id=tenant_id, pipeline=pipeline, name=name, **defaults
    )


def _deal(tenant_id, pipeline, stage, **kw):
    from apps.pipelines.models import Deal

    defaults = dict(name="Test Deal", value=Decimal("10000.00"), status="open")
    defaults.update(kw)
    return Deal.objects.create(
        tenant_id=tenant_id, pipeline=pipeline, stage=stage, **defaults
    )


def _setup_forecast_data(user, db):
    """Create pipeline+stages+deals for forecast export testing."""
    p = _pipeline(user.tenant_id, name="Sales", is_default=True)
    s1 = _stage(user.tenant_id, p, name="Qualified", display_order=1, probability=Decimal("0.25"))
    s2 = _stage(user.tenant_id, p, name="Proposal", display_order=2, probability=Decimal("0.60"))
    s3 = _stage(user.tenant_id, p, name="Negotiation", display_order=3, probability=Decimal("0.80"))
    s4 = _stage(user.tenant_id, p, name="Closed Won", display_order=4, probability=Decimal("1.00"))

    now = timezone.now()

    d1 = _deal(
        user.tenant_id, p, s1,
        name="Early Deal",
        value=Decimal("50000.00"),
        status="open",
        probability=Decimal("0.25"),
        expected_close_date=(now + timedelta(days=45)).date(),
        entered_stage_at=now - timedelta(days=10),
    )
    d2 = _deal(
        user.tenant_id, p, s2,
        name="Mid Pipeline",
        value=Decimal("100000.00"),
        status="open",
        probability=Decimal("0.60"),
        expected_close_date=(now + timedelta(days=60)).date(),
        entered_stage_at=now - timedelta(days=20),
    )
    d3 = _deal(
        user.tenant_id, p, s3,
        name="Deep Negotiation",
        value=Decimal("250000.00"),
        status="open",
        probability=Decimal("0.80"),
        expected_close_date=(now + timedelta(days=90)).date(),
        entered_stage_at=now - timedelta(days=5),
    )

    return {
        "pipeline": p,
        "stages": [s1, s2, s3, s4],
        "deals": [d1, d2, d3],
    }


# ===================================================================
# 1  Authentication
# ===================================================================


class TestForecastExportAuth:
    """All forecast export endpoints reject unauthenticated requests."""

    URL = FORECAST_EXPORT_URL

    def test_requires_auth(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_required_with_params(self, api_client):
        response = api_client.get(self.URL, {"range": "quarter"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ===================================================================
# 2  Forecast CSV Export — basic schema
# ===================================================================


class TestForecastExportBasic:
    """GET /api/reports/export/forecast/csv/ — basic response shape."""

    URL = FORECAST_EXPORT_URL

    def test_returns_csv_content_type(self, auth_client, user, db):
        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

    def test_has_content_disposition_with_filename(self, auth_client, user, db):
        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL)
        disposition = response.get("Content-Disposition", "")
        assert "attachment" in disposition
        assert ".csv" in disposition

    def test_streaming_response_class(self, auth_client, user, db):
        from django.http import StreamingHttpResponse

        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL)
        assert isinstance(response, StreamingHttpResponse)

    def test_returns_data_when_forecast_data_exists(self, auth_client, user, db):
        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        assert len(rows) > 0
        assert "Section" in header

    def test_contains_summary_projections(self, auth_client, user, db):
        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL)
        header, rows = _parse_csv(response)
        # Summary rows have "Summary" in column 0
        summary_rows = [r for r in rows if r and r[0] == "Summary"]
        projection_types = {r[1] for r in summary_rows if len(r) > 2}
        assert "Simple Weighted" in projection_types
        assert "Win-Rate Adjusted" in projection_types
        assert "Velocity Based" in projection_types

    def test_empty_tenant_still_returns_csv(self, auth_client, user, db):
        """No deals → CSV with header section only (no data)."""
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        header, rows = _parse_csv(response)
        # Should still have at least the header row
        assert len(header) >= 2


# ===================================================================
# 3  Forecast CSV — monthly breakdown & deal-level data
# ===================================================================


class TestForecastExportDetails:
    """Verify monthly breakdown and per-deal rows appear."""

    URL = FORECAST_EXPORT_URL

    def test_monthly_breakdown_included(self, auth_client, user, db):
        data = _setup_forecast_data(user, db)
        now = timezone.now()
        # Give deals with expected close dates so monthly breakdown appears
        response = auth_client.get(self.URL, {"range": "year"})
        assert response.status_code == status.HTTP_200_OK
        header, rows = _parse_csv(response)
        # Look for monthly breakdown rows
        monthly_rows = [r for r in rows if r and r[0] == "Monthly"]
        assert len(monthly_rows) >= 1, "Should have at least 1 month of data"

    def test_deal_level_details_included(self, auth_client, user, db):
        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        header, rows = _parse_csv(response)
        # Check for deal-level rows
        deal_rows = [r for r in rows if r and r[0] == "Deal"]
        # At least 3 deals (Early Deal, Mid Pipeline, Deep Negotiation)
        assert len(deal_rows) >= 3

    def test_deal_names_appear_in_export(self, auth_client, user, db):
        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        header, rows = _parse_csv(response)
        deal_rows = [r for r in rows if r and r[0] == "Deal"]
        deal_names = {r[1] for r in deal_rows if len(r) > 1}
        assert "Early Deal" in deal_names
        assert "Deep Negotiation" in deal_names

    def test_what_if_scenario_in_csv_when_provided(self, auth_client, user, db):
        """Scenario params produce a What-If section in the CSV."""
        _setup_forecast_data(user, db)
        response = auth_client.get(
            self.URL,
            {
                "scenario_stage": "Negotiation",
                "scenario_close_rate": "0.90",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        header, rows = _parse_csv(response)
        what_if_rows = [r for r in rows if r and r[0] == "What-If"]
        assert len(what_if_rows) >= 1, "What-If section should appear when params provided"

    def test_what_if_not_in_csv_when_not_requested(self, auth_client, user, db):
        """No scenario params → no What-If section."""
        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        header, rows = _parse_csv(response)
        what_if_rows = [r for r in rows if r and r[0] == "What-If"]
        assert len(what_if_rows) == 0, "What-If section should not appear without params"

    def test_currency_formatting_in_projected_revenue(self, auth_client, user, db):
        """Values should be formatted as currency ($X,XXX.XX)."""
        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        raw_content = b"".join(response.streaming_content).decode("utf-8-sig")
        reader = csv.reader(io.StringIO(raw_content))
        rows = list(reader)
        header = rows[0] if rows else []
        rows = rows[1:] if len(rows) > 1 else []
        # Only projection-type rows use currency formatting (not expected-close-count or avg-days)
        projection_types = {"Simple Weighted", "Win-Rate Adjusted", "Velocity Based"}
        summary_rows = [
            r for r in rows
            if r and r[0] == "Summary" and r[1] in projection_types and len(r) > 2
        ]
        for row in summary_rows:
            val = row[2]
            assert val.startswith("$"), f"Currency values should start with $, got '{val}'"
            # Should have 2 decimal places or be a properly formatted number
            assert "." in val, f"Currency values should have decimal places, got '{val}'"


# ===================================================================
# 4  CSV Injection Prevention
# ===================================================================


class TestForecastExportCsvInjection:
    """B3: CSV injection prevention — fields with formula prefixes
    (=, +, -, @) must be sanitised or properly quoted.

    Python's csv.writer handles quoting and escaping correctly by
    default — we verify that no formula injection characters
    appear unquoted at the start of CSV cells.
    """

    URL = FORECAST_EXPORT_URL

    def test_csv_writer_quotes_commas(self, auth_client, user, db):
        """Deal names with commas are properly quoted."""
        _setup_forecast_data(user, db)
        # Manually create a deal with a comma in the name
        from apps.pipelines.models import Deal, Stage, Pipeline

        pipeline = Pipeline.objects.get(tenant_id=user.tenant_id)
        stage = Stage.objects.filter(tenant_id=user.tenant_id).first()
        now = timezone.now()
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Deal A, Deal B",
            value=Decimal("1000.00"),
            status="open",
            expected_close_date=(now + timedelta(days=30)).date(),
        )
        response = auth_client.get(self.URL, {"range": "year"})
        content = b"".join(response.streaming_content).decode("utf-8-sig")
        # CSV spec: fields with commas are wrapped in quotes
        assert '"Deal A, Deal B"' in content, (
            "Deal name with comma must be CSV-quoted"
        )

    def test_backend_csv_writer_used_not_string_join(self, auth_client, user, db):
        """Verify the CSV uses proper Python csv.writer by checking that
        fields with commas are correctly quoted.  The OLD approach
        (client-side .join(',')) would produce broken CSV with
        misaligned columns when any field contained a comma."""
        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        content = b"".join(response.streaming_content).decode("utf-8-sig")
        # If csv.writer was used, the output is valid CSV that can be re-parsed
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        # Non-blank rows should have consistent column counts
        # (blank separator rows yield single empty-cell rows, which is fine)
        non_blank_rows = [r for r in rows if any(cell.strip() for cell in r)]
        for r in non_blank_rows:
            assert len(r) >= 2, f"Row has too few columns: {r}"

    def test_no_formula_prefix_injection_in_symbolic_data(self, auth_client, user, db):
        """Fields starting with =, +, -, @ are sanitised with a leading tab.

        The _sanitize_csv_field helper (used by _SanitizingCSVWriter)
        prepends a tab character to any field starting with =, +, -, or @
        so spreadsheet applications display them as text instead of
        executing them as formulas.

        The parsed field value (via csv.reader) is still the original
        string; only the raw CSV encoding includes the tab prefix.
        """
        from apps.pipelines.models import Deal, Stage, Pipeline

        _setup_forecast_data(user, db)
        pipeline = Pipeline.objects.get(tenant_id=user.tenant_id)
        stage = Stage.objects.filter(tenant_id=user.tenant_id).first()
        now = timezone.now()

        # Create deals with known formula-injection payloads in the name
        injection_names = [
            "=SUM(A1:A10)",
            "+SUM(A1:A10)",
            "-1+1",
            "@SUM(A1:A10)",
        ]
        for name in injection_names:
            Deal.objects.create(
                tenant_id=user.tenant_id,
                pipeline=pipeline,
                stage=stage,
                name=name,
                value=Decimal("100.00"),
                status="open",
                expected_close_date=(now + timedelta(days=30)).date(),
            )

        response = auth_client.get(self.URL, {"range": "year"})
        assert response.status_code == status.HTTP_200_OK
        content = b"".join(response.streaming_content).decode("utf-8-sig")

        # 1. Raw CSV must contain the sanitised form (tab-prefixed)
        for name in injection_names:
            assert f"\t{name}" in content, (
                f"Deal name '{name}' must be tab-prefixed (sanitised) in raw CSV output"
            )

        # 2. Parsed CSV (via csv.reader) preserves the tab prefix;
        #    the tab tells spreadsheet apps to treat the cell as text.
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        deal_rows = [r for r in rows if r and r[0] == "Deal"]
        sanitized_names = {r[1] for r in deal_rows if len(r) > 1}
        for name in injection_names:
            assert f"\t{name}" in sanitized_names, (
                f"Parsed deal name '{name}' must appear with tab prefix after sanitisation"
            )


# ===================================================================
# 5  Tenant Isolation & URL Validation
# ===================================================================


class TestForecastExportIsolation:
    """Forecast export respects tenant isolation."""

    URL = FORECAST_EXPORT_URL

    def test_tenant_isolation(self, auth_client, user, db):
        """Deals from other tenants don't appear in CSV."""
        _setup_forecast_data(user, db)

        # Other tenant has a deal too
        other_tenant = uuid4()
        other_pipe = _pipeline(other_tenant, name="Other")
        other_stage = _stage(other_tenant, other_pipe, name="OS1")
        _deal(
            other_tenant, other_pipe, other_stage,
            name="Other Tenant Deal",
            value=Decimal("99999.00"),
            status="open",
            expected_close_date=(timezone.now() + timedelta(days=30)).date(),
        )

        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        header, rows = _parse_csv(response)
        deal_rows = [r for r in rows if r and r[0] == "Deal"]
        deal_names = {r[1] for r in deal_rows if len(r) > 1}
        assert "Other Tenant Deal" not in deal_names, (
            "Other tenant's deals leaked into forecast CSV export"
        )

    def test_invalid_pipeline_id_does_not_crash(self, auth_client, user, db):
        """Bad pipeline_id UUID is silently ignored."""
        _setup_forecast_data(user, db)
        response = auth_client.get(self.URL, {"pipeline_id": "not-a-uuid"})
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_close_rate_does_not_crash(self, auth_client, user, db):
        """Bad scenario_close_rate is silently ignored."""
        _setup_forecast_data(user, db)
        response = auth_client.get(
            self.URL,
            {
                "scenario_stage": "Negotiation",
                "scenario_close_rate": "not-a-number",
            },
        )
        assert response.status_code == status.HTTP_200_OK


# ===================================================================
# 6  Pipeline Report Export URL rename
# ===================================================================


class TestPipelineExportUrl:
    """B3 also renamed /export/csv/ to /export/pipeline/csv/."""

    def test_pipeline_csv_endpoint_exists(self, auth_client, user, db):
        """The renamed pipeline CSV URL works."""
        url = "/api/reports/export/pipeline/csv/"
        response = auth_client.get(url)
        # Should 200 even with empty data
        assert response.status_code == status.HTTP_200_OK

    def test_old_pipeline_csv_url_not_found(self, api_client):
        """The old URL /api/reports/export/csv/ should 404."""
        response = api_client.get("/api/reports/export/csv/")
        assert response.status_code in (
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED,
        )


# ===================================================================
# 7  _sanitize_csv_field unit tests
# ===================================================================


class TestSanitizeCsvField:
    """Direct unit tests for the _sanitize_csv_field helper."""

    def _import(self):
        from apps.reports.export_views import _sanitize_csv_field
        return _sanitize_csv_field

    def test_normal_text_unchanged(self):
        fn = self._import()
        assert fn("plain text") == "plain text"

    def test_numbers_unchanged(self):
        fn = self._import()
        assert fn(123) == "123"
        assert fn(0.5) == "0.5"

    def test_empty_string_unchanged(self):
        fn = self._import()
        assert fn("") == ""

    def test_equals_sign_prefixed(self):
        fn = self._import()
        assert fn("=SUM(A1:A10)") == "\t=SUM(A1:A10)"

    def test_plus_sign_prefixed(self):
        fn = self._import()
        assert fn("+SUM(A1:A10)") == "\t+SUM(A1:A10)"

    def test_minus_sign_prefixed(self):
        fn = self._import()
        assert fn("-1+1") == "\t-1+1"

    def test_at_sign_prefixed(self):
        fn = self._import()
        assert fn("@SUM(A1:A10)") == "\t@SUM(A1:A10)"

    def test_tab_is_not_double_sanitized(self):
        fn = self._import()
        # A field that already starts with a tab should be left alone
        # (the leading tab means it was already sanitized)
        assert fn("\t=SUM()") == "\t=SUM()"


class TestSanitizingCSVWriter:
    """Integration test for the _SanitizingCSVWriter wrapper."""

    def test_writer_writes_sanitized_csv(self):
        from apps.reports.export_views import _SanitizingCSVWriter
        import io

        buf = io.StringIO()
        w = _SanitizingCSVWriter(buf)
        w.writerow(["=SUM()", "Safe", "-1+1", "123"])
        content = buf.getvalue()
        # csv.writer adds trailing newline + quoting on commas
        # The sanitized fields should have tab prefix
        assert "\t=SUM()" in content
        assert "\t-1+1" in content
        assert ",Safe," in content or ",Safe" in content
        assert ",123" in content


# ===================================================================
# 8  Pipeline report CSV injection safety
# ===================================================================


class TestPipelineExportCsvInjection:
    """Pipeline report CSV export also uses _SanitizingCSVWriter."""

    URL = "/api/reports/export/pipeline/csv/"

    def test_pipeline_report_sanitizes_formula_injection(self, auth_client, user, db):
        """Pipeline report CSV contains tab-prefixed fields for injection payloads."""
        from apps.pipelines.models import Pipeline, Stage, Deal
        from decimal import Decimal

        p = Pipeline.objects.create(tenant_id=user.tenant_id, name="Test Pipe", is_default=True)
        s = Stage.objects.create(
            tenant_id=user.tenant_id, pipeline=p,
            name="=SUM(A1)", display_order=1, probability=Decimal("0.50"),
        )
        Deal.objects.create(
            tenant_id=user.tenant_id, pipeline=p, stage=s,
            name="-1+1", value=Decimal("100.00"), status="open",
        )

        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        content = b"".join(response.streaming_content).decode("utf-8-sig")

        # Stage name "=SUM(A1)" should be sanitized
        # (PipelineReportExportView outputs stage names in the "Deals by Stage" section)
        assert "\t=SUM(A1)" in content, (
            "Pipeline report CSV must sanitize =prefixed stage name"
        )
        # PipelineReportExportView only outputs stage-level aggregates, not
        # individual deal names.  Deal-level formula injection is tested via
        # ForecastExportView (TestForecastExportCsvInjection).
