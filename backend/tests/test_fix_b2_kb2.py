"""Tests for Phase 4 audit fixes B2 + KB2.

B2  — _compute_what_if: Stage lookup now filters by pipeline__tenant_id
      to prevent cross-tenant stage leaks in what-if scenarios.
KB2 — _duration_to_days() helper: normalises DurationField aggregation
      values across PostgreSQL (microseconds) and SQLite (seconds)
      to actual days, used in avg_days_to_close and deal_velocity.

Before the fix, _compute_what_if did:
    Stage.objects.filter(name__iexact=scenario_stage_name).first()
… which could return a stage from another tenant's pipeline, silently
using the wrong stage probability.  Now it passes tenant_id:

    Stage.objects.filter(
        name__iexact=scenario_stage_name,
        pipeline__tenant_id=tenant_id,
    ).first()

Before KB2, avg_days_to_close and deal_velocity assumed PostgreSQL's
microsecond DurationField values, producing wildly wrong numbers on
SQLite (which returns seconds).  _duration_to_days() detects the
magnitude and normalises.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone

FORECAST_URL = "/api/reports/forecast/"
DASHBOARD_URL = "/api/reports/dashboard/"


# ── Factory helpers ───────────────────────────────────────────────────


def _pipeline(tenant_id, name="Sales Pipeline", **kw):
    from apps.pipelines.models import Pipeline

    return Pipeline.objects.create(tenant_id=tenant_id, name=name, **kw)


def _stage(tenant_id, pipeline, name="Qualified", **kw):
    from apps.pipelines.models import Stage
    from decimal import Decimal

    defaults = dict(display_order=1, probability=Decimal("0.50"))
    defaults.update(kw)
    return Stage.objects.create(
        tenant_id=tenant_id, pipeline=pipeline, name=name, **defaults
    )


def _deal(tenant_id, pipeline, stage, **kw):
    from apps.pipelines.models import Deal
    from decimal import Decimal

    defaults = dict(name="Test Deal", value=Decimal("10000.00"), status="open")
    defaults.update(kw)
    return Deal.objects.create(
        tenant_id=tenant_id, pipeline=pipeline, stage=stage, **defaults
    )


@pytest.fixture
def pipeline_fixture(user, db):
    """Full pipeline with 3 stages."""
    p = _pipeline(user.tenant_id, is_default=True)
    s1 = _stage(user.tenant_id, p, name="Qualified", display_order=1, probability=Decimal("0.25"))
    s2 = _stage(user.tenant_id, p, name="Proposal", display_order=2, probability=Decimal("0.60"))
    s3 = _stage(user.tenant_id, p, name="Closed Won", display_order=3, probability=Decimal("1.00"))
    return p, [s1, s2, s3]


# ===================================================================
# KB2 — _duration_to_days() unit tests
# ===================================================================


class TestDurationToDays:
    """Direct unit tests for the _duration_to_days helper.

    This function is not part of the public API — we test it via the
    dashboard view (which calls it through _compute_summary and
    _compute_deal_velocity), plus direct import for the math.
    """

    def _import_helper(self):
        from apps.reports.views import _duration_to_days

        return _duration_to_days

    def test_none_returns_zero(self):
        fn = self._import_helper()
        assert fn(None) == 0.0

    def test_zero_returns_zero(self):
        fn = self._import_helper()
        assert fn(0) == 0.0
        assert fn(0.0) == 0.0

    def test_pg_microseconds_converts_to_days(self):
        """PostgreSQL returns DurationField aggregates in microseconds.
        3 days = 3 * 24 * 3600 * 1_000_000 = 259_200_000_000 µs.
        """
        fn = self._import_helper()
        three_days_us = 259_200_000_000.0  # 3 days in microseconds
        result = fn(three_days_us)
        assert result == pytest.approx(3.0, abs=0.001)

    def test_sqlite_seconds_converts_to_days(self):
        """SQLite returns DurationField aggregates in seconds.
        3 days = 3 * 24 * 3600 = 259_200 s.
        """
        fn = self._import_helper()
        three_days_s = 259_200.0  # 3 days in seconds
        result = fn(three_days_s)
        assert result == pytest.approx(3.0, abs=0.001)

    def test_pg_milliseconds_converts_to_days(self):
        """Verify the 1e9 threshold: microseconds (>1e9) vs seconds (<1e9).
        Use 0.5 days as a test: 12 hours = 43_200 s (SQLite) vs 43_200_000_000 µs (PG).
        """
        fn = self._import_helper()
        half_day_us = 43_200_000_000.0  # 0.5 days in microseconds
        half_day_s = 43_200.0  # 0.5 days in seconds
        assert fn(half_day_us) == pytest.approx(0.5, abs=0.001)
        assert fn(half_day_s) == pytest.approx(0.5, abs=0.001)

    def test_large_value_above_1e9_boundary(self):
        """Values > 1e9 (microseconds) are divided by 86_400_000_000.
        Values < 1e9 (seconds) are divided by 86_400.
        """
        fn = self._import_helper()
        # A specific value just above the 1e9 boundary that represents
        # ~14.8 days in microseconds
        fourteen_days_us = 1_244_160_000_000.0  # ~14.4 days in microseconds
        result_us = fn(fourteen_days_us)
        assert result_us == pytest.approx(14.4, abs=0.1)

        # Same duration in seconds = 1_244_160
        fourteen_days_s = 1_244_160.0
        result_s = fn(fourteen_days_s)
        assert result_s == pytest.approx(14.4, abs=0.1)

    def test_negative_values(self):
        """Negative durations should also convert correctly (e.g., for a
        deal closed before it was created — shouldn't happen in practice,
        but the function shouldn't crash).
        """
        fn = self._import_helper()
        neg_us = -86_400_000_000.0  # -1 day in microseconds
        result = fn(neg_us)
        assert result == pytest.approx(-1.0, abs=0.001)

    def test_pg_edge_case_one_day(self):
        """Exactly 1 day in PostgreSQL microseconds."""
        fn = self._import_helper()
        one_day_us = 86_400_000_000.0
        result = fn(one_day_us)
        assert result == pytest.approx(1.0, abs=0.001)

    def test_sqlite_edge_case_one_day(self):
        """Exactly 1 day in SQLite seconds."""
        fn = self._import_helper()
        one_day_s = 86_400.0
        result = fn(one_day_s)
        assert result == pytest.approx(1.0, abs=0.001)

    def test_boundary_at_1e9_precise_us(self):
        """Value at exactly 1_000_000_000 — should be treated as SQLite seconds (boundary)."""
        fn = self._import_helper()
        # 1e9 µs = 1000 seconds ≈ 0.0116 days
        # Since abs(value) <= 1e9, it falls through to the SQLite-seconds branch
        boundary_s = 1_000_000_000.0  # 1e9 → treated as seconds
        result_s = fn(boundary_s)
        assert result_s == pytest.approx(11_574.074, abs=0.1), (
            f"1e9 as seconds should be ~11,574 days, got {result_s}"
        )

    def test_boundary_at_1e9_plus_one_us(self):
        """Value at 1_000_000_001 — should be treated as PG microseconds."""
        fn = self._import_helper()
        boundary_us = 1_000_000_001.0
        result_us = fn(boundary_us)
        assert result_us == pytest.approx(0.011574, abs=0.0001), (
            f"1e9+1 as µs should be ~0.0116 days, got {result_us}"
        )


# ===================================================================
# KB2 — _compute_summary edge cases (zero deals, empty querysets)
# ===================================================================


class TestSummaryEdgeCases:
    """_compute_summary must not crash with empty or edge-case querysets."""

    URL = DASHBOARD_URL

    def test_summary_with_zero_deals(self, auth_client, user, db):
        """No deals at all → summary returns zeroed metrics, not crashes."""
        resp = auth_client.get(
            self.URL,
            {"start_date": "2020-01-01", "end_date": "2020-12-31"},
        )
        assert resp.status_code == 200
        data = resp.json()
        s = data.get("summary", {})
        assert s.get("total_pipeline_value", -1) == 0
        assert s.get("weighted_pipeline", -1) == 0
        assert s.get("active_deals", -1) == 0
        assert s.get("avg_days_to_close", -1) == 0.0

    def test_summary_avg_days_to_close_no_closed_deals(self, auth_client, user, db):
        """Open deals only, no closed/won deals → avg_days_to_close = 0.0."""
        from apps.pipelines.models import Pipeline, Stage, Deal
        from decimal import Decimal

        pipe = Pipeline.objects.create(tenant_id=user.tenant_id, name="P")
        stage = Stage.objects.create(tenant_id=user.tenant_id, pipeline=pipe, name="S1")
        Deal.objects.create(
            tenant_id=user.tenant_id, pipeline=pipe, stage=stage,
            name="Open Deal", value=Decimal("1000.00"), status="open",
        )
        resp = auth_client.get(
            self.URL,
            {"start_date": "2020-01-01", "end_date": "2030-12-31"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["avg_days_to_close"] == 0.0

    def test_deal_velocity_empty_queryset(self, auth_client, user, db):
        """No deals → deal_velocity returns empty list, not crash."""
        resp = auth_client.get(
            self.URL,
            {"start_date": "2020-01-01", "end_date": "2020-12-31"},
        )
        assert resp.status_code == 200
        data = resp.json()
        velocity = data.get("deal_velocity", None)
        # Accept either empty list or None — both are non-crashing
        assert velocity is None or velocity == [], (
            f"deal_velocity should be empty when no deals exist, got {velocity}"
        )


# ===================================================================
# B2 — _compute_what_if edge cases
# ===================================================================


class TestWhatIfEdgeCases:
    """Boundary conditions for _compute_what_if."""

    FORECAST_URL = FORECAST_URL

    def test_what_if_zero_close_rate(self, auth_client, pipeline_fixture, user, db):
        """scenario_close_rate = 0 → what-if calculates zero upside."""
        pipeline, stages = pipeline_fixture
        from apps.pipelines.models import Deal, Stage
        from decimal import Decimal

        stage = Stage.objects.create(
            tenant_id=user.tenant_id, pipeline=pipeline,
            name="Qualified", display_order=1, probability=Decimal("0.25"),
        )
        Deal.objects.create(
            tenant_id=user.tenant_id, pipeline=pipeline, stage=stage,
            name="Zero Rate Deal", value=Decimal("10000.00"), status="open",
        )
        resp = auth_client.get(
            self.FORECAST_URL,
            {"scenario_stage": "Qualified", "scenario_close_rate": "0"},
        )
        assert resp.status_code == 200
        data = resp.json()
        wi = data.get("what_if")
        assert wi is not None, "what_if should be returned even with 0 close rate"
        assert wi["scenario_close_rate"] == 0.0
        # With rate 0, scenario value = 0, so upside is negative (current - 0)
        assert wi["upside"] <= 0

    def test_what_if_no_deals_in_stage(self, auth_client, pipeline_fixture, user, db):
        """Stage exists but has no deals → what_if returns zero-value projection."""
        pipeline, stages = pipeline_fixture
        from apps.pipelines.models import Stage
        from decimal import Decimal

        Stage.objects.create(
            tenant_id=user.tenant_id, pipeline=pipeline,
            name="Empty Stage", display_order=5, probability=Decimal("0.50"),
        )
        resp = auth_client.get(
            self.FORECAST_URL,
            {"scenario_stage": "Empty Stage", "scenario_close_rate": "0.75"},
        )
        assert resp.status_code == 200
        data = resp.json()
        wi = data.get("what_if")
        assert wi is not None, "what_if should be returned even with no deals in stage"
        assert wi["deals_affected"] == 0
# ===================================================================
# KB2 — Integration test via dashboard avg_days_to_close
# ===================================================================


class TestDurationToDaysIntegration:
    """Integration tests: avg_days_to_close uses _duration_to_days() via
    _compute_summary.  We create deals with known closed_at times and
    verify the average is in the right ballpark.
    """

    def test_avg_days_to_close_via_dashboard(self, auth_client, pipeline_fixture, user, db):
        """Create a deal opened 5 days ago and closed today → avg ~5 days."""
        pipeline, stages = pipeline_fixture
        from apps.pipelines.models import Deal
        from django.utils import timezone

        now = timezone.now()
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[2],  # Closed Won
            name="Fast Deal",
            value=Decimal("10000.00"),
            status="won",
            created_at=now - timedelta(days=5),
            closed_at=now,
        )
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stages[2],
            name="Slow Deal",
            value=Decimal("5000.00"),
            status="won",
            created_at=now - timedelta(days=15),
            closed_at=now,
        )

        resp = auth_client.get(
            DASHBOARD_URL,
            {"start_date": (now - timedelta(days=30)).date().isoformat(),
             "end_date": now.date().isoformat()},
        )
        assert resp.status_code == 200
        data = resp.json()
        avg = data["summary"]["avg_days_to_close"]
        # Average of 5 and 15 = 10 days (with small tolerance for time-of-day)
        assert avg == pytest.approx(10.0, abs=2.0), (
            f"avg_days_to_close should be ~10 days, got {avg}"
        )


# ===================================================================
# B2 — _compute_what_if cross-tenant isolation
# ===================================================================


class TestWhatIfCrossTenantIsolation:
    """B2: _compute_what_if must not return stages from other tenants.

    Previously it did:
        Stage.objects.filter(name__iexact=scenario_stage_name).first()

    If another tenant had a stage with the same name (e.g. "Negotiation"),
    the what-if would use THAT stage's probability — leaking data and
    producing wrong projections for the requesting tenant.
    """

    def test_what_if_does_not_find_stage_from_other_tenant(
        self, auth_client, pipeline_fixture, user, db
    ):
        """Other tenant has a "Negotiation" stage; requesting tenant does not.

        The what-if should return None because no stage named "Negotiation"
        exists in the requesting tenant's pipelines.
        """
        pipeline, _stages = pipeline_fixture

        # Arrange: create a "Negotiation" stage in a DIFFERENT tenant
        from apps.pipelines.models import Pipeline, Stage, Deal

        other_tenant_id = uuid4()
        other_pipe = Pipeline.objects.create(tenant_id=other_tenant_id, name="Other Pipe")
        Stage.objects.create(
            tenant_id=other_tenant_id,
            pipeline=other_pipe,
            name="Negotiation",
            display_order=1,
            probability=Decimal("0.80"),
        )

        # Act: requesting tenant (user's tenant) does NOT have "Negotiation"
        from apps.pipelines.models import Deal

        now = timezone.now()
        resp = auth_client.get(
            FORECAST_URL,
            {
                "scenario_stage": "Negotiation",
                "scenario_close_rate": "0.80",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # The what-if should be None — no "Negotiation" stage in this tenant
        assert data["what_if"] is None, (
            "B2 regression: _compute_what_if found a stage from another "
            "tenant's pipeline.  The fix (pipeline__tenant_id=tenant_id) "
            "should prevent cross-tenant stage leakage."
        )
        assert data["scenario"] is not None  # scenario metadata still sent
        assert data["scenario"]["stage_name"] == "Negotiation"

    def test_what_if_finds_matching_stage_in_same_tenant(
        self, auth_client, pipeline_fixture, user, db
    ):
        """Same tenant has a "Negotiation" stage → what-if should work."""
        pipeline, stages = pipeline_fixture

        # Add a "Negotiation" stage to this tenant's pipeline
        from apps.pipelines.models import Stage
        from decimal import Decimal

        neg = Stage.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            name="Negotiation",
            display_order=4,
            probability=Decimal("0.70"),
        )

        # Add a deal in Negotiation
        from apps.pipelines.models import Deal

        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=neg,
            name="Neg Deal",
            value=Decimal("50000.00"),
            status="open",
        )

        now = timezone.now()
        resp = auth_client.get(
            FORECAST_URL,
            {
                "scenario_stage": "Negotiation",
                "scenario_close_rate": "0.90",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        wi = data.get("what_if")
        assert wi is not None, "what_if should be populated for this tenant's own stage"
        assert wi["stage_name"] == "Negotiation"
        assert wi["deals_affected"] == 1
        assert wi["upside"] > 0

    def test_what_if_case_insensitive_matching_still_works(
        self, auth_client, pipeline_fixture, user, db
    ):
        """The stage name match is case-insensitive (name__iexact)."""
        pipeline, _stages = pipeline_fixture

        from apps.pipelines.models import Stage, Deal
        from decimal import Decimal

        stage = Stage.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            name="Proposal",
            display_order=2,
            probability=Decimal("0.60"),
        )
        Deal.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Prop Deal",
            value=Decimal("10000.00"),
            status="open",
        )

        # Use different casing than the stored name
        resp = auth_client.get(
            FORECAST_URL,
            {
                "scenario_stage": "proposal",
                "scenario_close_rate": "0.75",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        wi = data.get("what_if")
        assert wi is not None, "case-insensitive match should work"
        assert wi["stage_name"] == "Proposal"
