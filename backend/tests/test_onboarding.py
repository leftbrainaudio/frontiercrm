"""Tests for onboarding flow — status, progress, reset, and pipeline templates."""

from __future__ import annotations

import uuid

import pytest
from django.utils import timezone


class TestOnboardingStatus:
    """GET /api/accounts/onboarding/status/"""

    STATUS_URL = "/api/accounts/onboarding/status/"

    def test_unauthenticated(self, api_client):
        """Returns 401 for unauthenticated requests."""
        resp = api_client.get(self.STATUS_URL)
        assert resp.status_code == 401

    def test_fresh_tenant(self, auth_client, user):
        """Fresh tenant returns is_onboarded=False, all steps False, empty skipped_steps."""
        resp = auth_client.get(self.STATUS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_onboarded"] is False
        assert data["company_done"] is False
        assert data["invite_done"] is False
        assert data["import_done"] is False
        assert data["email_done"] is False
        assert data["pipeline_done"] is False
        assert data["skipped_steps"] == []
        assert data["tenant"]["name"] is not None

    def test_partial_progress(self, auth_client, user):
        """Partially completed steps are reflected in status."""
        from apps.teams.models import Tenant

        tenant = Tenant.objects.get(id=user.tenant_id)
        settings = dict(tenant.settings or {})
        settings["onboarding"] = {
            "company_done": True,
            "invite_done": False,
            "import_done": True,
            "email_done": False,
            "pipeline_done": False,
            "skipped_steps": ["import"],
        }
        tenant.settings = settings
        tenant.save(update_fields=["settings"])

        resp = auth_client.get(self.STATUS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_onboarded"] is False
        assert data["company_done"] is True
        assert data["invite_done"] is False
        assert data["import_done"] is True
        assert data["email_done"] is False
        assert data["pipeline_done"] is False
        assert data["skipped_steps"] == ["import"]

    def test_fully_onboarded(self, auth_client, user):
        """Onboarded user returns is_onboarded=True."""
        user.is_onboarded = True
        user.onboarded_at = timezone.now()
        user.save(update_fields=["is_onboarded", "onboarded_at"])

        resp = auth_client.get(self.STATUS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_onboarded"] is True


class TestOnboardingProgress:
    """PATCH /api/accounts/onboarding/progress/"""

    PROGRESS_URL = "/api/accounts/onboarding/progress/"

    def test_unauthenticated(self, api_client):
        """Returns 401 for unauthenticated requests."""
        resp = api_client.patch(self.PROGRESS_URL, {"company_done": True}, format="json")
        assert resp.status_code == 401

    def test_company_setup(self, auth_client, user):
        """Company payload updates Tenant.name, Tenant.industry."""
        from apps.teams.models import Tenant

        resp = auth_client.patch(
            self.PROGRESS_URL,
            {
                "company": {"name": "Acme Corp", "industry": "technology"},
                "company_done": True,
            },
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["company_done"] is True
        assert data["tenant"]["name"] == "Acme Corp"
        assert data["tenant"]["industry"] == "technology"

        # Verify persisted in DB
        tenant = Tenant.objects.get(id=user.tenant_id)
        assert tenant.name == "Acme Corp"
        assert tenant.industry == "technology"

    def test_pipeline_template_creates_stages(self, auth_client, user):
        """pipeline_template='sales' creates a Pipeline with 5 stages."""
        from apps.pipelines.models import Pipeline, Stage

        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"pipeline_template": "sales", "pipeline_done": True},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pipeline_done"] is True

        pipelines = Pipeline.objects.filter(tenant_id=user.tenant_id, is_default=True)
        assert pipelines.count() == 1
        pipeline = pipelines.first()
        assert "Sales" in pipeline.name
        assert pipeline.stages.count() == 5

    def test_pipeline_template_idempotent(self, auth_client, user):
        """Calling pipeline_template twice does not create a duplicate pipeline."""
        from apps.pipelines.models import Pipeline

        # First call
        auth_client.patch(
            self.PROGRESS_URL,
            {"pipeline_template": "sales", "pipeline_done": True},
            format="json",
        )

        # Second call — should be a no-op
        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"pipeline_template": "saas"},
            format="json",
        )
        assert resp.status_code == 200

        pipelines = Pipeline.objects.filter(tenant_id=user.tenant_id, is_default=True)
        assert pipelines.count() == 1

    def test_invalid_template_returns_400(self, auth_client):
        """Unknown pipeline template returns 400."""
        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"pipeline_template": "nonexistent", "pipeline_done": True},
            format="json",
        )
        assert resp.status_code == 400
        assert "error" in resp.json()

    def test_skip_step(self, auth_client, user):
        """skip_step='import' marks import_done=True and adds to skipped_steps."""
        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"skip_step": "import"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["import_done"] is True
        assert "import" in data["skipped_steps"]

    def test_skip_step_twice_does_not_duplicate(self, auth_client):
        """Skipping the same step twice does not duplicate in skipped_steps."""
        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"skip_step": "email"},
            format="json",
        )
        data = resp.json()
        assert data["skipped_steps"].count("email") == 1

        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"skip_step": "email"},
            format="json",
        )
        data = resp.json()
        assert data["skipped_steps"].count("email") == 1

    def test_mark_complete_sets_user_onboarded(self, auth_client, user):
        """mark_complete=True sets User.is_onboarded=True and User.onboarded_at."""
        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"mark_complete": True},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_onboarded"] is True

        user.refresh_from_db()
        assert user.is_onboarded is True
        assert user.onboarded_at is not None

    def test_mark_complete_auto_skips_incomplete_steps(self, auth_client, user):
        """mark_complete auto-skips any incomplete steps."""
        from apps.teams.models import Tenant

        # Set some steps incomplete
        tenant = Tenant.objects.get(id=user.tenant_id)
        settings = dict(tenant.settings or {})
        settings["onboarding"] = {
            "company_done": True,
            "invite_done": False,
            "import_done": True,
            "email_done": False,
            "pipeline_done": False,
            "skipped_steps": [],
        }
        tenant.settings = settings
        tenant.save(update_fields=["settings"])

        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"mark_complete": True},
            format="json",
        )
        assert resp.status_code == 200

        # Verify all steps now done
        data = resp.json()
        assert data["is_onboarded"] is True
        assert data["company_done"] is True
        assert data["invite_done"] is True
        assert data["import_done"] is True
        assert data["email_done"] is True
        assert data["pipeline_done"] is True

    def test_step_boolean_updates(self, auth_client):
        """Individual step booleans update correctly."""
        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"invite_done": True},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["invite_done"] is True

        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"import_done": True, "email_done": False},
            format="json",
        )
        data = resp.json()
        assert data["import_done"] is True
        assert data["email_done"] is False


    def test_company_logo_url(self, auth_client, user):
        """logo_url in company payload persists to Tenant."""
        from apps.teams.models import Tenant

        resp = auth_client.patch(
            self.PROGRESS_URL,
            {
                "company": {
                    "name": "LogoCorp",
                    "logo_url": "https://example.com/logo.png",
                    "industry": "technology",
                },
                "company_done": True,
            },
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant"]["logo_url"] == "https://example.com/logo.png"

        tenant = Tenant.objects.get(id=user.tenant_id)
        assert tenant.logo_url == "https://example.com/logo.png"

    def test_company_partial_industry_only(self, auth_client, user):
        """Sending only industry in company payload leaves name unchanged."""
        from apps.teams.models import Tenant

        tenant = Tenant.objects.get(id=user.tenant_id)
        original_name = tenant.name

        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"company": {"industry": "finance"}},
            format="json",
        )
        assert resp.status_code == 200

        tenant.refresh_from_db()
        assert tenant.name == original_name
        assert tenant.industry == "finance"

    def test_company_empty_object_is_noop(self, auth_client, user):
        """company: {} should not modify tenant or crash."""
        from apps.teams.models import Tenant

        tenant = Tenant.objects.get(id=user.tenant_id)
        original_name = tenant.name

        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"company": {}},
            format="json",
        )
        assert resp.status_code == 200

        tenant.refresh_from_db()
        assert tenant.name == original_name

    def test_mark_complete_persists_auto_skipped_in_tenant_settings(
        self, auth_client, user
    ):
        """mark_complete persists auto-skipped steps into tenant.settings."""
        from apps.teams.models import Tenant

        # Set some steps incomplete
        tenant = Tenant.objects.get(id=user.tenant_id)
        settings = dict(tenant.settings or {})
        settings["onboarding"] = {
            "company_done": True,
            "invite_done": False,
            "import_done": True,
            "email_done": False,
            "pipeline_done": False,
            "skipped_steps": [],
        }
        tenant.settings = settings
        tenant.save(update_fields=["settings"])

        resp = auth_client.patch(
            self.PROGRESS_URL,
            {"mark_complete": True},
            format="json",
        )
        assert resp.status_code == 200

        # Verify tenant settings were persisted with auto-skipped steps
        tenant.refresh_from_db()
        onboarding = (tenant.settings or {}).get("onboarding", {})
        assert onboarding.get("company_done") is True
        assert onboarding.get("invite_done") is True  # auto-skipped
        assert onboarding.get("import_done") is True
        assert onboarding.get("email_done") is True  # auto-skipped
        assert onboarding.get("pipeline_done") is True  # auto-skipped


