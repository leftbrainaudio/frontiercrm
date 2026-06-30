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


# ── Activity Timeline endpoint tests ──────────────────────────────────


class TestActivityTimeline:
    """Timeline endpoint tests — GET /api/activities/timeline/."""

    TIMELINE_URL = "/api/activities/timeline/"

    def _create_activities(self, user, count: int = 3) -> list[Activity]:
        """Helper: create N activities for the given user's tenant."""
        activities = []
        for i in range(count):
            a = Activity.objects.create(
                tenant_id=user.tenant_id,
                activity_type="note" if i % 2 == 0 else "call",
                entity_type="contact" if i % 2 == 0 else "deal",
                entity_id=uuid.uuid4(),
                title=f"Timeline activity {i}",
                description=f"Description {i}",
                actor_id=user.id,
            )
            activities.append(a)
        return activities

    # ── Basic functionality ────────────────────────────────────────────

    def test_empty_timeline(self, auth_client, db):
        resp = auth_client.get(self.TIMELINE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["results"] == []
        assert data["page"] == 1

    def test_timeline_returns_activities(self, auth_client, user, db):
        self._create_activities(user, 3)
        resp = auth_client.get(self.TIMELINE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3
        assert len(data["results"]) == 3

    def test_timeline_multi_tenant_isolation(self, auth_client, user, db):
        """Activities from other tenants should not appear in the timeline."""
        self._create_activities(user, 2)
        Activity.objects.create(
            tenant_id=uuid.uuid4(),
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other tenant activity",
        )
        resp = auth_client.get(self.TIMELINE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2

    def test_timeline_response_shape(self, auth_client, user, db):
        self._create_activities(user, 1)
        resp = auth_client.get(self.TIMELINE_URL)
        data = resp.json()
        result = data["results"][0]
        # Check required fields
        assert "id" in result
        assert "activity_type" in result
        assert "title" in result
        assert "description" in result
        assert "created_at" in result
        assert "actor" in result
        assert "entity" in result
        assert "metadata" in result
        # Check nested shapes
        assert "id" in result["actor"]
        assert "name" in result["actor"]
        assert "avatar_url" in result["actor"]
        assert "type" in result["entity"]
        assert "id" in result["entity"]
        assert "name" in result["entity"]
        assert "url" in result["entity"]

    def test_timeline_ordering_newest_first(self, auth_client, user, db):
        """Activities should be ordered by created_at descending."""
        import datetime
        from django.utils import timezone

        a1 = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Oldest",
            actor_id=user.id,
        )
        # Manually set older timestamp
        Activity.objects.filter(id=a1.id).update(
            created_at=timezone.now() - datetime.timedelta(hours=2)
        )
        a2 = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="call",
            entity_type="deal",
            entity_id=uuid.uuid4(),
            title="Newest",
            actor_id=user.id,
        )
        resp = auth_client.get(self.TIMELINE_URL)
        data = resp.json()
        assert data["count"] == 2
        assert data["results"][0]["title"] == "Newest"
        assert data["results"][1]["title"] == "Oldest"

    # ── Pagination ─────────────────────────────────────────────────────

    def test_pagination_default_page_size(self, auth_client, user, db):
        self._create_activities(user, 30)
        resp = auth_client.get(self.TIMELINE_URL)
        data = resp.json()
        assert data["count"] == 30
        assert len(data["results"]) == 25  # default page_size
        assert data["page_size"] == 25
        assert data["total_pages"] == 2
        assert data["next"] is not None
        assert data["previous"] is None

    def test_pagination_custom_page_size(self, auth_client, user, db):
        self._create_activities(user, 10)
        resp = auth_client.get(f"{self.TIMELINE_URL}?page_size=5")
        data = resp.json()
        assert data["count"] == 10
        assert len(data["results"]) == 5
        assert data["page_size"] == 5
        assert data["total_pages"] == 2

    def test_pagination_max_page_size_capped(self, auth_client, user, db):
        self._create_activities(user, 50)
        resp = auth_client.get(f"{self.TIMELINE_URL}?page_size=200")
        data = resp.json()
        assert data["page_size"] == 100  # max_page_size
        assert len(data["results"]) == 50

    def test_pagination_second_page(self, auth_client, user, db):
        self._create_activities(user, 30)
        resp = auth_client.get(f"{self.TIMELINE_URL}?page=2")
        data = resp.json()
        assert data["page"] == 2
        assert len(data["results"]) == 5  # remaining 5
        assert data["previous"] is not None

    def test_pagination_page_out_of_range(self, auth_client, user, db):
        self._create_activities(user, 5)
        resp = auth_client.get(f"{self.TIMELINE_URL}?page=999")
        # DRF PageNumberPagination returns 404 for out-of-range pages
        assert resp.status_code == 404

    # ── Activity type filter ───────────────────────────────────────────

    def test_filter_by_activity_type(self, auth_client, user, db):
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="A note",
            actor_id=user.id,
        )
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="call",
            entity_type="deal",
            entity_id=uuid.uuid4(),
            title="A call",
            actor_id=user.id,
        )
        resp = auth_client.get(f"{self.TIMELINE_URL}?activity_type=call")
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["title"] == "A call"

    def test_filter_by_activity_type_no_match(self, auth_client, user, db):
        self._create_activities(user, 2)
        resp = auth_client.get(f"{self.TIMELINE_URL}?activity_type=meeting")
        data = resp.json()
        assert data["count"] == 0

    # ── Date range filter ──────────────────────────────────────────────

    def test_filter_by_start_date(self, auth_client, user, db):
        import datetime
        from django.utils import timezone

        # Create one old and one recent activity
        old = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Old activity",
            actor_id=user.id,
        )
        Activity.objects.filter(id=old.id).update(
            created_at=timezone.now() - datetime.timedelta(days=10)
        )
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="call",
            entity_type="deal",
            entity_id=uuid.uuid4(),
            title="Recent activity",
            actor_id=user.id,
        )
        # Filter to only last 5 days
        cutoff = (timezone.now() - datetime.timedelta(days=5)).date()
        resp = auth_client.get(f"{self.TIMELINE_URL}?start_date={cutoff}")
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["title"] == "Recent activity"

    def test_filter_by_end_date(self, auth_client, user, db):
        import datetime
        from django.utils import timezone

        old = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Old activity",
            actor_id=user.id,
        )
        Activity.objects.filter(id=old.id).update(
            created_at=timezone.now() - datetime.timedelta(days=10)
        )
        recent = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="call",
            entity_type="deal",
            entity_id=uuid.uuid4(),
            title="Recent activity",
            actor_id=user.id,
        )
        Activity.objects.filter(id=recent.id).update(
            created_at=timezone.now() - datetime.timedelta(days=2)
        )
        # Only activities before 5 days ago
        cutoff = (timezone.now() - datetime.timedelta(days=4)).date()
        resp = auth_client.get(f"{self.TIMELINE_URL}?end_date={cutoff}")
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["title"] == "Old activity"

    def test_filter_by_date_range(self, auth_client, user, db):
        import datetime
        from django.utils import timezone

        # Activity outside range (too old)
        old = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Too old",
            actor_id=user.id,
        )
        Activity.objects.filter(id=old.id).update(
            created_at=timezone.now() - datetime.timedelta(days=20)
        )
        # Activity inside range
        mid = Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="call",
            entity_type="deal",
            entity_id=uuid.uuid4(),
            title="In range",
            actor_id=user.id,
        )
        Activity.objects.filter(id=mid.id).update(
            created_at=timezone.now() - datetime.timedelta(days=5)
        )
        # Activity outside range (too recent) — actually "too recent" won't
        # be excluded by end_date since both reference now; skip that case.

        start = (timezone.now() - datetime.timedelta(days=10)).date()
        end = (timezone.now() - datetime.timedelta(days=1)).date()
        resp = auth_client.get(f"{self.TIMELINE_URL}?start_date={start}&end_date={end}")
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["title"] == "In range"

    # ── Actor filter ───────────────────────────────────────────────────

    def test_filter_by_actor_id(self, auth_client, user, db):
        self._create_activities(user, 3)
        resp = auth_client.get(f"{self.TIMELINE_URL}?actor_id={user.id}")
        data = resp.json()
        assert data["count"] == 3

    def test_filter_by_actor_id_no_match(self, auth_client, user, db):
        self._create_activities(user, 2)
        resp = auth_client.get(f"{self.TIMELINE_URL}?actor_id={uuid.uuid4()}")
        data = resp.json()
        assert data["count"] == 0

    def test_filter_by_entity_type(self, auth_client, user, db):
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="note",
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Contact activity",
            actor_id=user.id,
        )
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="call",
            entity_type="deal",
            entity_id=uuid.uuid4(),
            title="Deal activity",
            actor_id=user.id,
        )
        resp = auth_client.get(f"{self.TIMELINE_URL}?entity_type=deal")
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["entity"]["type"] == "deal"

    # ── Error handling ─────────────────────────────────────────────────

    def test_invalid_filter_returns_400(self, auth_client, db):
        """Invalid filter values should return 400, not 500."""
        resp = auth_client.get(f"{self.TIMELINE_URL}?start_date=not-a-date")
        assert resp.status_code == 400

    def test_actor_resolution(self, auth_client, user, db):
        """Actor name should be resolved from the User model."""
        self._create_activities(user, 1)
        resp = auth_client.get(self.TIMELINE_URL)
        data = resp.json()
        result = data["results"][0]
        assert result["actor"]["name"] != ""
        assert isinstance(result["actor"]["id"], str) or result["actor"]["id"] is not None

    def test_entity_route_mapping(self, auth_client, user, db):
        """Entity URLs should map to meaningful frontend routes."""
        Activity.objects.create(
            tenant_id=user.tenant_id,
            activity_type="deal_stage_change",
            entity_type="deal",
            entity_id=uuid.uuid4(),
            title="Deal moved",
            actor_id=user.id,
        )
        resp = auth_client.get(self.TIMELINE_URL)
        data = resp.json()
        # The URL maps to /pipeline for deals, even though no actual Deal
        # object exists (entity.name will be empty but url is set)
        result = data["results"][0]
        assert result["entity"]["type"] == "deal"
        assert result["entity"]["url"] == "/pipeline"
