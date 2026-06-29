"""Tests for pipeline and stage endpoints."""

from __future__ import annotations

import uuid

from apps.pipelines.models import Pipeline, Stage


class TestPipelineAPI:
    """Pipeline and stage CRUD tests."""

    PIPELINES_URL = "/api/deals/pipelines/"
    STAGES_URL = "/api/deals/stages/"

    def test_create_pipeline(self, auth_client, user, db):
        resp = auth_client.post(
            self.PIPELINES_URL,
            {"name": "Sales Pipeline 2025"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Sales Pipeline 2025"

    def test_create_stage(self, auth_client, user, db):
        pipeline = Pipeline.objects.create(tenant_id=user.tenant_id, name="Test Pipe")
        resp = auth_client.post(
            self.STAGES_URL,
            {
                "pipeline": str(pipeline.id),
                "name": "Qualified",
                "display_order": 1,
                "probability": "0.50",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Qualified"

    def test_pipeline_with_stages(self, auth_client, user, db):
        pipeline = Pipeline.objects.create(tenant_id=user.tenant_id, name="Full Pipe")
        Stage.objects.create(
            tenant_id=user.tenant_id,
            pipeline=pipeline,
            name="Lead In",
            display_order=1,
        )
        resp = auth_client.get(f"{self.PIPELINES_URL}{pipeline.id}/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Full Pipe"

    def test_tenant_isolation_pipeline(self, auth_client, user, db):
        Pipeline.objects.create(tenant_id=uuid.uuid4(), name="Other Pipe")
        resp = auth_client.get(self.PIPELINES_URL)
        for p in resp.json()["results"]:
            assert p["tenant_id"] == str(user.tenant_id)

    def test_tenant_isolation_stage(self, auth_client, user, db):
        other_id = uuid.uuid4()
        other_pipe = Pipeline.objects.create(tenant_id=other_id, name="Other")
        Stage.objects.create(tenant_id=other_id, pipeline=other_pipe, name="Other Stage")
        resp = auth_client.get(self.STAGES_URL)
        assert len(resp.json()["results"]) == 0
