"""Comprehensive tests for email endpoints.

Covers: CRUD, filtering, search, toggle-star, mark-read,
multi-tenant isolation, and ordering.
"""

from __future__ import annotations

import uuid

import pytest
from django.utils import timezone


# ── Helpers ───────────────────────────────────────────────────────────────────


def create_email(tenant_id, **overrides):
    """Factory helper — creates an EmailMessage directly via ORM."""
    from apps.email.models import EmailMessage

    defaults = dict(
        tenant_id=tenant_id,
        message_id=f"msg-{uuid.uuid4().hex[:12]}",
        thread_id=f"thread-{uuid.uuid4().hex[:8]}",
        direction="inbound",
        from_email="sender@example.com",
        to_emails=["recipient@example.com"],
        cc_emails=[],
        bcc_emails=[],
        subject="Test Subject",
        body_text="Hello world",
        body_html="<p>Hello world</p>",
        sent_at=timezone.now(),
        received_at=timezone.now(),
        is_read=False,
        is_starred=False,
        labels=[],
        entity_type="",
        entity_id=None,
        gmail_history_id="",
    )
    defaults.update(overrides)
    return EmailMessage.objects.create(**defaults)


def email_data(**overrides):
    """Return a POST-able payload dict."""
    data = dict(
        message_id="msg-new",
        thread_id="thread-new",
        direction="inbound",
        from_email="new@example.com",
        to_emails=["me@example.com"],
        subject="New Email",
        body_text="Fresh content",
        sent_at=timezone.now().isoformat(),
    )
    data.update(overrides)
    return data


# ── CRUD ──────────────────────────────────────────────────────────────────────


