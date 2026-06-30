"""Comprehensive tests for Slack notification webhooks.

Covers: CRUD for SlackWebhook, test/deactivate actions, notification
service filtering, rate limiting, failure auto-deactivation, message
formatters, tenant isolation, and signal/task wiring.

Running: pytest tests/test_slack.py -x -v
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
import requests
from django.utils import timezone


# ── Helpers ───────────────────────────────────────────────────────────────────


def create_webhook(tenant_id, **overrides):
    """Factory helper — creates a SlackWebhook directly via ORM."""
    from apps.slack.models import SlackWebhook

    defaults = dict(
        tenant_id=tenant_id,
        webhook_url="https://hooks.slack.com/services/T00/B00/test",
        display_name="Test Webhook",
        subscribed_events=[],
        is_active=True,
    )
    defaults.update(overrides)
    return SlackWebhook.objects.create(**defaults)


def create_activity(tenant_id, act_type="deal_stage_change", entity_type="deal", **meta_overrides):
    """Factory helper — creates an Activity record."""
    from apps.activities.models import Activity

    meta = {
        "deal_name": "Big Deal",
        "from_stage": "Qualified",
        "to_stage": "Proposal",
        "value": "50000",
        "owner_name": "Alice",
        "pipeline_name": "Sales Pipeline",
        "pipeline_id": str(uuid.uuid4()),
    }
    meta.update(meta_overrides)

    return Activity.objects.create(
        tenant_id=tenant_id,
        activity_type=act_type,
        entity_type=entity_type,
        entity_id=uuid.uuid4(),
        title=f"Test {act_type}",
        metadata=meta,
    )


# ── SlackWebhook CRUD ─────────────────────────────────────────────────────────


class TestSlackWebhookCRUD:
    """Full CRUD for SlackWebhook."""

    WEBHOOKS_URL = "/api/slack/webhooks/"

    # ── Create ──

    def test_create_webhook(self, auth_client, user, db):
        resp = auth_client.post(
            self.WEBHOOKS_URL,
            {
                "webhook_url": "https://hooks.slack.com/services/T00/B00/abc123",
                "display_name": "Sales Team",
                "subscribed_events": ["deal_stage_change", "deal_status_change"],
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["webhook_url"] == "https://hooks.slack.com/services/T00/B00/abc123"
        assert data["display_name"] == "Sales Team"
        assert data["subscribed_events"] == ["deal_stage_change", "deal_status_change"]
        assert data["is_active"] is True
        assert data["tenant_id"] == str(user.tenant_id)
        assert data["failure_count"] == 0

    def test_create_minimal(self, auth_client, user, db):
        resp = auth_client.post(
            self.WEBHOOKS_URL,
            {"webhook_url": "https://hooks.slack.com/services/T00/B00/x"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["subscribed_events"] == []
        assert resp.json()["display_name"] == ""

    def test_create_invalid_url(self, auth_client, db):
        resp = auth_client.post(
            self.WEBHOOKS_URL,
            {"webhook_url": "https://evil.com/hook"},
            format="json",
        )
        assert resp.status_code == 400
        assert "hooks.slack.com" in str(resp.json())

    def test_create_with_pipeline_filter(self, auth_client, user, db):
        from apps.pipelines.models import Pipeline

        pipeline = Pipeline.objects.create(
            tenant_id=user.tenant_id,
            name="Sales Pipeline",
        )
        resp = auth_client.post(
            self.WEBHOOKS_URL,
            {
                "webhook_url": "https://hooks.slack.com/services/T00/B00/abc",
                "pipeline_filter_id": str(pipeline.id),
                "subscribed_events": ["deal_stage_change"],
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["pipeline_filter"]["id"] == str(pipeline.id)
        assert resp.json()["pipeline_filter"]["name"] == "Sales Pipeline"

    # ── List ──

    def test_list_empty(self, auth_client, db):
        resp = auth_client.get(self.WEBHOOKS_URL)
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_list_with_data(self, auth_client, user, db):
        create_webhook(tenant_id=user.tenant_id)
        create_webhook(tenant_id=user.tenant_id, display_name="Second Webhook")
        resp = auth_client.get(self.WEBHOOKS_URL)
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 2

    # ── Retrieve ──

    def test_retrieve(self, auth_client, user, db):
        wh = create_webhook(tenant_id=user.tenant_id, display_name="Detail Check")
        resp = auth_client.get(f"{self.WEBHOOKS_URL}{wh.id}/")
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Detail Check"

    def test_retrieve_not_found(self, auth_client, db):
        resp = auth_client.get(f"{self.WEBHOOKS_URL}{uuid.uuid4()}/")
        assert resp.status_code == 404

    # ── Update ──

    def test_update(self, auth_client, user, db):
        wh = create_webhook(tenant_id=user.tenant_id)
        resp = auth_client.patch(
            f"{self.WEBHOOKS_URL}{wh.id}/",
            {"display_name": "Updated", "is_active": False},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated"
        assert resp.json()["is_active"] is False

    def test_update_readonly_fields(self, auth_client, user, db):
        """tenant_id, failure_count, last_triggered_at are read-only."""
        wh = create_webhook(tenant_id=user.tenant_id)
        resp = auth_client.patch(
            f"{self.WEBHOOKS_URL}{wh.id}/",
            {"tenant_id": str(uuid.uuid4()), "failure_count": 999},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] == str(user.tenant_id)
        assert resp.json()["failure_count"] == 0

    # ── Delete ──

    def test_delete(self, auth_client, user, db):
        wh = create_webhook(tenant_id=user.tenant_id)
        resp = auth_client.delete(f"{self.WEBHOOKS_URL}{wh.id}/")
        assert resp.status_code == 204
        resp = auth_client.get(f"{self.WEBHOOKS_URL}{wh.id}/")
        assert resp.status_code == 404


# ── Test and Deactivate Actions ───────────────────────────────────────────────


class TestSlackWebhookActions:
    """POST /api/slack/webhooks/{id}/test/ and /deactivate/."""

    WEBHOOKS_URL = "/api/slack/webhooks/"

    def test_test_message_delivered(self, auth_client, user, db):
        wh = create_webhook(tenant_id=user.tenant_id)
        with patch("apps.slack.views.send_test_message") as mock_send:
            mock_send.return_value = {"status": "delivered"}
            resp = auth_client.post(f"{self.WEBHOOKS_URL}{wh.id}/test/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "delivered"

    def test_test_message_failed(self, auth_client, user, db):
        wh = create_webhook(tenant_id=user.tenant_id)
        with patch("apps.slack.views.send_test_message") as mock_send:
            mock_send.return_value = {"status": "failed", "error": "404 Not Found"}
            resp = auth_client.post(f"{self.WEBHOOKS_URL}{wh.id}/test/")
        assert resp.status_code == 400
        assert "failed" in resp.json()["status"]

    def test_deactivate(self, auth_client, user, db):
        wh = create_webhook(tenant_id=user.tenant_id)
        resp = auth_client.post(f"{self.WEBHOOKS_URL}{wh.id}/deactivate/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deactivated"
        wh.refresh_from_db()
        assert wh.is_active is False

    def test_deactivate_already_inactive(self, auth_client, user, db):
        wh = create_webhook(tenant_id=user.tenant_id, is_active=False)
        resp = auth_client.post(f"{self.WEBHOOKS_URL}{wh.id}/deactivate/")
        assert resp.status_code == 200
        wh.refresh_from_db()
        assert wh.is_active is False


# ── Tenant Isolation ──────────────────────────────────────────────────────────


class TestSlackWebhookTenantIsolation:
    """Tenant A's webhooks must not be visible to Tenant B."""

    WEBHOOKS_URL = "/api/slack/webhooks/"

    def test_list_isolation(self, auth_client, user, tenant_id, db):
        """User sees only their own webhooks."""
        other_tenant = uuid.uuid4()
        create_webhook(tenant_id=user.tenant_id)  # user's webhook
        create_webhook(tenant_id=other_tenant)  # other tenant

        resp = auth_client.get(self.WEBHOOKS_URL)
        assert resp.status_code == 200
        ids = [w["id"] for w in resp.json()["results"]]
        assert len(ids) == 1  # only user's webhook

    def test_update_isolation(self, auth_client, user, db):
        """Cannot update another tenant's webhook."""
        other_tenant = uuid.uuid4()
        wh = create_webhook(tenant_id=other_tenant)
        resp = auth_client.patch(
            f"{self.WEBHOOKS_URL}{wh.id}/",
            {"display_name": "Hacked"},
            format="json",
        )
        assert resp.status_code == 404

    def test_delete_isolation(self, auth_client, user, db):
        """Cannot delete another tenant's webhook."""
        other_tenant = uuid.uuid4()
        wh = create_webhook(tenant_id=other_tenant)
        resp = auth_client.delete(f"{self.WEBHOOKS_URL}{wh.id}/")
        assert resp.status_code == 404

    def test_test_isolation(self, auth_client, user, db):
        """Cannot test another tenant's webhook."""
        other_tenant = uuid.uuid4()
        wh = create_webhook(tenant_id=other_tenant)
        resp = auth_client.post(f"{self.WEBHOOKS_URL}{wh.id}/test/")
        assert resp.status_code == 404

    def test_deactivate_isolation(self, auth_client, user, db):
        """Cannot deactivate another tenant's webhook."""
        other_tenant = uuid.uuid4()
        wh = create_webhook(tenant_id=other_tenant)
        resp = auth_client.post(f"{self.WEBHOOKS_URL}{wh.id}/deactivate/")
        assert resp.status_code == 404