class TestOnboardingReset:
    """POST /api/accounts/onboarding/reset/"""

    RESET_URL = "/api/accounts/onboarding/reset/"

    def test_unauthenticated(self, api_client):
        """Returns 401 for unauthenticated requests."""
        resp = api_client.post(self.RESET_URL)
        assert resp.status_code == 401

    def test_reset_clears_state(self, auth_client, user):
        """Reset clears onboarding state and sets is_onboarded=False."""
        from apps.teams.models import Tenant

        # Set up some onboarding state
        tenant = Tenant.objects.get(id=user.tenant_id)
        settings = dict(tenant.settings or {})
        settings["onboarding"] = {
            "company_done": True,
            "invite_done": True,
            "import_done": False,
            "email_done": False,
            "pipeline_done": True,
            "skipped_steps": ["import"],
        }
        tenant.settings = settings
        tenant.save(update_fields=["settings"])

        user.is_onboarded = True
        user.onboarded_at = timezone.now()
        user.save(update_fields=["is_onboarded", "onboarded_at"])

        # Reset
        resp = auth_client.post(self.RESET_URL)
        assert resp.status_code == 200
        assert resp.json() == {"status": "reset"}

        # Verify state cleared
        user.refresh_from_db()
        assert user.is_onboarded is False
        assert user.onboarded_at is None

        tenant.refresh_from_db()
        onboarding = (tenant.settings or {}).get("onboarding")
        assert onboarding is None

    def test_reset_does_not_delete_created_data(self, auth_client, user):
        """Reset does not delete pipeline or other data created during onboarding."""
        from apps.pipelines.models import Pipeline

        # Create a pipeline as if the user already set one up
        Pipeline.objects.create(
            tenant_id=user.tenant_id,
            name="Test Pipeline",
            is_default=True,
        )

        auth_client.post(self.RESET_URL)

        pipelines = Pipeline.objects.filter(tenant_id=user.tenant_id)
        assert pipelines.count() == 1

    def test_reset_idempotent(self, auth_client, user):
        """Calling reset twice returns the same result."""
        resp = auth_client.post(self.RESET_URL)
        assert resp.status_code == 200
        assert resp.json() == {"status": "reset"}

        resp = auth_client.post(self.RESET_URL)
        assert resp.status_code == 200
        assert resp.json() == {"status": "reset"}

    def test_reset_with_no_onboarding_state(self, auth_client, user):
        """Reset when no onboarding state exists is a safe no-op."""
        user.is_onboarded = True
        user.onboarded_at = None
        user.save(update_fields=["is_onboarded", "onboarded_at"])

        resp = auth_client.post(self.RESET_URL)
        assert resp.status_code == 200
        assert resp.json() == {"status": "reset"}

        user.refresh_from_db()
        assert user.is_onboarded is False
        assert user.onboarded_at is None


