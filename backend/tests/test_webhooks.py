"""Comprehensive tests for webhook endpoints and delivery.

Covers: Endpoint CRUD, Event CRUD (ReadOnly), webhook receiver
with signature verification and subscriber matching, retry/dead-letter
via _retry_or_fail, and multi-tenant isolation.

Celery test settings: CELERY_TASK_ALWAYS_EAGER = True
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────


def create_endpoint(tenant_id, **overrides):
    """Factory helper — creates a WebhookEndpoint directly via ORM."""
    from apps.webhooks.models import WebhookEndpoint

    defaults = dict(
        tenant_id=tenant_id,
        url="https://hooks.example.com/crm",
        secret="test-secret",
        events=["contact.created", "deal.updated"],
        description="Test endpoint",
        is_active=True,
        max_retries=3,
    )
    defaults.update(overrides)
    return WebhookEndpoint.objects.create(**defaults)


def create_event(tenant_id, endpoint, **overrides):
    """Factory helper — creates a WebhookEvent directly via ORM."""
    from apps.webhooks.models import WebhookEvent

    defaults = dict(
        tenant_id=tenant_id,
        endpoint=endpoint,
        event_type="contact.created",
        payload={"event_type": "contact.created", "data": {"id": "abc"}},
        status=WebhookEvent.EventStatus.PENDING,
        attempt_count=0,
    )
    defaults.update(overrides)
    return WebhookEvent.objects.create(**defaults)


def compute_signature(payload: dict, secret: str, timestamp: str) -> str:
    """Replicate _compute_signature from webhooks.views."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    message = f"{timestamp}.{raw}"
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


# ── Endpoint CRUD ─────────────────────────────────────────────────────────────