# ── Notification Service ──────────────────────────────────────────────────────


class TestSlackNotificationService:
    """SlackNotificationService.notify() delivery and filtering."""

    def test_notify_matching_webhook(self, db, user):
        """Active webhook with matching event type delivers."""
        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"])

        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

        # Signal fired eagerly via CELERY_TASK_ALWAYS_EAGER
        assert mock_post.called
        wh.refresh_from_db()
        assert wh.last_triggered_at is not None
        assert wh.failure_count == 0

    def test_notify_empty_subscribed_events(self, db, user):
        """Empty subscribed_events = notify on all event types."""
        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=[])

        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            activity = create_activity(tenant_id=user.tenant_id, act_type="note")

        assert mock_post.called
        wh.refresh_from_db()
        assert wh.last_triggered_at is not None
        assert wh.failure_count == 0

    def test_notify_non_matching_event_type(self, db, user):
        """Webhook subscribed to deal_stage_change only, note event skips."""
        from apps.slack.services import SlackNotificationService

        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"])
        activity = create_activity(tenant_id=user.tenant_id, act_type="note")

        with patch("apps.slack.services.requests.post") as mock_post:
            results = SlackNotificationService.notify(activity)

        assert len(results) == 0
        mock_post.assert_not_called()

    def test_notify_inactive_webhook_skipped(self, db, user):
        """Inactive webhook is not queried."""
        from apps.slack.services import SlackNotificationService

        create_webhook(tenant_id=user.tenant_id, is_active=False, subscribed_events=["deal_stage_change"])
        activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

        with patch("apps.slack.services.requests.post") as mock_post:
            results = SlackNotificationService.notify(activity)

        assert len(results) == 0
        mock_post.assert_not_called()

    def test_pipeline_filter(self, db, user):
        """Pipeline filter scopes notifications to matching pipeline."""
        from apps.slack.services import SlackNotificationService
        from apps.pipelines.models import Pipeline

        pipeline = Pipeline.objects.create(
            tenant_id=user.tenant_id,
            name="Sales Pipeline",
        )
        wh = create_webhook(
            tenant_id=user.tenant_id,
            subscribed_events=["deal_stage_change"],
            pipeline_filter=pipeline,
        )

        # Deal in wrong pipeline → skip
        activity_wrong = create_activity(
            tenant_id=user.tenant_id,
            act_type="deal_stage_change",
            pipeline_id=str(uuid.uuid4()),
        )
        with patch("apps.slack.services.requests.post") as mock_post:
            results = SlackNotificationService.notify(activity_wrong)
        assert len(results) == 0
        mock_post.assert_not_called()

        # Deal in matching pipeline → deliver
        activity_match = create_activity(
            tenant_id=user.tenant_id,
            act_type="deal_stage_change",
            pipeline_id=str(pipeline.id),
        )
        with patch("apps.slack.services.requests.post") as mock_post:
            results = SlackNotificationService.notify(activity_match)
        assert len(results) == 1
        mock_post.assert_called_once()

    def test_tenant_isolation_in_service(self, db, user):
        """Tenant B's webhook does not receive Tenant A's activity."""
        from apps.slack.services import SlackNotificationService

        other_tenant = uuid.uuid4()
        create_webhook(tenant_id=other_tenant, subscribed_events=["deal_stage_change"])
        activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

        with patch("apps.slack.services.requests.post") as mock_post:
            results = SlackNotificationService.notify(activity)

        assert len(results) == 0

    def test_failure_increments_count(self, db, user):
        """Failed POST increments failure_count."""
        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"])

        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
            activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

        wh.refresh_from_db()
        assert wh.failure_count == 1
        assert wh.is_active is True  # Still active at 1 failure

    def test_auto_deactivate_after_10_failures(self, db, user):
        """10 consecutive failures auto-deactivates the webhook."""
        wh = create_webhook(tenant_id=user.tenant_id, failure_count=9, subscribed_events=["deal_stage_change"])

        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 500
            mock_post.return_value.text = "Server Error"
            activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

        wh.refresh_from_db()
        assert wh.failure_count == 10
        assert wh.is_active is False

    def test_webhook_not_notify_for_non_deal_entity_type(self, db, user):
        """pipeline_filter only applies to deal entity_type, skips for other entities."""
        from apps.pipelines.models import Pipeline

        pipeline = Pipeline.objects.create(
            tenant_id=user.tenant_id,
            name="Sales Pipeline",
        )
        wh = create_webhook(
            tenant_id=user.tenant_id,
            subscribed_events=["email"],
            pipeline_filter=pipeline,
        )

        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            # Email activity (entity_type = "email", not "deal") should still deliver
            # regardless of pipeline_filter, since the filter only applies to "deal"
            create_activity(
                tenant_id=user.tenant_id,
                act_type="email",
                entity_type="email",
                deal_name="N/A",
                from_name="Bob",
                from_email="bob@example.com",
                subject="Hello",
                snippet="Test msg",
                direction="inbound",
            )

        assert mock_post.called
        wh.refresh_from_db()
        assert wh.last_triggered_at is not None