class TestEmailCRUD:
    """Create, Read, Update, Delete."""

    BASE_URL = "/api/emails/"

    def test_list_empty(self, auth_client, db):
        resp = auth_client.get(self.BASE_URL)
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_list_with_data(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id)
        create_email(tenant_id=user.tenant_id, subject="Second")
        resp = auth_client.get(self.BASE_URL)
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 2

    def test_create(self, auth_client, user, db):
        payload = email_data()
        resp = auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["subject"] == "New Email"
        assert data["from_email"] == "new@example.com"
        assert data["tenant_id"] == str(user.tenant_id)
        assert data["message_id"] == "msg-new"
        assert "id" in data

    def test_retrieve(self, auth_client, user, db):
        email = create_email(tenant_id=user.tenant_id, subject="Detail Test")
        resp = auth_client.get(f"{self.BASE_URL}{email.id}/")
        assert resp.status_code == 200
        assert resp.json()["subject"] == "Detail Test"

    def test_update(self, auth_client, user, db):
        email = create_email(tenant_id=user.tenant_id)
        resp = auth_client.patch(
            f"{self.BASE_URL}{email.id}/",
            {"subject": "Updated Subject"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["subject"] == "Updated Subject"

    def test_delete(self, auth_client, user, db):
        email = create_email(tenant_id=user.tenant_id)
        resp = auth_client.delete(f"{self.BASE_URL}{email.id}/")
        assert resp.status_code == 204
        resp = auth_client.get(f"{self.BASE_URL}{email.id}/")
        assert resp.status_code == 404

    def test_retrieve_not_found(self, auth_client, db):
        resp = auth_client.get(f"{self.BASE_URL}{uuid.uuid4()}/")
        assert resp.status_code == 404


# ── Filtering ─────────────────────────────────────────────────────────────────


class TestEmailFiltering:
    """FilterSet-based filtering."""

    BASE_URL = "/api/emails/"

    def test_filter_by_direction(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, direction="inbound", message_id="i1")
        create_email(tenant_id=user.tenant_id, direction="outbound", message_id="o1")
        resp = auth_client.get(self.BASE_URL, {"direction": "inbound"})
        assert resp.status_code == 200
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "i1" in ids
        assert "o1" not in ids

    def test_filter_by_from_email_exact(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, from_email="alice@a.com", message_id="a1")
        create_email(tenant_id=user.tenant_id, from_email="bob@b.com", message_id="b1")
        resp = auth_client.get(self.BASE_URL, {"from_email": "alice@a.com"})
        assert resp.status_code == 200
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "a1" in ids
        assert "b1" not in ids

    def test_filter_by_from_email_icontains(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, from_email="alice@a.com", message_id="a1")
        create_email(tenant_id=user.tenant_id, from_email="bob@b.com", message_id="b1")
        resp = auth_client.get(self.BASE_URL, {"from_email__icontains": "lice"})
        assert resp.status_code == 200
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "a1" in ids
        assert "b1" not in ids

    def test_filter_by_thread_id(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, thread_id="th-a", message_id="m1")
        create_email(tenant_id=user.tenant_id, thread_id="th-b", message_id="m2")
        resp = auth_client.get(self.BASE_URL, {"thread_id": "th-a"})
        assert resp.status_code == 200
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "m1" in ids
        assert "m2" not in ids

    def test_filter_by_entity_type(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, entity_type="contact", message_id="m1")
        create_email(tenant_id=user.tenant_id, entity_type="deal", message_id="m2")
        resp = auth_client.get(self.BASE_URL, {"entity_type": "contact"})
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "m1" in ids
        assert "m2" not in ids

    def test_filter_by_entity_id(self, auth_client, user, db):
        eid = uuid.uuid4()
        create_email(tenant_id=user.tenant_id, entity_id=eid, message_id="m1")
        create_email(tenant_id=user.tenant_id, entity_id=uuid.uuid4(), message_id="m2")
        resp = auth_client.get(self.BASE_URL, {"entity_id": str(eid)})
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "m1" in ids
        assert "m2" not in ids

    def test_filter_by_is_read(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, is_read=True, message_id="r1")
        create_email(tenant_id=user.tenant_id, is_read=False, message_id="u1")
        resp = auth_client.get(self.BASE_URL, {"is_read": "true"})
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "r1" in ids
        assert "u1" not in ids

    def test_filter_by_is_starred(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, is_starred=True, message_id="s1")
        create_email(tenant_id=user.tenant_id, is_starred=False, message_id="n1")
        resp = auth_client.get(self.BASE_URL, {"is_starred": "true"})
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "s1" in ids
        assert "n1" not in ids


# ── Search ────────────────────────────────────────────────────────────────────


class TestEmailSearch:
    """SearchFilter — subject, body_text, from_email."""

    BASE_URL = "/api/emails/"

    def test_search_by_subject(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, subject="Quarterly Report", message_id="m1")
        create_email(tenant_id=user.tenant_id, subject="Lunch Plans", message_id="m2")
        resp = auth_client.get(self.BASE_URL, {"search": "Quarterly"})
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "m1" in ids
        assert "m2" not in ids

    def test_search_by_body_text(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, body_text="Invoice attached", message_id="m1")
        create_email(tenant_id=user.tenant_id, body_text="Meeting notes", message_id="m2")
        resp = auth_client.get(self.BASE_URL, {"search": "Invoice"})
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "m1" in ids
        assert "m2" not in ids

    def test_search_by_from_email(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, from_email="vendor@supplier.com", message_id="m1")
        create_email(tenant_id=user.tenant_id, from_email="friend@personal.com", message_id="m2")
        resp = auth_client.get(self.BASE_URL, {"search": "vendor@supplier"})
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "m1" in ids
        assert "m2" not in ids

    def test_search_no_match(self, auth_client, user, db):
        create_email(tenant_id=user.tenant_id, subject="Something")
        resp = auth_client.get(self.BASE_URL, {"search": "nonexistent"})
        assert resp.json()["results"] == []


# ── Actions ───────────────────────────────────────────────────────────────────


class TestEmailActions:
    """toggle_star, mark_read."""

    BASE_URL = "/api/emails/"

    def test_toggle_star_on(self, auth_client, user, db):
        email = create_email(tenant_id=user.tenant_id, is_starred=False)
        resp = auth_client.post(f"{self.BASE_URL}{email.id}/toggle_star/")
        assert resp.status_code == 200
        assert resp.json()["is_starred"] is True
        email.refresh_from_db()
        assert email.is_starred is True

    def test_toggle_star_off(self, auth_client, user, db):
        email = create_email(tenant_id=user.tenant_id, is_starred=True)
        resp = auth_client.post(f"{self.BASE_URL}{email.id}/toggle_star/")
        assert resp.status_code == 200
        assert resp.json()["is_starred"] is False
        email.refresh_from_db()
        assert email.is_starred is False

    def test_toggle_star_twice(self, auth_client, user, db):
        """Toggle on then off."""
        email = create_email(tenant_id=user.tenant_id, is_starred=False)
        auth_client.post(f"{self.BASE_URL}{email.id}/toggle_star/")
        email.refresh_from_db()
        assert email.is_starred is True
        auth_client.post(f"{self.BASE_URL}{email.id}/toggle_star/")
        email.refresh_from_db()
        assert email.is_starred is False

    def test_mark_read(self, auth_client, user, db):
        email = create_email(tenant_id=user.tenant_id, is_read=False)
        resp = auth_client.post(f"{self.BASE_URL}{email.id}/mark_read/")
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True
        email.refresh_from_db()
        assert email.is_read is True

    def test_mark_read_already_read(self, auth_client, user, db):
        """Marking an already-read email is idempotent."""
        email = create_email(tenant_id=user.tenant_id, is_read=True)
        resp = auth_client.post(f"{self.BASE_URL}{email.id}/mark_read/")
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    def test_toggle_star_other_tenant(self, auth_client, user, db):
        """Cannot toggle star on another tenant's email."""
        other_tenant = uuid.uuid4()
        email = create_email(tenant_id=other_tenant)
        resp = auth_client.post(f"{self.BASE_URL}{email.id}/toggle_star/")
        assert resp.status_code == 404

    def test_mark_read_other_tenant(self, auth_client, user, db):
        """Cannot mark another tenant's email as read."""
        other_tenant = uuid.uuid4()
        email = create_email(tenant_id=other_tenant)
        resp = auth_client.post(f"{self.BASE_URL}{email.id}/mark_read/")
        assert resp.status_code == 404


# ── Multi-tenant isolation ────────────────────────────────────────────────────


class TestEmailTenantIsolation:
    """Tenants must not see each other's emails."""

    BASE_URL = "/api/emails/"

    def test_list_isolation(self, auth_client, user, db):
        other_tenant = uuid.uuid4()
        create_email(tenant_id=user.tenant_id, subject="Mine")
        create_email(tenant_id=other_tenant, subject="Theirs")
        resp = auth_client.get(self.BASE_URL)
        subjects = [e["subject"] for e in resp.json()["results"]]
        assert "Mine" in subjects
        assert "Theirs" not in subjects

    def test_retrieve_isolation(self, auth_client, user, db):
        other_tenant = uuid.uuid4()
        email = create_email(tenant_id=other_tenant)
        resp = auth_client.get(f"{self.BASE_URL}{email.id}/")
        assert resp.status_code == 404

    def test_update_isolation(self, auth_client, user, db):
        other_tenant = uuid.uuid4()
        email = create_email(tenant_id=other_tenant)
        resp = auth_client.patch(
            f"{self.BASE_URL}{email.id}/",
            {"subject": "Hacked"},
            format="json",
        )
        assert resp.status_code == 404

    def test_delete_isolation(self, auth_client, user, db):
        other_tenant = uuid.uuid4()
        email = create_email(tenant_id=other_tenant)
        resp = auth_client.delete(f"{self.BASE_URL}{email.id}/")
        assert resp.status_code == 404

    def test_create_sets_own_tenant(self, auth_client, user, db):
        payload = email_data()
        resp = auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["tenant_id"] == str(user.tenant_id)

    def test_filter_respects_tenant(self, auth_client, user, db):
        """Filtering does not leak other tenant's emails."""
        other = uuid.uuid4()
        create_email(tenant_id=other, direction="inbound", message_id="hidden")
        resp = auth_client.get(self.BASE_URL, {"direction": "inbound"})
        ids = [e["message_id"] for e in resp.json()["results"]]
        assert "hidden" not in ids


# ── Ordering ──────────────────────────────────────────────────────────────────


class TestEmailOrdering:
    """OrderingFilter — especially -sent_at."""

    BASE_URL = "/api/emails/"

    def test_default_ordering_desc_sent_at(self, auth_client, user, db):
        from datetime import timedelta

        now = timezone.now()
        older = create_email(
            tenant_id=user.tenant_id,
            sent_at=now - timedelta(days=2),
            message_id="old",
        )
        newer = create_email(
            tenant_id=user.tenant_id,
            sent_at=now - timedelta(hours=1),
            message_id="new",
        )
        resp = auth_client.get(self.BASE_URL)
        ids = [e["message_id"] for e in resp.json()["results"]]
        # latest first
        assert ids == ["new", "old"]

    def test_ordering_field_is_allowed(self, auth_client, user, db):
        resp = auth_client.get(self.BASE_URL, {"ordering": "-sent_at"})
        assert resp.status_code == 200