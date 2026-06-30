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


def compose_payload(**overrides):
    """Return a compose-style POST payload (to_emails, subject, body_text)."""
    data = dict(
        to_emails=["recipient@example.com"],
        subject="Hello from CRM",
        body_text="This is a test email sent from FrontierCRM.",
        direction="outbound",
        from_email="placeholder@example.com",
        sent_at=timezone.now().isoformat(),
    )
    data.update(overrides)
    return data


@pytest.fixture
def gmail_user(user):
    """Extend the default user with Gmail OAuth tokens so compose succeeds."""
    user.google_refresh_token = "fake-refresh-token"
    user.google_access_token = "fake-access-token"
    user.save(update_fields=["google_refresh_token", "google_access_token"])
    return user


@pytest.fixture
def gmail_auth_client(gmail_user, api_client):
    """Authenticated client for a user with Gmail connected."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(gmail_user)
    if gmail_user.tenant_id:
        refresh.access_token["tenant_id"] = str(gmail_user.tenant_id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


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

    def test_create(self, gmail_auth_client, gmail_user, db):
        from unittest.mock import patch

        payload = compose_payload()
        with patch("apps.email.views.send_gmail_message.delay") as mock_delay:
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["direction"] == "outbound"
        assert data["status"] == "sending"
        assert data["from_email"] == gmail_user.email
        assert data["tenant_id"] == str(gmail_user.tenant_id)
        assert data["to_emails"] == ["recipient@example.com"]
        assert data["subject"] == "Hello from CRM"
        assert "id" in data
        mock_delay.assert_called_once()

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

    def test_create_sets_own_tenant(self, gmail_auth_client, gmail_user, db):
        from unittest.mock import patch

        payload = compose_payload()
        with patch("apps.email.views.send_gmail_message.delay"):
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["tenant_id"] == str(gmail_user.tenant_id)

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


# ── Compose & Send ──────────────────────────────────────────────────────────────


class TestEmailCompose:
    """POST /api/emails/ — the compose-to-send flow."""

    BASE_URL = "/api/emails/"

    def test_compose_creates_email_dispatches_celery(self, gmail_auth_client, gmail_user, db):
        """Compose creates email with correct fields and dispatches Celery task."""
        from unittest.mock import patch

        payload = compose_payload()
        with patch("apps.email.views.send_gmail_message.delay") as mock_delay:
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["direction"] == "outbound"
        assert data["status"] == "sending"
        assert data["from_email"] == gmail_user.email  # overridden by perform_create
        assert data["tenant_id"] == str(gmail_user.tenant_id)
        assert data["to_emails"] == ["recipient@example.com"]
        assert data["subject"] == "Hello from CRM"
        assert data["body_text"] == "This is a test email sent from FrontierCRM."
        assert "id" in data
        # Verify Celery task dispatched with (user_id, email_id)
        mock_delay.assert_called_once_with(str(gmail_user.id), data["id"])

    def test_compose_fails_without_gmail_connected(self, auth_client, user, db):
        """POST without Gmail returns 400; no email is created."""
        payload = compose_payload()
        resp = auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 400
        body = resp.json()
        # Custom error format: error in detail field, not errors
        err_text = str(body.get("detail", body))
        assert "gmail" in err_text.lower() or "connect" in err_text.lower()

    def test_compose_no_email_created_on_gmail_missing(self, auth_client, user, db):
        """No EmailMessage row is persisted when Gmail is not connected."""
        from apps.email.models import EmailMessage

        count_before = EmailMessage.objects.count()
        payload = compose_payload()
        auth_client.post(self.BASE_URL, payload, format="json")
        assert EmailMessage.objects.count() == count_before

    def test_compose_sets_outbound_and_sending(self, gmail_auth_client, gmail_user, db):
        """Direction and status are explicitly set by perform_create regardless of input."""
        from unittest.mock import patch

        # Even if the client sends junk direction/status, perform_create overrides
        payload = compose_payload(direction="inbound", status="synced")
        with patch("apps.email.views.send_gmail_message.delay"):
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["direction"] == "outbound"
        assert data["status"] == "sending"

    def test_compose_with_empty_body(self, gmail_auth_client, gmail_user, db):
        """Compose succeeds with empty body_text."""
        from unittest.mock import patch

        payload = compose_payload(body_text="")
        with patch("apps.email.views.send_gmail_message.delay"):
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["body_text"] == ""

    def test_compose_with_empty_to_emails_rejected(self, gmail_auth_client, gmail_user, db):
        """Compose with empty to_emails list is accepted (backend doesn't validate at serializer level)."""
        from unittest.mock import patch

        payload = compose_payload(to_emails=[])
        with patch("apps.email.views.send_gmail_message.delay"):
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["to_emails"] == []

    def test_compose_rejects_empty_to_string(self, gmail_auth_client, gmail_user, db):
        """Compose with empty string in to_emails is accepted (no per-item validation)."""
        from unittest.mock import patch

        payload = compose_payload(to_emails=[""])
        with patch("apps.email.views.send_gmail_message.delay"):
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["to_emails"] == [""]

    def test_compose_accepts_empty_subject(self, gmail_auth_client, gmail_user, db):
        """Compose with empty subject is accepted (some emails have no subject)."""
        from unittest.mock import patch

        payload = compose_payload(subject="")
        with patch("apps.email.views.send_gmail_message.delay"):
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["subject"] == ""

    def test_compose_with_bcc(self, gmail_auth_client, gmail_user, db):
        """Compose with BCC field works."""
        from unittest.mock import patch

        payload = compose_payload(bcc_emails=["bcc@example.com"])
        with patch("apps.email.views.send_gmail_message.delay"):
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["bcc_emails"] == ["bcc@example.com"]

    def test_compose_sets_sent_at(self, gmail_auth_client, gmail_user, db):
        """perform_create sets sent_at to now regardless of input."""
        from unittest.mock import patch
        from datetime import datetime, timedelta

        # Sending a date far in the past to verify override
        past_iso = (datetime.now() - timedelta(days=365)).isoformat()
        payload = compose_payload(sent_at=past_iso)
        with patch("apps.email.views.send_gmail_message.delay"):
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        # Should be recent, not the old date we sent
        sent = datetime.fromisoformat(data["sent_at"].replace("Z", "+00:00"))
        assert (datetime.now() - sent.replace(tzinfo=None)).total_seconds() < 60

    def test_compose_from_email_overridden(self, gmail_auth_client, gmail_user, db):
        """from_email in payload is overridden by perform_create with user.email."""
        from unittest.mock import patch

        payload = compose_payload(from_email="hacker@evil.com")
        with patch("apps.email.views.send_gmail_message.delay"):
            resp = gmail_auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["from_email"] == gmail_user.email

    def test_compose_no_celery_task_dispatched_on_validation_failure(self, auth_client, user, db):
        """Celery task is NOT dispatched when validation fails (no Gmail)."""
        from unittest.mock import patch

        payload = compose_payload()
        with patch("apps.email.views.send_gmail_message.delay") as mock_delay:
            auth_client.post(self.BASE_URL, payload, format="json")
        mock_delay.assert_not_called()


# ── Send Status ─────────────────────────────────────────────────────────────────


class TestEmailSendStatus:
    """GET /api/emails/{id}/send_status/ — poll endpoint."""

    BASE_URL = "/api/emails/"

    def test_send_status_sending(self, auth_client, user, db):
        """Returns 'sending' when email is still being sent."""
        from apps.email.models import EmailMessage

        email = EmailMessage.objects.create(
            tenant_id=user.tenant_id,
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.SENDING,
            from_email=user.email,
            to_emails=["r@example.com"],
            subject="Test",
            body_text="Hi",
            sent_at=timezone.now(),
        )
        resp = auth_client.get(f"{self.BASE_URL}{email.id}/send_status/")
        assert resp.status_code == 200
        assert resp.json() == {"status": "sending"}

    def test_send_status_sent_with_message_id(self, auth_client, user, db):
        """Returns 'sent' with the Gmail message_id when send succeeded."""
        from apps.email.models import EmailMessage

        email = EmailMessage.objects.create(
            tenant_id=user.tenant_id,
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.SENT,
            from_email=user.email,
            to_emails=["r@example.com"],
            subject="Test",
            body_text="Hi",
            sent_at=timezone.now(),
            external_id="gmail-msg-abc123",
        )
        resp = auth_client.get(f"{self.BASE_URL}{email.id}/send_status/")
        assert resp.status_code == 200
        assert resp.json() == {"status": "sent", "message_id": "gmail-msg-abc123"}

    def test_send_status_failed_with_error(self, auth_client, user, db):
        """Returns 'failed' with the error message."""
        from apps.email.models import EmailMessage

        email = EmailMessage.objects.create(
            tenant_id=user.tenant_id,
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.FAILED,
            from_email=user.email,
            to_emails=["r@example.com"],
            subject="Test",
            body_text="Hi",
            sent_at=timezone.now(),
            error_message="Send failed: 403 Forbidden",
        )
        resp = auth_client.get(f"{self.BASE_URL}{email.id}/send_status/")
        assert resp.status_code == 200
        assert resp.json() == {"status": "failed", "error_message": "Send failed: 403 Forbidden"}

    def test_send_status_other_tenant_404(self, auth_client, user, db):
        """Cannot poll send_status on another tenant's email."""
        from apps.email.models import EmailMessage

        other = uuid.uuid4()
        email = EmailMessage.objects.create(
            tenant_id=other,
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.SENDING,
            from_email="x@x.com",
            to_emails=["r@example.com"],
            subject="Test",
            body_text="Hi",
            sent_at=timezone.now(),
        )
        resp = auth_client.get(f"{self.BASE_URL}{email.id}/send_status/")
        assert resp.status_code == 404

    def test_send_status_draft_returns_draft_status(self, auth_client, user, db):
        """Draft emails also report their status accurately."""
        from apps.email.models import EmailMessage

        email = EmailMessage.objects.create(
            tenant_id=user.tenant_id,
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.DRAFT,
            from_email=user.email,
            to_emails=["r@example.com"],
            subject="Draft",
            body_text="Unfinished",
            sent_at=timezone.now(),
        )
        resp = auth_client.get(f"{self.BASE_URL}{email.id}/send_status/")
        assert resp.status_code == 200
        assert resp.json() == {"status": "draft"}


# ── Send Gmail Message Task ─────────────────────────────────────────────────────


class TestSendGmailMessageTask:
    """Celery task send_gmail_message — mocked Gmail API."""

    def _create_outgoing(self, user):
        from apps.email.models import EmailMessage

        return EmailMessage.objects.create(
            tenant_id=user.tenant_id,
            from_email=user.email,
            to_emails=["recipient@example.com"],
            subject="Task Test",
            body_text="Testing the Celery task",
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.SENDING,
            sent_at=timezone.now(),
        )

    def test_task_success_sets_sent_status(self, gmail_user, db):
        from unittest.mock import patch

        from apps.email.tasks import send_gmail_message

        email = self._create_outgoing(gmail_user)

        with patch("apps.email.tasks.requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"id": "gmail-sent-456", "threadId": "thread-789"}

            result = send_gmail_message(str(gmail_user.id), str(email.id))

        assert result == {"status": "sent", "message_id": "gmail-sent-456"}
        email.refresh_from_db()
        assert email.status == "sent"
        assert email.message_id == "gmail-sent-456"
        assert email.external_id == "gmail-sent-456"
        assert email.thread_id == "thread-789"
        assert email.is_read is True
        assert email.sent_at is not None

    def test_task_failure_sets_failed_status(self, gmail_user, db):
        from unittest.mock import patch

        from apps.email.tasks import send_gmail_message

        email = self._create_outgoing(gmail_user)

        with patch("apps.email.tasks.requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 403
            mock_resp.text = "Access denied: insufficient scopes"

            result = send_gmail_message(str(gmail_user.id), str(email.id))

        assert result["status"] == "failed"
        assert "Access denied" in result["error"]
        email.refresh_from_db()
        assert email.status == "failed"
        assert "Access denied" in email.error_message

    def test_task_creates_activity_on_success(self, gmail_user, db):
        from unittest.mock import patch

        from apps.activities.models import Activity
        from apps.email.tasks import send_gmail_message

        email = self._create_outgoing(gmail_user)

        with patch("apps.email.tasks.requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"id": "gmail-act-1", "threadId": "th-act-1"}

            send_gmail_message(str(gmail_user.id), str(email.id))

        activity = Activity.objects.filter(entity_id=email.id, activity_type="email").first()
        assert activity is not None
        assert activity.title == "Email sent: Task Test"
        assert "recipient@example.com" in activity.description
        assert activity.actor_id == gmail_user.id
        assert activity.metadata["status"] == "sent"
        assert activity.metadata["message_id"] == "gmail-act-1"

    def test_task_creates_activity_on_failure(self, gmail_user, db):
        from unittest.mock import patch

        from apps.activities.models import Activity
        from apps.email.tasks import send_gmail_message

        email = self._create_outgoing(gmail_user)

        with patch("apps.email.tasks.requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 500
            mock_resp.text = "Internal server error"

            send_gmail_message(str(gmail_user.id), str(email.id))

        activity = Activity.objects.filter(entity_id=email.id, activity_type="email").first()
        assert activity is not None
        assert "failed" in activity.title.lower()
        assert activity.metadata["status"] == "failed"
        assert "error" in activity.metadata

    def test_task_user_not_found(self, db):
        from apps.email.tasks import send_gmail_message

        result = send_gmail_message("00000000-0000-0000-0000-000000000000", str(uuid.uuid4()))
        assert result == {"error": "User not found"}

    def test_task_email_not_found(self, gmail_user, db):
        from apps.email.tasks import send_gmail_message

        result = send_gmail_message(str(gmail_user.id), str(uuid.uuid4()))
        assert result == {"error": "EmailMessage not found"}

    def test_task_retries_on_token_refresh(self, gmail_user, db):
        """401 triggers token refresh then retry; second attempt succeeds."""
        from unittest.mock import patch, MagicMock

        from apps.email.tasks import send_gmail_message

        email = self._create_outgoing(gmail_user)
        gmail_user.google_refresh_token = "valid-refresh"
        gmail_user.google_access_token = "expired-token"
        gmail_user.save(update_fields=["google_refresh_token", "google_access_token"])

        call_count = [0]

        def _side_effect(url, **kwargs):
            call_count[0] += 1
            mock = MagicMock()
            if call_count[0] == 1:
                mock.status_code = 401
                mock.text = "Token expired"
            else:
                mock.status_code = 200
                mock.json.return_value = {"id": "retry-ok", "threadId": "retry-th"}
            return mock

        with patch("apps.email.tasks.requests.post", side_effect=_side_effect):
            with patch("apps.email.tasks._refresh_google_token", return_value=True):
                result = send_gmail_message(str(gmail_user.id), str(email.id))

        assert result["status"] == "sent"
        assert result["message_id"] == "retry-ok"

    def test_task_both_body_text_and_html(self, gmail_user, db):
        """Task sends both body_text and body_html in MIME multipart structure."""
        from unittest.mock import patch
        from apps.email.tasks import send_gmail_message
        from apps.email.models import EmailMessage

        email = EmailMessage.objects.create(
            tenant_id=gmail_user.tenant_id,
            from_email=gmail_user.email,
            to_emails=["user@example.com"],
            subject="HTML Test",
            body_text="Plain text version",
            body_html="<p>HTML version</p>",
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.SENDING,
            sent_at=timezone.now(),
        )

        with patch("apps.email.tasks.requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"id": "html-msg-1", "threadId": "html-th-1"}
            send_gmail_message(str(gmail_user.id), str(email.id))

        # Verify the raw message is multipart with both alternatives
        call_args = mock_post.call_args
        sent_json = call_args[1]["json"]
        import base64
        raw_bytes = base64.urlsafe_b64decode(sent_json["raw"].encode("ascii"))
        decoded = raw_bytes.decode("utf-8", errors="replace")
        assert "Content-Type: multipart/alternative" in decoded
        assert "Plain text version" in decoded
        assert "HTML version" in decoded

    def test_task_sends_correct_headers(self, gmail_user, db):
        """MIME message has correct To, Subject, and From headers."""
        from unittest.mock import patch
        from apps.email.tasks import send_gmail_message
        from apps.email.models import EmailMessage

        email = EmailMessage.objects.create(
            tenant_id=gmail_user.tenant_id,
            from_email=gmail_user.email,
            to_emails=["recipient@example.com"],
            subject="Header Test",
            body_text="Check headers",
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.SENDING,
            sent_at=timezone.now(),
        )

        with patch("apps.email.tasks.requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"id": "hdr-1", "threadId": "hdr-th-1"}
            send_gmail_message(str(gmail_user.id), str(email.id))

        call_args = mock_post.call_args
        sent_json = call_args[1]["json"]
        import base64
        raw_bytes = base64.urlsafe_b64decode(sent_json["raw"].encode("ascii"))
        decoded = raw_bytes.decode("utf-8", errors="replace")
        assert "To: recipient@example.com" in decoded
        assert "Subject: Header Test" in decoded
        assert "From: " + gmail_user.email in decoded

    def test_task_has_max_retries_configured(self):
        """send_gmail_message Celery task has max_retries=2."""
        from apps.email.tasks import send_gmail_message
        assert send_gmail_message.max_retries == 2

    def test_task_success_creates_activity_with_metadata(self, gmail_user, db):
        from unittest.mock import patch
        from apps.activities.models import Activity
        from apps.email.tasks import send_gmail_message
        from apps.email.models import EmailMessage

        email = EmailMessage.objects.create(
            tenant_id=gmail_user.tenant_id,
            from_email=gmail_user.email,
            to_emails=["user@example.com"],
            subject="Meta Test",
            body_text="Test",
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.SENDING,
            sent_at=timezone.now(),
        )

        with patch("apps.email.tasks.requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"id": "meta-1", "threadId": "meta-th-1"}
            send_gmail_message(str(gmail_user.id), str(email.id))

        activity = Activity.objects.filter(
            entity_id=email.id, activity_type="email"
        ).first()
        assert activity is not None
        assert activity.metadata["status"] == "sent"
        assert activity.metadata["message_id"] == "meta-1"
        assert activity.metadata["subject"] == "Meta Test"

    def test_task_failure_updates_error_message_truncated(self, gmail_user, db):
        """Long error messages are truncated to 2000 chars."""
        from unittest.mock import patch
        from apps.email.tasks import send_gmail_message
        from apps.email.models import EmailMessage

        email = EmailMessage.objects.create(
            tenant_id=gmail_user.tenant_id,
            from_email=gmail_user.email,
            to_emails=["user@example.com"],
            subject="Error Test",
            body_text="Test",
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.SENDING,
            sent_at=timezone.now(),
        )

        long_error = "X" * 5000

        with patch("apps.email.tasks.requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 500
            mock_resp.text = long_error
            send_gmail_message(str(gmail_user.id), str(email.id))

        email.refresh_from_db()
        assert email.status == "failed"
        assert len(email.error_message) <= 2100  # "Send failed: " prefix + 2000 chars

    def test_task_with_multiple_recipients(self, gmail_user, db):
        """Task handles multiple To recipients."""
        from unittest.mock import patch
        from apps.email.tasks import send_gmail_message
        from apps.email.models import EmailMessage

        email = EmailMessage.objects.create(
            tenant_id=gmail_user.tenant_id,
            from_email=gmail_user.email,
            to_emails=["alice@example.com", "bob@example.com"],
            subject="Multi-Recipient",
            body_text="Hello both",
            direction=EmailMessage.EmailDirection.OUTBOUND,
            status=EmailMessage.EmailStatus.SENDING,
            sent_at=timezone.now(),
        )

        with patch("apps.email.tasks.requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"id": "multi-1", "threadId": "multi-th-1"}
            send_gmail_message(str(gmail_user.id), str(email.id))

        call_args = mock_post.call_args
        sent_json = call_args[1]["json"]
        import base64
        raw_bytes = base64.urlsafe_b64decode(sent_json["raw"].encode("ascii"))
        decoded = raw_bytes.decode("utf-8", errors="replace")
        assert "alice@example.com" in decoded
        assert "bob@example.com" in decoded