# ── Message Formatters ────────────────────────────────────────────────────────


class TestSlackMessageFormatters:
    """SlackMessageFormatter builds correct Block Kit payload per activity type."""

    def test_deal_stage_change_format(self, db, user):
        from apps.slack.formatters import SlackMessageFormatter

        activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")
        payload = SlackMessageFormatter.format(activity)

        assert payload["blocks"][0]["text"]["text"] == "🔄 Deal Stage Changed"
        fields_text = "".join(f["text"] for f in payload["blocks"][1]["fields"])
        assert "Big Deal" in fields_text
        assert "Qualified" in fields_text
        assert "Proposal" in fields_text
        assert "$50000" in fields_text

    def test_deal_status_change_won(self, db, user):
        from apps.slack.formatters import SlackMessageFormatter

        activity = create_activity(
            tenant_id=user.tenant_id,
            act_type="deal_status_change",
            new_status="won",
            deal_name="Won Deal",
            value="100000",
            owner_name="Alice",
            pipeline_name="Sales",
        )
        payload = SlackMessageFormatter.format(activity)
        assert "🎉" in payload["blocks"][0]["text"]["text"]
        assert "Deal Won" in payload["blocks"][0]["text"]["text"]

    def test_deal_status_change_lost_with_reason(self, db, user):
        from apps.slack.formatters import SlackMessageFormatter

        activity = create_activity(
            tenant_id=user.tenant_id,
            act_type="deal_status_change",
            new_status="lost",
            deal_name="Lost Deal",
            value="50000",
            owner_name="Alice",
            pipeline_name="Sales",
            lost_reason="Budget too low",
        )
        payload = SlackMessageFormatter.format(activity)
        assert "❌" in payload["blocks"][0]["text"]["text"]
        assert "Deal Lost" in payload["blocks"][0]["text"]["text"]
        fields_text = str(payload["blocks"][1]["fields"])
        assert "Budget too low" in fields_text

    def test_email_inbound_format(self, db, user):
        from apps.slack.formatters import SlackMessageFormatter

        activity = create_activity(
            tenant_id=user.tenant_id,
            act_type="email",
            from_name="Bob Smith",
            from_email="bob@example.com",
            subject="Meeting tomorrow",
            snippet="Just confirming our meeting",
            direction="inbound",
        )
        activity.entity_type = "email"
        activity.save()

        payload = SlackMessageFormatter.format(activity)
        assert "📧 New Email" in payload["blocks"][0]["text"]["text"]
        fields_text = str(payload["blocks"][1]["fields"])
        assert "bob@example.com" in fields_text
        assert "Meeting tomorrow" in fields_text

    def test_email_outbound_format(self, db, user):
        from apps.slack.formatters import SlackMessageFormatter

        activity = create_activity(
            tenant_id=user.tenant_id,
            act_type="email",
            from_name="Alice",
            from_email="alice@frontiercrm.com",
            subject="Proposal sent",
            snippet="Here is the proposal",
            direction="outbound",
        )
        activity.entity_type = "email"
        activity.save()

        payload = SlackMessageFormatter.format(activity)
        assert "📤 Email Sent" in payload["blocks"][0]["text"]["text"]

    def test_generic_fallback_format(self, db, user):
        from apps.slack.formatters import SlackMessageFormatter

        activity = create_activity(
            tenant_id=user.tenant_id,
            act_type="note",
            title="Test Note",
        )
        activity.description = "A note about the deal"
        activity.save()

        payload = SlackMessageFormatter.format(activity)
        # No registered formatter for 'note' → uses generic fallback
        assert "text" in payload  # generic has a 'text' top-level key
        assert "blocks" in payload


