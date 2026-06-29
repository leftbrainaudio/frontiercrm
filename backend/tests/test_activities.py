"""Tests for activity feed API endpoints."""

from __future__ import annotations

import uuid

from apps.activities.models import Activity


class TestActivityAPI:
    """Activity feed endpoint tests."""

    BASE_URL = "/api/activities/"

    def test_list_activities_empty(self, auth_client, db):
        resp = auth_client.get(self.BASE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["count"] == 0

    def test_list_activities(self, auth_client, user, db):
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="First activity",
        )
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="call",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Second activity",
        )
        resp = auth_client.get(self.BASE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert len(data["results"]) == 2

    def test_create_activity(self, auth_client, user, db):
        resp = auth_client.post(
            self.BASE_URL,
            {
                "activity_type": "note",
                "title": "Added a note",
                "entity_type": "contact",
                "entity_id": str(uuid.uuid4()),
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["activity_type"] == "note"
        assert data["title"] == "Added a note"
        assert data["tenant_id"] == str(user.tenant_id)
        assert "id" in data
        assert "created_at" in data
        assert Activity.objects.count() == 1

    def test_create_activity_sets_actor_id(self, auth_client, user, db):
        resp = auth_client.post(
            self.BASE_URL,
            {
                "activity_type": "email",
                "title": "Email sent",
                "entity_type": "contact",
                "entity_id": str(uuid.uuid4()),
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["actor_id"] == str(user.id)

    def test_create_activity_all_types(self, auth_client, user, db):
        """Test creating activities with each valid activity_type."""
        activity_types = [
            "note", "call", "email", "meeting", "task",
            "deal_stage_change", "file_upload", "system",
        ]
        for at in activity_types:
            resp = auth_client.post(
                self.BASE_URL,
                {
                    "activity_type": at,
                    "title": f"Activity of type {at}",
                    "entity_type": "contact",
                    "entity_id": str(uuid.uuid4()),
                },
                format="json",
            )
            assert resp.status_code == 201, f"Failed for activity_type={at}: {resp.content}"
            assert resp.json()["activity_type"] == at
        assert Activity.objects.count() == len(activity_types)

    def test_get_activity_detail(self, auth_client, user, db):
        entity_id = uuid.uuid4()
        activity = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="meeting",
            title="Team standup",
            description="Daily sync",
            entity_type="deal",
            entity_id=entity_id,
            metadata={"duration": 30},
        )
        resp = auth_client.get(f"{self.BASE_URL}{activity.id}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(activity.id)
        assert data["activity_type"] == "meeting"
        assert data["title"] == "Team standup"
        assert data["description"] == "Daily sync"
        assert data["entity_type"] == "deal"
        assert data["entity_id"] == str(entity_id)
        assert data["metadata"] == {"duration": 30}

    def test_update_activity(self, auth_client, user, db):
        activity = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Original title",
        )
        resp = auth_client.patch(
            f"{self.BASE_URL}{activity.id}/",
            {"title": "Updated title"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated title"
        assert data["id"] == str(activity.id)

    def test_delete_activity(self, auth_client, user, db):
        activity = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="system",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="To delete",
        )
        resp = auth_client.delete(f"{self.BASE_URL}{activity.id}/")
        assert resp.status_code == 204
        assert Activity.objects.count() == 0

    def test_delete_nonexistent_returns_404(self, auth_client, db):
        resp = auth_client.delete(f"{self.BASE_URL}{uuid.uuid4()}/")
        assert resp.status_code == 404

    def test_filter_by_activity_type(self, auth_client, user, db):
        for at in ["note", "call", "email"]:
            Activity.objects.create(
                tenant_id=user.tenant_id,
                activity_type=at,
                entity_type="contact",
                entity_id=uuid.uuid4(),
                title=f"Activity {at}",
            )
        resp = auth_client.get(f"{self.BASE_URL}?activity_type=call")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        for item in data["results"]:
            assert item["activity_type"] == "call"

    def test_filter_by_entity_type(self, auth_client, user, db):
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Contact activity",
        )
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="deal",
            entity_id=uuid.uuid4(),
            title="Deal activity",
        )
        resp = auth_client.get(f"{self.BASE_URL}?entity_type=deal")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["entity_type"] == "deal"

    def test_filter_by_entity_id(self, auth_client, user, db):
        target_entity_id = uuid.uuid4()
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=target_entity_id,
            title="Target activity",
        )
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other activity",
        )
        resp = auth_client.get(f"{self.BASE_URL}?entity_id={target_entity_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["entity_id"] == str(target_entity_id)

    def test_filter_by_actor_id(self, auth_client, user, db):
        """Activities created via the API have actor_id set automatically."""
        # Create one via API so actor_id = user.id
        resp = auth_client.post(
            self.BASE_URL,
            {
                "activity_type": "note",
                "title": "My activity",
                "entity_type": "contact",
                "entity_id": str(uuid.uuid4()),
            },
            format="json",
        )
        assert resp.status_code == 201
        # Create another via API to also be by this user
        resp2 = auth_client.post(
            self.BASE_URL,
            {
                "activity_type": "call",
                "title": "Another",
                "entity_type": "contact",
                "entity_id": str(uuid.uuid4()),
            },
            format="json",
        )
        assert resp2.status_code == 201

        # Filter by the current user's actor_id
        resp3 = auth_client.get(f"{self.BASE_URL}?actor_id={user.id}")
        assert resp3.status_code == 200
        data = resp3.json()
        assert data["count"] == 2

    def test_multi_tenant_isolation(self, auth_client, user, db):
        Activity.objects.create(
            tenant_id=uuid.uuid4(),
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other tenant activity",
        )
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="My tenant activity",
        )
        resp = auth_client.get(self.BASE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        for a in data["results"]:
            assert a["tenant_id"] == str(user.tenant_id)

    def test_tenant_isolation_on_create(self, auth_client, user, db):
        """Activities created through the API are scoped to the user's tenant."""
        resp = auth_client.post(
            self.BASE_URL,
            {
                "activity_type": "note",
                "title": "Tenant scoped",
                "entity_type": "contact",
                "entity_id": str(uuid.uuid4()),
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["tenant_id"] == str(user.tenant_id)

    def test_ordering_by_minus_created_at(self, auth_client, user, db):
        """Activities are ordered by -created_at (most recent first)."""
        # Create two activities; the second should appear first in results
        a1 = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Older",
        )
        # Manually force a1's created_at to be older
        import datetime
        from django.utils import timezone
        Activity.objects.filter(id=a1.id).update(
            created_at=timezone.now() - datetime.timedelta(hours=1)
        )

        a2 = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="call",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Newer",
        )

        resp = auth_client.get(f"{self.BASE_URL}?ordering=-created_at")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        # Newer activity should be first
        assert data["results"][0]["title"] == "Newer"
        assert data["results"][1]["title"] == "Older"

    def test_access_other_tenant_activity_returns_404(self, auth_client, user, db):
        """Cannot view detail of another tenant's activity."""
        other = Activity.objects.create(
            tenant_id=uuid.uuid4(),
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other tenant",
        )
        resp = auth_client.get(f"{self.BASE_URL}{other.id}/")
        assert resp.status_code == 404

    def test_update_other_tenant_activity_returns_404(self, auth_client, user, db):
        other = Activity.objects.create(
            tenant_id=uuid.uuid4(),
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other tenant",
        )
        resp = auth_client.patch(
            f"{self.BASE_URL}{other.id}/",
            {"title": "Hacked"},
            format="json",
        )
        assert resp.status_code == 404
