"""Comprehensive tests for pipeline, stage, and deal endpoints."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from django.utils import timezone

# ---------------------------------------------------------------------------
# Module-level URL constants
# ---------------------------------------------------------------------------

PIPELINES_URL = "/api/deals/pipelines/"
STAGES_URL = "/api/deals/stages/"
DEALS_URL = "/api/deals/deals/"


# ===================================================================
# Helpers
# ===================================================================


def _create_pipeline(tenant_id, name="Sales Pipeline", **kw):
    from apps.pipelines.models import Pipeline

    return Pipeline.objects.create(tenant_id=tenant_id, name=name, **kw)


def _create_stage(tenant_id, pipeline, name="Qualified", **kw):
    from apps.pipelines.models import Stage

    return Stage.objects.create(tenant_id=tenant_id, pipeline=pipeline, name=name, **kw)


def _create_deal(tenant_id, pipeline, stage, name="Test Deal", **kw):
    from apps.pipelines.models import Deal

    return Deal.objects.create(
        tenant_id=tenant_id,
        pipeline=pipeline,
        stage=stage,
        name=name,
        **kw,
    )


def _count_activities(tenant_id, entity_id):
    from apps.activities.models import Activity

    return Activity.objects.filter(tenant_id=tenant_id, entity_id=entity_id).count()


# ===================================================================
# Fixtures shared across deal tests
# ===================================================================


@pytest.fixture
def pipeline(user, db):
    pipe = _create_pipeline(user.tenant_id, is_default=True)
    _create_stage(user.tenant_id, pipe, name="Qualified", display_order=1, probability=Decimal("0.25"))
    _create_stage(user.tenant_id, pipe, name="Proposal", display_order=2, probability=Decimal("0.50"))
    _create_stage(user.tenant_id, pipe, name="Closed Won", display_order=3, probability=Decimal("1.00"))
    return pipe


@pytest.fixture
def deal(user, pipeline, db):
    """A basic open deal owned by the fixture user."""
    stage = pipeline.stages.first()
    return _create_deal(user.tenant_id, pipeline, stage, name="Fixture Deal")


# ===================================================================
# 1  Pipeline CRUD
# ===================================================================


class TestPipelineCRUD:
    """List, create, detail, update, delete + filters."""

    def test_list_pipelines(self, auth_client, user, pipeline):
        resp = auth_client.get(PIPELINES_URL)
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["results"]]
        assert str(pipeline.id) in ids

    def test_create_pipeline(self, auth_client, user):
        resp = auth_client.post(PIPELINES_URL, {"name": "New Pipeline"}, format="json")
        assert resp.status_code == 201
        assert resp.json()["name"] == "New Pipeline"
        assert resp.json()["tenant_id"] == str(user.tenant_id)

    def test_get_pipeline_detail(self, auth_client, pipeline):
        resp = auth_client.get(f"{PIPELINES_URL}{pipeline.id}/")
        assert resp.status_code == 200
        assert resp.json()["name"] == pipeline.name

    def test_update_pipeline(self, auth_client, pipeline):
        resp = auth_client.patch(
            f"{PIPELINES_URL}{pipeline.id}/",
            {"name": "Updated Pipeline"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Pipeline"

    def test_delete_pipeline(self, auth_client, pipeline):
        resp = auth_client.delete(f"{PIPELINES_URL}{pipeline.id}/")
        assert resp.status_code == 204
        # Pipeline is hard-deleted by ModelViewSet
        from apps.pipelines.models import Pipeline

        assert not Pipeline.objects.filter(id=pipeline.id).exists()

    def test_filter_pipeline_by_is_default(self, auth_client, user, pipeline):
        resp = auth_client.get(PIPELINES_URL, {"is_default": "true"})
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["results"]]
        assert str(pipeline.id) in ids

    def test_filter_pipeline_by_is_active(self, auth_client, user):
        p_active = _create_pipeline(user.tenant_id, "Active Pipe", is_active=True)
        _create_pipeline(user.tenant_id, "Inactive Pipe", is_active=False)
        resp = auth_client.get(PIPELINES_URL, {"is_active": "true"})
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["results"]]
        assert str(p_active.id) in ids


# ===================================================================
# 2  Stage CRUD
# ===================================================================


class TestStageCRUD:
    """List, create (with pipeline FK), detail, filter by pipeline."""

    def test_list_stages(self, auth_client, user, pipeline):
        resp = auth_client.get(STAGES_URL)
        assert resp.status_code == 200
        assert len(resp.json()["results"]) >= pipeline.stages.count()

    def test_create_stage(self, auth_client, user, pipeline):
        resp = auth_client.post(
            STAGES_URL,
            {"name": "New Stage", "pipeline": str(pipeline.id), "display_order": 5, "probability": "0.75"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "New Stage"
        assert resp.json()["probability"] == "0.75"

    def test_get_stage_detail(self, auth_client, pipeline):
        stage = pipeline.stages.first()
        resp = auth_client.get(f"{STAGES_URL}{stage.id}/")
        assert resp.status_code == 200
        assert resp.json()["name"] == stage.name

    def test_filter_stages_by_pipeline(self, auth_client, user, pipeline):
        other = _create_pipeline(user.tenant_id, "Other Pipeline")
        other_stage = _create_stage(user.tenant_id, other, name="Other Stage")
        resp = auth_client.get(STAGES_URL, {"pipeline": str(other.id)})
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()["results"]]
        assert str(other_stage.id) in ids
        for s in pipeline.stages.all():
            assert str(s.id) not in ids


# ===================================================================
# 3  Deal CRUD
# ===================================================================


class TestDealCRUD:
    """List, create (with pipeline + stage FK), detail, update, delete."""

    def test_list_deals(self, auth_client, deal):
        resp = auth_client.get(DEALS_URL)
        assert resp.status_code == 200
        ids = [d["id"] for d in resp.json()["results"]]
        assert str(deal.id) in ids

    def test_create_deal(self, auth_client, user, pipeline):
        stage = pipeline.stages.first()
        resp = auth_client.post(
            DEALS_URL,
            {
                "name": "Big Deal",
                "pipeline": str(pipeline.id),
                "stage": str(stage.id),
                "value": "50000.00",
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Big Deal"
        assert data["tenant_id"] == str(user.tenant_id)

    def test_get_deal_detail(self, auth_client, deal):
        resp = auth_client.get(f"{DEALS_URL}{deal.id}/")
        assert resp.status_code == 200
        assert resp.json()["name"] == deal.name

    def test_update_deal(self, auth_client, deal):
        resp = auth_client.patch(DEALS_URL + str(deal.id) + "/", {"name": "Updated Deal"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Deal"

    def test_delete_deal(self, auth_client, deal):
        resp = auth_client.delete(f"{DEALS_URL}{deal.id}/")
        assert resp.status_code == 204
        # Deal is hard-deleted by ModelViewSet
        from apps.pipelines.models import Deal

        assert not Deal.objects.filter(id=deal.id).exists()


# ===================================================================
# 4  Deal custom actions — move_stage
# ===================================================================


class TestDealMoveStage:
    """Move a deal through the pipeline."""

    def test_move_stage_success(self, auth_client, user, pipeline, deal):
        """Change stage and confirm probability updates + Activity created."""
        stage2 = pipeline.stages.last()
        act_before = _count_activities(user.tenant_id, deal.id)

        resp = auth_client.post(
            f"{DEALS_URL}{deal.id}/move_stage/",
            {"stage_id": str(stage2.id)},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["stage"] == str(stage2.id)
        assert resp.json()["stage_name"] == stage2.name

        # Probability follows the stage when there is no override
        assert Decimal(resp.json()["win_probability"]) == stage2.probability

        # An Activity was created
        assert _count_activities(user.tenant_id, deal.id) == act_before + 1

    def test_move_stage_updates_probability(self, auth_client, user, pipeline, deal):
        """Probability updates to reflect the new stage."""
        stage2 = pipeline.stages.last()
        resp = auth_client.post(
            f"{DEALS_URL}{deal.id}/move_stage/",
            {"stage_id": str(stage2.id)},
            format="json",
        )
        assert Decimal(resp.json()["win_probability"]) == stage2.probability


# ===================================================================
# 4 (cont.)  Deal custom actions — change_status
# ===================================================================


class TestDealChangeStatus:
    """Won / lost / abandoned status changes."""

    def test_change_status_won(self, auth_client, user, deal):
        """Won: status changes, closed_at set, Activity created."""
        assert deal.closed_at is None
        act_before = _count_activities(user.tenant_id, deal.id)

        resp = auth_client.post(
            f"{DEALS_URL}{deal.id}/change_status/",
            {"status": "won", "close_reason": "Happy customer"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "won"

        # closed_at should be set
        deal.refresh_from_db()
        assert deal.closed_at is not None
        assert deal.close_reason == "Happy customer"

        # Activity created
        assert _count_activities(user.tenant_id, deal.id) == act_before + 1

    def test_change_status_lost(self, auth_client, user, deal):
        """Lost: status changes, closed_at set, Activity created."""
        assert deal.closed_at is None
        resp = auth_client.post(
            f"{DEALS_URL}{deal.id}/change_status/",
            {"status": "lost", "close_reason": "Budget"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "lost"
        deal.refresh_from_db()
        assert deal.closed_at is not None

    def test_change_status_abandoned(self, auth_client, user, deal):
        """Abandoned: status changes, closed_at NOT set (only won/lost)."""
        resp = auth_client.post(
            f"{DEALS_URL}{deal.id}/change_status/",
            {"status": "abandoned", "close_reason": "No longer relevant"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "abandoned"
        deal.refresh_from_db()
        # Only won/lost set closed_at per the view implementation
        assert deal.closed_at is None
        assert deal.close_reason == ""

    def test_change_status_open(self, auth_client, user, deal):
        """Re-open: status goes back to open."""
        # First close as won
        auth_client.post(
            f"{DEALS_URL}{deal.id}/change_status/",
            {"status": "won"},
            format="json",
        )
        # Now re-open
        resp = auth_client.post(
            f"{DEALS_URL}{deal.id}/change_status/",
            {"status": "open"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "open"


# ===================================================================
# 5  Validation
# ===================================================================


class TestDealValidation:
    """400 / 404 for invalid actions."""

    def test_move_stage_missing_stage_id(self, auth_client, deal):
        resp = auth_client.post(
            f"{DEALS_URL}{deal.id}/move_stage/",
            {},
            format="json",
        )
        assert resp.status_code == 400
        assert "stage_id required" in resp.json().get("error", "").lower()

    def test_move_stage_invalid_stage(self, auth_client, deal):
        resp = auth_client.post(
            f"{DEALS_URL}{deal.id}/move_stage/",
            {"stage_id": str(uuid4())},
            format="json",
        )
        assert resp.status_code == 404
        assert "not found" in resp.json().get("error", "").lower()

    def test_move_stage_wrong_pipeline_stage(self, auth_client, user, pipeline, deal):
        """A stage from a different pipeline (same tenant) should 404."""
        other_pipe = _create_pipeline(user.tenant_id, "Other Pipe")
        other_stage = _create_stage(user.tenant_id, other_pipe, name="Other Stage")
        resp = auth_client.post(
            f"{DEALS_URL}{deal.id}/move_stage/",
            {"stage_id": str(other_stage.id)},
            format="json",
        )
        assert resp.status_code == 404

    def test_change_status_invalid_status(self, auth_client, deal):
        resp = auth_client.post(
            f"{DEALS_URL}{deal.id}/change_status/",
            {"status": "invalid_status"},
            format="json",
        )
        assert resp.status_code == 400
        assert "invalid status" in resp.json().get("error", "").lower()


# ===================================================================
# 6  Multi-tenant isolation
# ===================================================================


class TestMultiTenantIsolation:
    """Objects from other tenants are invisible."""

    def test_other_tenant_pipeline_invisible(self, auth_client, user):
        """Pipeline from another tenant does not appear in list or detail."""
        other_tid = uuid4()
        other_pipe = _create_pipeline(other_tid, "Other Tenant Pipeline")
        # List
        resp = auth_client.get(PIPELINES_URL)
        ids = [p["id"] for p in resp.json()["results"]]
        assert str(other_pipe.id) not in ids
        # Detail
        resp = auth_client.get(f"{PIPELINES_URL}{other_pipe.id}/")
        assert resp.status_code == 404

    def test_other_tenant_stage_invisible(self, auth_client, user):
        other_tid = uuid4()
        other_pipe = _create_pipeline(other_tid, "Other Pipe")
        other_stage = _create_stage(other_tid, other_pipe, name="Other Stage")
        resp = auth_client.get(STAGES_URL)
        ids = [s["id"] for s in resp.json()["results"]]
        assert str(other_stage.id) not in ids
        # Detail
        resp = auth_client.get(f"{STAGES_URL}{other_stage.id}/")
        assert resp.status_code == 404

    def test_other_tenant_deal_invisible(self, auth_client, user, pipeline):
        other_tid = uuid4()
        other_pipe = _create_pipeline(other_tid, "Other Pipe")
        other_stage = _create_stage(other_tid, other_pipe, name="Other Stage")
        other_deal = _create_deal(other_tid, other_pipe, other_stage, name="Other Deal")
        resp = auth_client.get(DEALS_URL)
        ids = [d["id"] for d in resp.json()["results"]]
        assert str(other_deal.id) not in ids
        # Detail
        resp = auth_client.get(f"{DEALS_URL}{other_deal.id}/")
        assert resp.status_code == 404


# ===================================================================
# 7  Cross-tenant: other tenant cannot move_stage or change_status
# ===================================================================


class TestCrossTenantActions:
    """Other tenant can't mutate our deals via custom actions."""

    def test_other_tenant_cannot_move_stage(self, auth_client, user, pipeline):
        """A deal owned by another tenant is invisible → 404 on custom action."""
        other_tid = uuid4()
        other_pipe = _create_pipeline(other_tid, "Other Pipe")
        other_stage = _create_stage(other_tid, other_pipe, name="Other Stage")
        other_deal = _create_deal(other_tid, other_pipe, other_stage, name="Other Deal")
        resp = auth_client.post(
            f"{DEALS_URL}{other_deal.id}/move_stage/",
            {"stage_id": str(other_stage.id)},
            format="json",
        )
        assert resp.status_code == 404

    def test_other_tenant_cannot_change_status(self, auth_client, user, pipeline):
        other_tid = uuid4()
        other_pipe = _create_pipeline(other_tid, "Other Pipe")
        other_stage = _create_stage(other_tid, other_pipe, name="Other Stage")
        other_deal = _create_deal(other_tid, other_pipe, other_stage, name="Other Deal")
        resp = auth_client.post(
            f"{DEALS_URL}{other_deal.id}/change_status/",
            {"status": "won"},
            format="json",
        )
        assert resp.status_code == 404