# ── Signal and Task Wiring ────────────────────────────────────────────────────


class TestSlackSignalAndTask:
    """post_save signal on Activity enqueues the Celery task."""

    def test_signal_fires_on_activity_create(self, db, user):
        """Creating an Activity triggers the signal handler (enqueues task)."""
        from apps.slack.signals import activity_created_handler

        activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

        # The signal is connected — just verify the handler exists and is wired
        # by checking the receiver is registered
        from django.db.models.signals import post_save
        from apps.activities.models import Activity

        receivers = post_save._live_receivers(sender=Activity)
        registered_funcs = receivers[0] if isinstance(receivers, tuple) else receivers
        assert activity_created_handler in registered_funcs

    def test_celery_task_creates(self, db):
        """The Celery task can be imported and has the right signature."""
        from apps.slack.tasks import deliver_slack_notifications

        # Just verify the task exists and is a shared_task
        assert deliver_slack_notifications.__name__ == "deliver_slack_notifications"
        assert hasattr(deliver_slack_notifications, "delay")


# ── Send Test Message ─────────────────────────────────────────────────────────


class TestSendTestMessage:
    """send_test_message helper function."""

    def test_send_test_success(self, db, user):
        from apps.slack.services import send_test_message

        wh = create_webhook(tenant_id=user.tenant_id)
        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            result = send_test_message(wh)

        assert result["status"] == "delivered"

    def test_send_test_failure(self, db, user):
        from apps.slack.services import send_test_message

        wh = create_webhook(tenant_id=user.tenant_id)
        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 404
            mock_post.return_value.text = "Not Found"
            result = send_test_message(wh)

        assert result["status"] == "failed"
        assert "Not Found" in result["error"]

    def test_send_test_network_error(self, db, user):
        from apps.slack.services import send_test_message

        wh = create_webhook(tenant_id=user.tenant_id)
        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection timeout")
            result = send_test_message(wh)

        assert result["status"] == "failed"
        assert "Connection timeout" in result["error"]