class TestPipelineTemplateService:
    """Unit tests for create_pipeline_from_template."""

    def test_creates_sales_template(self, db, tenant_id):
        """Sales template creates Pipeline with 5 stages."""
        from apps.pipelines.services import create_pipeline_from_template

        pipeline = create_pipeline_from_template(
            tenant_id=str(tenant_id),
            template_name="sales",
        )
        assert pipeline is not None
        assert pipeline.is_default is True
        assert pipeline.stages.count() == 5
        stage_names = [s.name for s in pipeline.stages.all()]
        assert "Lead" in stage_names
        assert "Closed Won" in stage_names

    def test_creates_saas_template(self, db, tenant_id):
        """SaaS template creates Pipeline with 4 stages."""
        from apps.pipelines.services import create_pipeline_from_template

        pipeline = create_pipeline_from_template(
            tenant_id=str(tenant_id),
            template_name="saas",
        )
        assert pipeline is not None
        assert pipeline.stages.count() == 4

    def test_creates_recruiting_template(self, db, tenant_id):
        """Recruiting template creates Pipeline with 5 stages."""
        from apps.pipelines.services import create_pipeline_from_template

        pipeline = create_pipeline_from_template(
            tenant_id=str(tenant_id),
            template_name="recruiting",
        )
        assert pipeline is not None
        assert pipeline.stages.count() == 5

    def test_creates_custom_template(self, db, tenant_id):
        """Custom template creates Pipeline with 3 default stages."""
        from apps.pipelines.services import create_pipeline_from_template

        pipeline = create_pipeline_from_template(
            tenant_id=str(tenant_id),
            template_name="custom",
        )
        assert pipeline is not None
        assert pipeline.is_default is True
        assert pipeline.stages.count() == 3
        stage_names = [s.name for s in pipeline.stages.all()]
        assert stage_names == ["Lead", "Qualified", "Closed"]

    def test_unknown_template_raises_valueerror(self, db, tenant_id):
        """Unknown template name raises ValueError."""
        from apps.pipelines.services import create_pipeline_from_template

        with pytest.raises(ValueError, match="Unknown pipeline template"):
            create_pipeline_from_template(
                tenant_id=str(tenant_id),
                template_name="nonexistent",
            )

    def test_idempotent_when_default_exists(self, db, tenant_id):
        """Returns None when a default pipeline already exists."""
        from apps.pipelines.models import Pipeline
        from apps.pipelines.services import create_pipeline_from_template

        # Create a default pipeline first
        Pipeline.objects.create(
            tenant_id=tenant_id,
            name="Existing Pipeline",
            is_default=True,
        )

        result = create_pipeline_from_template(
            tenant_id=str(tenant_id),
            template_name="sales",
        )
        assert result is None
        # Only the original pipeline should exist
        assert Pipeline.objects.filter(tenant_id=tenant_id).count() == 1

    def test_stage_probabilities_match_spec(self, db):
        """Each template stage has the correct probability."""
        import uuid
        from apps.pipelines.services import (
            PIPELINE_TEMPLATES,
            create_pipeline_from_template,
        )

        for template_name in ("sales", "saas", "recruiting"):
            tid = uuid.uuid4()
            pipeline = create_pipeline_from_template(
                tenant_id=str(tid),
                template_name=template_name,
            )
            assert pipeline is not None
            for stage in pipeline.stages.all():
                spec_prob = [
                    t["probability"]
                    for t in PIPELINE_TEMPLATES[template_name]
                    if t["name"] == stage.name
                ][0]
                assert stage.probability == spec_prob