# ===================================================================
# 8  Win probability and weighted_value properties
# ===================================================================


class TestWinProbability:
    """Properties: win_probability (stage default vs override) and weighted_value."""

    def test_win_probability_from_stage(self, user, db):
        pipe = _create_pipeline(user.tenant_id)
        stage = _create_stage(user.tenant_id, pipe, probability=Decimal("0.25"))
        deal = _create_deal(user.tenant_id, pipe, stage)
        assert deal.win_probability == Decimal("0.25")

    def test_win_probability_override(self, user, db):
        pipe = _create_pipeline(user.tenant_id)
        stage = _create_stage(user.tenant_id, pipe, probability=Decimal("0.25"))
        deal = _create_deal(user.tenant_id, pipe, stage)
        deal.probability = Decimal("0.75")
        deal.save()
        assert deal.win_probability == Decimal("0.75")

    def test_weighted_value(self, user, db):
        pipe = _create_pipeline(user.tenant_id)
        stage = _create_stage(user.tenant_id, pipe, probability=Decimal("0.25"))
        deal = _create_deal(user.tenant_id, pipe, stage, value=Decimal("1000.00"))
        assert deal.weighted_value == Decimal("250.00")

        # With probability override
        deal.probability = Decimal("0.50")
        deal.save()
        assert deal.weighted_value == Decimal("500.00")

    def test_weighted_value_in_list_response(self, auth_client, user, pipeline):
        stage = pipeline.stages.first()
        deal = _create_deal(user.tenant_id, pipeline, stage, name="Weighted Test", value=Decimal("20000.00"))
        resp = auth_client.get(DEALS_URL)
        assert resp.status_code == 200
        for d in resp.json()["results"]:
            if d["id"] == str(deal.id):
                assert "weighted_value" in d
                assert "win_probability" in d
                break
        else:
            pytest.fail("deal not found in list")

    def test_weighted_value_and_probability_in_detail(self, auth_client, deal):
        resp = auth_client.get(f"{DEALS_URL}{deal.id}/")
        assert "win_probability" in resp.json()
        assert "weighted_value" in resp.json()