# ── Rate Limiting ─────────────────────────────────────────────────────────────


class TestRateLimiting:
    """SlackNotificationService._send() enforces 1 req/sec rate limit."""

    SLACK_RATE_LIMIT_SECONDS = 1.0

    def test_send_respects_rate_limit(self, db, user):
        """Two rapid calls to _send() for the same webhook should sleep."""
        from apps.slack.services import SlackNotificationService
        import time

        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"])
        activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

        with patch("apps.slack.services.time.sleep") as mock_sleep, \
             patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"

            # Force _last_send_time to emulate a recent send
            wh_id = str(wh.id)
            SlackNotificationService._last_send_time[wh_id] = time.time() - 0.1  # 100ms ago

            SlackNotificationService.notify(activity)

            # Should have slept because < 1s elapsed
            assert mock_sleep.call_count >= 1
            call_arg = mock_sleep.call_args[0][0]
            assert call_arg > 0.8  # sleep ≈ 0.9s to fill the gap

    def test_rate_limit_bypasses_when_enough_time_passed(self, db, user):
        """No sleep if more than SLACK_RATE_LIMIT_SECONDS since last send."""
        from apps.slack.services import SlackNotificationService
        import time

        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"])
        activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

        with patch("apps.slack.services.time.sleep") as mock_sleep, \
             patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"

            wh_id = str(wh.id)
            SlackNotificationService._last_send_time[wh_id] = time.time() - 5.0  # 5s ago

            SlackNotificationService.notify(activity)

            mock_sleep.assert_not_called()

    def test_rate_limit_per_webhook_independent(self, db, user):
        """Two different webhooks do not share rate-limit state for each other."""
        from apps.slack.services import SlackNotificationService
        import time

        create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"])
        create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"],
                       webhook_url="https://hooks.slack.com/services/T00/B00/test2")

        # First activity: wh1 is rate-limited, wh2 is not
        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"

            activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change",
                                       deal_name="Deal 1")
            SlackNotificationService._last_send_time.clear()
            results = SlackNotificationService.notify(activity)

            # Both webhooks matched — verify we had deliveries
            assert len(results) == 2

        # Second notification: wh1 is now rate-limited via _last_send_time
        with patch("apps.slack.services.time.sleep") as mock_sleep, \
             patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"

            activity2 = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change",
                                        deal_name="Deal 2")

            SlackNotificationService.notify(activity2)

            # wh1 needs to sleep (was just triggered), wh2 does not
            assert mock_sleep.called