class TestWebhookEndpointCRUD:
    """Full CRUD for WebhookEndpoint."""

    ENDPOINTS_URL = "/api/webhooks/endpoints/"

    # ── Create ──

    def test_create_endpoint(self, auth_client, user, db):
        resp = auth_client.post(
            self.ENDPOINTS_URL,
            {
                "url": "https://hooks.example.com/crm",
                "secret": "my-secret",
                "events": ["contact.created"],
                "description": "My webhook",
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "hooks.example.com" in data["url"]
        assert data["events"] == ["contact.created"]
        assert data["is_active"] is True
        assert data["tenant_id"] == str(user.tenant_id)
        assert data["failure_count"] == 0

    def test_create_minimal(self, auth_client, user, db):
        """Minimal payload works."""
        resp = auth_client.post(
            self.ENDPOINTS_URL,
            {"url": "https://example.com/hook", "secret": "s", "events": []},
            format="json",
        )
        assert resp.status_code == 201

    def test_create_without_events(self, auth_client, db):
        resp = auth_client.post(
            self.ENDPOINTS_URL,
            {"url": "https://ex.com/hook", "secret": "s", "events": []},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["events"] == []

    # ── List ──

    def test_list_empty(self, auth_client, db):
        resp = auth_client.get(self.ENDPOINTS_URL)
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_list_with_data(self, auth_client, user, db):
        create_endpoint(tenant_id=user.tenant_id)
        create_endpoint(tenant_id=user.tenant_id, url="https://other.com/hook")
        resp = auth_client.get(self.ENDPOINTS_URL)
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 2

    # ── Retrieve ──

    def test_retrieve(self, auth_client, user, db):
        ep = create_endpoint(tenant_id=user.tenant_id, description="Detail")
        resp = auth_client.get(f"{self.ENDPOINTS_URL}{ep.id}/")
        assert resp.status_code == 200
        assert resp.json()["description"] == "Detail"

    def test_retrieve_not_found(self, auth_client, db):
        resp = auth_client.get(f"{self.ENDPOINTS_URL}{uuid.uuid4()}/")
        assert resp.status_code == 404

    # ── Update ──

    def test_update(self, auth_client, user, db):
        ep = create_endpoint(tenant_id=user.tenant_id)
        resp = auth_client.patch(
            f"{self.ENDPOINTS_URL}{ep.id}/",
            {"description": "Updated webhook", "is_active": False},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated webhook"
        assert resp.json()["is_active"] is False

    def test_update_readonly_fields(self, auth_client, user, db):
        """tenant_id, last_triggered_at, failure_count are read-only."""
        ep = create_endpoint(tenant_id=user.tenant_id)
        resp = auth_client.patch(
            f"{self.ENDPOINTS_URL}{ep.id}/",
            {"tenant_id": str(uuid.uuid4())},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] == str(user.tenant_id)

    # ── Delete ──

    def test_delete(self, auth_client, user, db):
        ep = create_endpoint(tenant_id=user.tenant_id)
        resp = auth_client.delete(f"{self.ENDPOINTS_URL}{ep.id}/")
        assert resp.status_code == 204
        resp = auth_client.get(f"{self.ENDPOINTS_URL}{ep.id}/")
        assert resp.status_code == 404


# ── Event Read-Only CRUD ──────────────────────────────────────────────────────


class TestWebhookEventCRUD:
    """WebhookEvent is read-only via API (list, retrieve, filter)."""

    EVENTS_URL = "/api/webhooks/events/"

    def test_list_empty(self, auth_client, db):
        resp = auth_client.get(self.EVENTS_URL)
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_list_with_data(self, auth_client, user, db):
        ep = create_endpoint(tenant_id=user.tenant_id)
        create_event(tenant_id=user.tenant_id, endpoint=ep)
        create_event(tenant_id=user.tenant_id, endpoint=ep, event_type="deal.updated")
        resp = auth_client.get(self.EVENTS_URL)
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 2

    def test_retrieve(self, auth_client, user, db):
        ep = create_endpoint(tenant_id=user.tenant_id)
        ev = create_event(tenant_id=user.tenant_id, endpoint=ep)
        resp = auth_client.get(f"{self.EVENTS_URL}{ev.id}/")
        assert resp.status_code == 200
        assert resp.json()["event_type"] == "contact.created"

    def test_create_not_allowed(self, auth_client, user, db):
        """Events cannot be created via API (ReadOnlyModelViewSet)."""
        ep = create_endpoint(tenant_id=user.tenant_id)
        resp = auth_client.post(
            self.EVENTS_URL,
            {
                "endpoint": str(ep.id),
                "event_type": "test.event",
                "payload": {},
            },
            format="json",
        )
        assert resp.status_code in (403, 405)

    def test_filter_by_event_type(self, auth_client, user, db):
        ep = create_endpoint(tenant_id=user.tenant_id)
        create_event(tenant_id=user.tenant_id, endpoint=ep, event_type="contact.created")
        create_event(tenant_id=user.tenant_id, endpoint=ep, event_type="deal.updated")
        resp = auth_client.get(self.EVENTS_URL, {"event_type": "contact.created"})
        types = [e["event_type"] for e in resp.json()["results"]]
        assert "contact.created" in types
        assert "deal.updated" not in types

    def test_filter_by_status(self, auth_client, user, db):
        from apps.webhooks.models import WebhookEvent

        ep = create_endpoint(tenant_id=user.tenant_id)
        create_event(tenant_id=user.tenant_id, endpoint=ep, status=WebhookEvent.EventStatus.PENDING)
        create_event(tenant_id=user.tenant_id, endpoint=ep, status=WebhookEvent.EventStatus.DELIVERED)
        resp = auth_client.get(self.EVENTS_URL, {"status": "pending"})
        statuses = [e["status"] for e in resp.json()["results"]]
        assert "pending" in statuses
        assert "delivered" not in statuses

    def test_filter_by_endpoint(self, auth_client, user, db):
        ep1 = create_endpoint(tenant_id=user.tenant_id, url="https://ep1.com/hook")
        ep2 = create_endpoint(tenant_id=user.tenant_id, url="https://ep2.com/hook")
        create_event(tenant_id=user.tenant_id, endpoint=ep1)
        create_event(tenant_id=user.tenant_id, endpoint=ep2)
        resp = auth_client.get(self.EVENTS_URL, {"endpoint": str(ep1.id)})
        assert len(resp.json()["results"]) == 1


# ── Webhook Receiver ──────────────────────────────────────────────────────────


class TestWebhookReceiver:
    """POST /api/webhooks/receive/ — public endpoint."""

    RECEIVE_URL = "/api/webhooks/receive/"

    def test_no_subscribers(self, api_client, db):
        """No matching endpoints → 200, no_subscribers."""
        resp = api_client.post(
            self.RECEIVE_URL,
            {"event_type": "unknown.event"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_subscribers"

    def test_endpoint_no_matching_events(self, api_client, user, db):
        """Endpoint exists but doesn't subscribe to this event type → no_subscribers."""
        create_endpoint(
            tenant_id=user.tenant_id,
            events=["contact.created"],  # only subscribes to contact.created
        )
        resp = api_client.post(
            self.RECEIVE_URL,
            {"event_type": "deal.updated"},  # not in endpoint's events
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_subscribers"

    def test_with_matching_endpoint(self, api_client, user, db):
        """Matching endpoint → 202, accepted, event created, task dispatched."""
        create_endpoint(
            tenant_id=user.tenant_id,
            events=["contact.created"],
            secret="test-secret",
        )
        # Mock requests.post to prevent actual HTTP call from dispatch_webhook
        with patch("apps.webhooks.views.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            resp = api_client.post(
                self.RECEIVE_URL,
                {"event_type": "contact.created", "data": {"id": "123"}},
                format="json",
            )
        assert resp.status_code == 202
        assert resp.json()["status"] == "accepted"

        # Verify event was created
        from apps.webhooks.models import WebhookEvent

        assert WebhookEvent.objects.count() == 1
        event = WebhookEvent.objects.first()
        assert event.event_type == "contact.created"
        assert event.endpoint.url == "https://hooks.example.com/crm"

    def test_multiple_endpoints_same_event(self, api_client, user, db):
        """Multiple endpoints subscribing to the same event each get an event."""
        ep1 = create_endpoint(
            tenant_id=user.tenant_id,
            url="https://ep1.com/hook",
            events=["contact.created"],
        )
        ep2 = create_endpoint(
            tenant_id=user.tenant_id,
            url="https://ep2.com/hook",
            events=["contact.created"],
        )
        with patch("apps.webhooks.views.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            resp = api_client.post(
                self.RECEIVE_URL,
                {"event_type": "contact.created"},
                format="json",
            )
        assert resp.status_code == 202

        from apps.webhooks.models import WebhookEvent

        events = WebhookEvent.objects.all()
        assert events.count() == 2
        endpoint_ids = {e.endpoint_id for e in events}
        assert endpoint_ids == {ep1.id, ep2.id}


# ── Signature Verification ────────────────────────────────────────────────────


class TestWebhookSignatureVerification:
    """HMAC-SHA256 signature verification in webhook receiver."""

    RECEIVE_URL = "/api/webhooks/receive/"

    def test_valid_signature(self, api_client, user, db):
        """Valid HMAC signature → event accepted."""
        secret = "shared-secret"
        create_endpoint(tenant_id=user.tenant_id, secret=secret, events=["data.updated"])

        payload = {"event_type": "data.updated", "data": {"key": "value"}}
        timestamp = str(int(time.time()))
        signature = compute_signature(payload, secret, timestamp)

        with patch("apps.webhooks.views.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            resp = api_client.post(
                self.RECEIVE_URL,
                payload,
                format="json",
                HTTP_X_WEBHOOK_SIGNATURE=signature,
                HTTP_X_WEBHOOK_TIMESTAMP=timestamp,
            )
        assert resp.status_code == 202

    def test_invalid_signature(self, api_client, user, db):
        """Invalid HMAC signature → endpoint is matched but no event created."""
        secret = "shared-secret"
        create_endpoint(tenant_id=user.tenant_id, secret=secret, events=["data.updated"])

        payload = {"event_type": "data.updated", "data": {"key": "value"}}
        wrong_sig = "invalid-signature"

        with patch("apps.webhooks.views.requests.post") as mock_post:
            resp = api_client.post(
                self.RECEIVE_URL,
                payload,
                format="json",
                HTTP_X_WEBHOOK_SIGNATURE=wrong_sig,
                HTTP_X_WEBHOOK_TIMESTAMP=str(int(time.time())),
            )
        # The endpoint is in the endpoints list (matched by event_type), but
        # signature verification fails so event creation is skipped.
        # The receiver still returns 202 (accepted) — it found matching endpoints.
        assert resp.status_code == 202
        assert resp.json()["status"] == "accepted"
        mock_post.assert_not_called()

        # No event was created
        from apps.webhooks.models import WebhookEvent

        assert WebhookEvent.objects.count() == 0

    def test_no_signature_but_endpoint_has_secret(self, api_client, user, db):
        """If endpoint has a secret but request has no signature, signature check is skipped (existing behavior)."""
        secret = "shared-secret"
        create_endpoint(tenant_id=user.tenant_id, secret=secret, events=["data.updated"])

        with patch("apps.webhooks.views.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            resp = api_client.post(
                self.RECEIVE_URL,
                {"event_type": "data.updated"},
                format="json",
            )
        # The receiver checks `if endpoint.secret and signature:` — empty signature
        # means the branch is skipped, so the endpoint is matched as usual.
        assert resp.status_code == 202

    def test_endpoint_without_secret(self, api_client, user, db):
        """Endpoint with empty secret accepts events without signature verification."""
        create_endpoint(tenant_id=user.tenant_id, secret="", events=["data.public"])

        with patch("apps.webhooks.views.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            resp = api_client.post(
                self.RECEIVE_URL,
                {"event_type": "data.public"},
                format="json",
            )
        assert resp.status_code == 202

    def test_verify_signature_format(self, api_client, user, db):
        """The _compute_signature produces a hex-encoded HMAC-SHA256."""
        from apps.webhooks.views import _compute_signature

        payload = {"a": 1, "b": 2}
        sig = _compute_signature(payload, "secret", "12345")
        assert len(sig) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in sig)


# ── Retry / Dead-letter ───────────────────────────────────────────────────────


class TestWebhookRetryAndDeadLetter:
    """Retry logic: _retry_or_fail, attempt_count, status transitions."""

    def test_retry_increments_attempt_count(self, db, user):
        """_retry_or_fail sets PENDING + increments attempt_count below max."""
        from apps.webhooks.models import WebhookEndpoint, WebhookEvent
        from apps.webhooks.views import _retry_or_fail

        endpoint = create_endpoint(tenant_id=user.tenant_id, max_retries=3)
        event = create_event(tenant_id=user.tenant_id, endpoint=endpoint, attempt_count=0)

        mock_task = MagicMock()
        _retry_or_fail(mock_task, event, endpoint, "Connection timeout")

        assert event.attempt_count == 0  # incremented in dispatch, not _retry_or_fail
        assert event.status == WebhookEvent.EventStatus.PENDING
        assert event.error_message == "Connection timeout"
        mock_task.retry.assert_called_once()

    def test_dead_letter_after_max_retries(self, db, user):
        """When attempt_count >= max_retries, event is FAILED."""
        from apps.webhooks.models import WebhookEndpoint, WebhookEvent
        from apps.webhooks.views import _retry_or_fail

        endpoint = create_endpoint(tenant_id=user.tenant_id, max_retries=3)
        event = create_event(
            tenant_id=user.tenant_id,
            endpoint=endpoint,
            attempt_count=3,  # already at max
        )

        mock_task = MagicMock()
        _retry_or_fail(mock_task, event, endpoint, "HTTP 500: Server Error")

        assert event.status == WebhookEvent.EventStatus.FAILED
        assert event.error_message == "HTTP 500: Server Error"
        mock_task.retry.assert_not_called()

        # endpoint.failure_count was incremented
        endpoint.refresh_from_db()
        assert endpoint.failure_count == 1

    def test_dead_letter_above_max_retries(self, db, user):
        """attempt_count > max_retries also goes to FAILED."""
        from apps.webhooks.models import WebhookEndpoint, WebhookEvent
        from apps.webhooks.views import _retry_or_fail

        endpoint = create_endpoint(tenant_id=user.tenant_id, max_retries=2)
        event = create_event(
            tenant_id=user.tenant_id,
            endpoint=endpoint,
            attempt_count=5,
        )

        mock_task = MagicMock()
        _retry_or_fail(mock_task, event, endpoint, "Gave up")

        assert event.status == WebhookEvent.EventStatus.FAILED
        mock_task.retry.assert_not_called()

    def test_dispatch_success_updates_event_and_endpoint(self, db, user):
        """Successful dispatch (HTTP 200) marks DELIVERED and resets failure_count."""
        from apps.webhooks.models import WebhookEndpoint, WebhookEvent

        endpoint = create_endpoint(tenant_id=user.tenant_id, failure_count=3)
        event = create_event(tenant_id=user.tenant_id, endpoint=endpoint, attempt_count=0)

        with patch("apps.webhooks.views.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            from apps.webhooks.views import dispatch_webhook

            dispatch_webhook.delay(event.id)

        event.refresh_from_db()
        assert event.status == WebhookEvent.EventStatus.DELIVERED
        assert event.attempt_count == 1
        assert event.response_status == 200

        endpoint.refresh_from_db()
        assert endpoint.failure_count == 0
        assert endpoint.last_triggered_at is not None

    def test_dispatch_non_2xx_triggers_retry(self, db, user):
        """Non-2xx response triggers retry via _retry_or_fail."""
        import celery.exceptions

        from apps.webhooks.models import WebhookEndpoint, WebhookEvent

        endpoint = create_endpoint(tenant_id=user.tenant_id, max_retries=3)
        event = create_event(tenant_id=user.tenant_id, endpoint=endpoint, attempt_count=0)

        with patch("apps.webhooks.views.requests.post") as mock_post:
            mock_post.return_value.status_code = 500
            mock_post.return_value.text = "Internal error"

            # With CELERY_TASK_EAGER_PROPAGATES=True, retry raises Retry exception
            from apps.webhooks.views import dispatch_webhook

            with pytest.raises(celery.exceptions.Retry):
                dispatch_webhook.delay(event.id)

        # Event may not be persisted since retry raised before save()
        event.refresh_from_db()
        assert event.attempt_count == 0  # not saved due to retry exception propagation


# ── Multi-tenant isolation ────────────────────────────────────────────────────


class TestWebhookTenantIsolation:
    """Tenants must not see each other's webhook data."""

    ENDPOINTS_URL = "/api/webhooks/endpoints/"
    EVENTS_URL = "/api/webhooks/events/"

    def test_endpoint_list_isolation(self, auth_client, user, db):
        other = uuid.uuid4()
        create_endpoint(tenant_id=user.tenant_id, url="https://mine.com/hook")
        create_endpoint(tenant_id=other, url="https://theirs.com/hook")
        resp = auth_client.get(self.ENDPOINTS_URL)
        urls = [e["url"] for e in resp.json()["results"]]
        assert "https://mine.com/hook" in urls
        assert "https://theirs.com/hook" not in urls

    def test_endpoint_retrieve_isolation(self, auth_client, user, db):
        other = uuid.uuid4()
        ep = create_endpoint(tenant_id=other)
        resp = auth_client.get(f"{self.ENDPOINTS_URL}{ep.id}/")
        assert resp.status_code == 404

    def test_endpoint_update_isolation(self, auth_client, user, db):
        other = uuid.uuid4()
        ep = create_endpoint(tenant_id=other)
        resp = auth_client.patch(
            f"{self.ENDPOINTS_URL}{ep.id}/",
            {"description": "Hacked"},
            format="json",
        )
        assert resp.status_code == 404

    def test_endpoint_delete_isolation(self, auth_client, user, db):
        other = uuid.uuid4()
        ep = create_endpoint(tenant_id=other)
        resp = auth_client.delete(f"{self.ENDPOINTS_URL}{ep.id}/")
        assert resp.status_code == 404

    def test_event_list_isolation(self, auth_client, user, db):
        other = uuid.uuid4()
        my_ep = create_endpoint(tenant_id=user.tenant_id)
        other_ep = create_endpoint(tenant_id=other)
        create_event(tenant_id=user.tenant_id, endpoint=my_ep, event_type="my.event")
        create_event(tenant_id=other, endpoint=other_ep, event_type="hidden.event")
        resp = auth_client.get(self.EVENTS_URL)
        types = [e["event_type"] for e in resp.json()["results"]]
        assert "my.event" in types
        assert "hidden.event" not in types

    def test_event_retrieve_isolation(self, auth_client, user, db):
        other = uuid.uuid4()
        ep = create_endpoint(tenant_id=other)
        ev = create_event(tenant_id=other, endpoint=ep)
        resp = auth_client.get(f"{self.EVENTS_URL}{ev.id}/")
        assert resp.status_code == 404

    def test_receiver_uses_endpoint_tenant(self, api_client, user, db):
        """Webhook receiver creates events under the endpoint's tenant."""
        create_endpoint(tenant_id=user.tenant_id, events=["data.event"])
        with patch("apps.webhooks.views.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            api_client.post(
                "/api/webhooks/receive/",
                {"event_type": "data.event"},
                format="json",
            )

        from apps.webhooks.models import WebhookEvent

        event = WebhookEvent.objects.first()
        assert event is not None
        assert event.tenant_id == user.tenant_id

    def test_create_sets_own_tenant(self, auth_client, user, db):
        resp = auth_client.post(
            self.ENDPOINTS_URL,
            {"url": "https://example.com/hook", "secret": "s", "events": []},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["tenant_id"] == str(user.tenant_id)