# ===================================================================
# 9  Search deals by name
# ===================================================================


class TestDealSearch:
    """Search deals via the search query param."""

    def test_search_finds_by_name(self, auth_client, user, pipeline, deal):
        stage = pipeline.stages.first()
        _create_deal(user.tenant_id, pipeline, stage, name="Another Deal")
        _create_deal(user.tenant_id, pipeline, stage, name="Matching Search Term")
        resp = auth_client.get(DEALS_URL, {"search": "Matching"})
        assert resp.status_code == 200
        names = [d["name"] for d in resp.json()["results"]]
        assert "Matching Search Term" in names
        assert "Fixture Deal" not in names
        assert "Another Deal" not in names

    def test_search_empty_result(self, auth_client, deal):
        resp = auth_client.get(DEALS_URL, {"search": "ZZZZNOTFOUND"})
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 0


# ===================================================================
# 10  Ordering deals by value, created_at
# ===================================================================


class TestDealOrdering:
    """Ordering deals via ordering query param."""

    def test_order_by_value_ascending(self, auth_client, user, pipeline):
        stage = pipeline.stages.first()
        d1 = _create_deal(user.tenant_id, pipeline, stage, name="Small", value=Decimal("100.00"))
        d2 = _create_deal(user.tenant_id, pipeline, stage, name="Medium", value=Decimal("5000.00"))
        d3 = _create_deal(user.tenant_id, pipeline, stage, name="Large", value=Decimal("100000.00"))
        resp = auth_client.get(DEALS_URL, {"ordering": "value"})
        assert resp.status_code == 200
        results = resp.json()["results"]
        values = [Decimal(r["value"]) for r in results]
        assert values == sorted(values)

    def test_order_by_value_descending(self, auth_client, user, pipeline):
        stage = pipeline.stages.first()
        d1 = _create_deal(user.tenant_id, pipeline, stage, name="Small", value=Decimal("100.00"))
        d2 = _create_deal(user.tenant_id, pipeline, stage, name="Medium", value=Decimal("5000.00"))
        d3 = _create_deal(user.tenant_id, pipeline, stage, name="Large", value=Decimal("100000.00"))
        resp = auth_client.get(DEALS_URL, {"ordering": "-value"})
        assert resp.status_code == 200
        results = resp.json()["results"]
        values = [Decimal(r["value"]) for r in results]
        assert values == sorted(values, reverse=True)

    def test_order_by_created_at_descending_default(self, auth_client, user, pipeline):
        """Default ordering is -created_at."""
        stage = pipeline.stages.first()
        d1 = _create_deal(user.tenant_id, pipeline, stage, name="First")
        d2 = _create_deal(user.tenant_id, pipeline, stage, name="Second")
        d3 = _create_deal(user.tenant_id, pipeline, stage, name="Third")
        resp = auth_client.get(DEALS_URL)
        assert resp.status_code == 200
        results = resp.json()["results"]
        # The most recently created should be first
        names = [r["name"] for r in results]
        first_idx = names.index("Third")
        second_idx = names.index("Second")
        third_idx = names.index("First")
        assert first_idx < second_idx < third_idx

    def test_order_by_created_at_ascending(self, auth_client, user, pipeline):
        stage = pipeline.stages.first()
        d1 = _create_deal(user.tenant_id, pipeline, stage, name="Oldest")
        d2 = _create_deal(user.tenant_id, pipeline, stage, name="Middle")
        d3 = _create_deal(user.tenant_id, pipeline, stage, name="Newest")
        resp = auth_client.get(DEALS_URL, {"ordering": "created_at"})
        assert resp.status_code == 200
        results = resp.json()["results"]
        names = [r["name"] for r in results]
        old_idx = names.index("Oldest")
        mid_idx = names.index("Middle")
        new_idx = names.index("Newest")
        assert old_idx < mid_idx < new_idx