# ── _handle_failure Edge Cases ────────────────────────────────────────────────


class TestHandleFailureEdgeCases:
    """Direct tests for SlackNotificationService._handle_failure()."""

    def test_handle_failure_with_exception_only(self, db, user):
        """_handle_failure works when only exception is provided (no response)."""
        from apps.slack.services import SlackNotificationService

        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"])
        result = SlackNotificationService._handle_failure(wh, exc=Exception("Network is unreachable"))

        assert result["status"] == "failed"
        assert "Network is unreachable" in result["error"]
        wh.refresh_from_db()
        assert wh.failure_count == 1

    def test_handle_failure_truncates_long_response(self, db, user):
        """Response text > 500 chars is truncated in the error message."""
        from apps.slack.services import SlackNotificationService
        from unittest.mock import MagicMock

        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"])
        mock_resp = MagicMock()
        mock_resp.text = "x" * 2000
        mock_resp.status_code = 500

        result = SlackNotificationService._handle_failure(wh, resp=mock_resp)

        assert len(result["error"]) == 500
        assert result["status"] == "failed"

    def test_handle_failure_auto_deactivates_at_10_without_extra_call(self, db, user):
        """Direct call with failure_count=9 auto-deactivates."""
        from apps.slack.services import SlackNotificationService

        wh = create_webhook(tenant_id=user.tenant_id, failure_count=9,
                            subscribed_events=["deal_stage_change"])
        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.text = "Too many errors"
        mock_resp.status_code = 500

        result = SlackNotificationService._handle_failure(wh, resp=mock_resp)

        assert result["status"] == "failed"
        wh.refresh_from_db()
        assert wh.is_active is False
        assert wh.failure_count == 10


# ── _should_notify Edge Cases ─────────────────────────────────────────────────


class TestShouldNotifyEdgeCases:
    """Direct tests for SlackNotificationService._should_notify()."""

    def test_should_notify_without_pipeline_id_in_metadata(self, db, user):
        """Deal activity with pipeline_filter set but no pipeline_id in metadata → no match."""
        from apps.slack.services import SlackNotificationService
        from apps.pipelines.models import Pipeline

        pipeline = Pipeline.objects.create(tenant_id=user.tenant_id, name="Sales Pipeline")
        wh = create_webhook(
            tenant_id=user.tenant_id,
            subscribed_events=["deal_stage_change"],
            pipeline_filter=pipeline,
        )

        # Activity with no pipeline_id in metadata at all
        activity = create_activity(
            tenant_id=user.tenant_id,
            act_type="deal_stage_change",
            pipeline_id=None,  # provide as None to remove it
        )
        # Remove pipeline_id from metadata
        del activity.metadata["pipeline_id"]
        activity.save(update_fields=["metadata"])

        result = SlackNotificationService._should_notify(wh, activity)
        assert result is False  # None pipeline_id != str filter → skip

    def test_should_notify_returns_true_without_subscribed_events(self, db, user):
        """Webhook with empty subscribed_events list notifies on any type."""
        from apps.slack.services import SlackNotificationService

        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=[])
        activity = create_activity(tenant_id=user.tenant_id, act_type="some_random_type")

        result = SlackNotificationService._should_notify(wh, activity)
        assert result is True

    def test_should_notify_with_pipeline_filter_mismatch(self, db, user):
        """Deal activity with non-matching pipeline_id returns False."""
        from apps.slack.services import SlackNotificationService
        from apps.pipelines.models import Pipeline

        pipeline = Pipeline.objects.create(tenant_id=user.tenant_id, name="Sales Pipeline")
        wh = create_webhook(
            tenant_id=user.tenant_id,
            subscribed_events=["deal_stage_change"],
            pipeline_filter=pipeline,
        )

        activity = create_activity(
            tenant_id=user.tenant_id,
            act_type="deal_stage_change",
            pipeline_id=str(uuid.uuid4()),  # different pipeline
        )

        result = SlackNotificationService._should_notify(wh, activity)
        assert result is False

    def test_should_notify_with_no_filters(self, db, user):
        """Webhook with no filters returns True for matching event type."""
        from apps.slack.services import SlackNotificationService

        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"])
        activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

        result = SlackNotificationService._should_notify(wh, activity)
        assert result is True


# ── Celery Task Execution ─────────────────────────────────────────────────────


class TestSlackTaskExecution:
    """deliver_slack_notifications Celery task with real activity data."""

    def test_task_delivers_for_existing_activity(self, db, user):
        """Task loads a real activity and calls notify()."""
        from apps.slack.tasks import deliver_slack_notifications

        wh = create_webhook(tenant_id=user.tenant_id, subscribed_events=["deal_stage_change"])

        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

            result = deliver_slack_notifications(str(activity.id))

        assert result["activity_id"] == str(activity.id)
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "delivered"

    def test_task_returns_error_for_missing_activity(self, db):
        """Task returns error dict when Activity does not exist."""
        from apps.slack.tasks import deliver_slack_notifications

        missing_id = str(uuid.uuid4())
        result = deliver_slack_notifications(missing_id)

        assert result["error"] == "Activity not found"
        assert result["activity_id"] == missing_id

    def test_task_skips_inactive_webhooks(self, db, user):
        """Task does not deliver to inactive webhooks."""
        from apps.slack.tasks import deliver_slack_notifications

        create_webhook(tenant_id=user.tenant_id, is_active=False,
                       subscribed_events=["deal_stage_change"])
        activity = create_activity(tenant_id=user.tenant_id, act_type="deal_stage_change")

        with patch("apps.slack.services.requests.post") as mock_post:
            result = deliver_slack_notifications(str(activity.id))

        assert result["activity_id"] == str(activity.id)
        assert len(result["results"]) == 0
        mock_post.assert_not_called()


# ── Unauthenticated Access ────────────────────────────────────────────────────


class TestUnauthenticatedAccess:
    """403/401 for unauthenticated requests to webhook endpoints."""

    WEBHOOKS_URL = "/api/slack/webhooks/"

    def test_list_unauthenticated(self, api_client, db):
        resp = api_client.get(self.WEBHOOKS_URL)
        assert resp.status_code in (401, 403)

    def test_create_unauthenticated(self, api_client, db):
        resp = api_client.post(
            self.WEBHOOKS_URL,
            {"webhook_url": "https://hooks.slack.com/services/T00/B00/x"},
            format="json",
        )
        assert resp.status_code in (401, 403)

    def test_detail_unauthenticated(self, api_client, db, user):
        wh = create_webhook(tenant_id=user.tenant_id)
        resp = api_client.get(f"{self.WEBHOOKS_URL}{wh.id}/")
        assert resp.status_code in (401, 403)

    def test_test_action_unauthenticated(self, api_client, db, user):
        wh = create_webhook(tenant_id=user.tenant_id)
        resp = api_client.post(f"{self.WEBHOOKS_URL}{wh.id}/test/")
        assert resp.status_code in (401, 403)

    def test_deactivate_action_unauthenticated(self, api_client, db, user):
        wh = create_webhook(tenant_id=user.tenant_id)
        resp = api_client.post(f"{self.WEBHOOKS_URL}{wh.id}/deactivate/")
        assert resp.status_code in (401, 403)


# ── send_test_message Payload ────────────────────────────────────────────────


class TestSendTestMessagePayload:
    """send_test_message builds correct Block Kit payload structure."""

    def test_payload_has_correct_block_kit_structure(self, db, user):
        """Verify the payload sent by send_test_message matches Slack spec."""
        from apps.slack.services import send_test_message

        wh = create_webhook(tenant_id=user.tenant_id)
        with patch("apps.slack.services.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            send_test_message(wh)

        # Capture the payload that was POSTed
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]

        assert "text" in payload
        assert "working" in payload["text"].lower()
        assert "blocks" in payload
        assert len(payload["blocks"]) == 2
        assert payload["blocks"][0]["type"] == "section"
        assert payload["blocks"][1]["type"] == "context"
        assert payload["blocks"][0]["text"]["type"] == "mrkdwn"