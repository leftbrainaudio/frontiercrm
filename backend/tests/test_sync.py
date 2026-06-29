"""Tests for the Gmail sync engine — adapter, MIME, client, contact linker, API."""
from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import ANY, MagicMock, patch

import pytest
from django.utils import timezone as tz

from apps.sync.adapters.base import AttachmentInfo, DeltaResult, EmailMessage, EmailSendResult, OutgoingEmail
from apps.sync.adapters.gmail.adapter import GmailAdapter
from apps.sync.adapters.gmail.client import GmailApiClient, GmailApiError, GmailAuthError, GmailNotFoundError, GmailRateLimitError, SyncLock
from apps.sync.adapters.gmail.contact_linker import ContactLinker, LinkingResult
from apps.sync.adapters.gmail.mime_builder import build_rfc2822_message
from apps.sync.adapters.gmail.mime_parser import parse_gmail_message, normalize_subject, _parse_address_list, _parse_from_header
from apps.sync.adapters.gmail.thread_matcher import ThreadMatcher
from apps.sync.models import SyncConnection, SyncState


# ═══════════════════════════════════════════════════════════════════════════════
# MIME Parser Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMimeParser:
    """Gmail API response → EmailMessage dataclass conversion."""

    def build_gmail_response(self, **overrides):
        """Build a realistic Gmail API message response."""
        default = {
            "id": "msg_123",
            "threadId": "thread_abc",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "Hi, here is the proposal...",
            "sizeEstimate": 12345,
            "payload": {
                "mimeType": "multipart/alternative",
                "headers": [
                    {"name": "From", "value": "Alice <alice@acme.com>"},
                    {"name": "To", "value": "bob@example.com"},
                    {"name": "Subject", "value": "Proposal for Q3"},
                    {"name": "Date", "value": "Mon, 29 Jun 2026 10:30:00 +0000"},
                    {"name": "Message-ID", "value": "<abc123@mail.gmail.com>"},
                    {"name": "Cc", "value": "cc@example.com"},
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": base64.b64encode(b"Hi, here is the proposal...").decode("utf-8")},
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": base64.b64encode(b"<p>Hi, here is the proposal...</p>").decode("utf-8")},
                    },
                ],
            },
            "internalDate": "1759102200000",
        }
        default.update(overrides)
        return default

    def test_parse_full_message(self):
        raw = self.build_gmail_response()
        msg = parse_gmail_message(raw)

        assert msg.provider_id == "msg_123"
        assert msg.thread_id == "thread_abc"
        assert msg.message_id == "<abc123@mail.gmail.com>"
        assert msg.subject == "Proposal for Q3"
        assert msg.from_address == "alice@acme.com"
        assert msg.from_name == "Alice"
        assert msg.to_addresses == ["bob@example.com"]
        assert msg.cc_addresses == ["cc@example.com"]
        assert msg.body_text == "Hi, here is the proposal..."
        assert msg.body_html == "<p>Hi, here is the proposal...</p>"
        assert msg.snippet == "Hi, here is the proposal..."
        assert not msg.is_read  # UNREAD label present
        assert not msg.is_starred
        assert msg.labels == ["INBOX", "UNREAD"]
        assert msg.size_estimate == 12345
        assert msg.sent_at is not None

    def test_parse_read_message(self):
        raw = self.build_gmail_response(labelIds=["INBOX"])
        msg = parse_gmail_message(raw)
        assert msg.is_read  # No UNREAD label

    def test_parse_starred_message(self):
        raw = self.build_gmail_response(labelIds=["INBOX", "STARRED"])
        msg = parse_gmail_message(raw)
        assert msg.is_starred

    def test_parse_no_subject(self):
        raw = self.build_gmail_response()
        raw["payload"]["headers"] = [
            h for h in raw["payload"]["headers"] if h["name"] != "Subject"
        ]
        msg = parse_gmail_message(raw)
        assert msg.subject == "(no subject)"

    def test_parse_simple_text_message(self):
        """Handle messages without parts — a single text body."""
        raw = {
            "id": "msg_456",
            "threadId": "thread_def",
            "labelIds": [],
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "From", "value": "bob@example.com"},
                    {"name": "To", "value": "alice@acme.com"},
                    {"name": "Subject", "value": "Re: Proposal"},
                    {"name": "Date", "value": "Tue, 30 Jun 2026 14:00:00 +0000"},
                    {"name": "Message-ID", "value": "<def456@mail.gmail.com>"},
                ],
                "body": {"data": base64.b64encode(b"Sure, sounds good!").decode("utf-8")},
            },
            "internalDate": "1759189200000",
        }
        msg = parse_gmail_message(raw)
        assert msg.body_text == "Sure, sounds good!"
        assert msg.body_html is None

    def test_parse_no_date(self):
        raw = self.build_gmail_response()
        raw["payload"]["headers"] = [
            h for h in raw["payload"]["headers"] if h["name"] != "Date"
        ]
        raw.pop("internalDate", None)
        msg = parse_gmail_message(raw)
        assert msg.sent_at is None
        assert msg.received_at is None

    def test_parse_address_helpers(self):
        assert _parse_from_header("Alice <alice@acme.com>") == ("alice@acme.com", "Alice")
        assert _parse_from_header("<alice@acme.com>") == ("alice@acme.com", None)
        assert _parse_from_header("alice@acme.com") == ("alice@acme.com", None)
        assert _parse_from_header("") == ("", None)

        assert _parse_address_list("a@a.com, b@b.com") == ["a@a.com", "b@b.com"]
        assert _parse_address_list("") == []
        assert _parse_address_list("Alice <alice@acme.com>, Bob <bob@b.com>") == [
            "alice@acme.com", "bob@b.com"
        ]

    def test_normalize_subject(self):
        assert normalize_subject("Re: Proposal") == "proposal"
        assert normalize_subject("Fwd: Hello") == "hello"
        assert normalize_subject("  Meeting   Tomorrow  ") == "meeting tomorrow"
        assert normalize_subject("Re: Fwd: Chain") == "chain"
        assert normalize_subject("") == ""
        assert normalize_subject("NoPrefix") == "noprefix"


# ═══════════════════════════════════════════════════════════════════════════════
# MIME Builder Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMimeBuilder:
    """RFC 2822 MIME composition."""

    def test_build_simple_message(self):
        msg = OutgoingEmail(
            to_addresses=["alice@acme.com"],
            subject="Hello",
            body_text="Hi Alice",
            body_html="<p>Hi Alice</p>",
        )
        mime = build_rfc2822_message(msg)
        assert mime["To"] == "alice@acme.com"
        assert mime["Subject"] == "Hello"
        assert mime["Message-ID"] is not None
        assert mime["Date"] is not None
        # Should be multipart/mixed
        assert mime.get_content_type().startswith("multipart/mixed")

    def test_build_message_with_cc_bcc(self):
        msg = OutgoingEmail(
            to_addresses=["alice@acme.com"],
            cc_addresses=["cc@acme.com"],
            bcc_addresses=["bcc@acme.com"],
            subject="Team Update",
            body_text="Updates",
        )
        mime = build_rfc2822_message(message=msg)
        assert mime["Cc"] == "cc@acme.com"
        assert mime["Bcc"] == "bcc@acme.com"

    def test_build_empty_body(self):
        msg = OutgoingEmail(
            to_addresses=["alice@acme.com"],
            subject="No body",
        )
        mime = build_rfc2822_message(message=msg)
        assert mime is not None  # Should not crash

    def test_base64_encoding(self):
        msg = OutgoingEmail(
            to_addresses=["test@test.com"],
            subject="Test",
            body_text="Hello world",
        )
        mime = build_rfc2822_message(message=msg)
        # The message should be serializable and encodable
        raw_bytes = mime.as_bytes()
        encoded = base64.urlsafe_b64encode(raw_bytes).decode("ascii")
        assert len(encoded) > 0
        # Decode back and verify body is present in MIME structure
        decoded = base64.urlsafe_b64decode(encoded)
        # The text body will be base64-encoded within the MIME, so verify
        # the MIME structure is valid and contains our subject header
        assert b"Subject: Test" in decoded
        assert b"text/plain" in decoded

    def test_attachments_in_mime(self):
        """MIME builder includes attachments with base64 and Content-Disposition."""
        attachment = AttachmentInfo(
            attachment_id="att_1",
            filename="report.pdf",
            mime_type="application/pdf",
            size=1024,
            storage_key="fake-pdf-content",
        )

        msg = OutgoingEmail(
            to_addresses=["recipient@acme.com"],
            subject="With attachment",
            body_text="Please find the report attached.",
            attachments=[attachment],
        )

        mime = build_rfc2822_message(message=msg)
        raw = mime.as_string()

        # Should be multipart/mixed (outermost)
        assert "multipart/mixed" in mime.get_content_type()

        # Attachment should have Content-Disposition
        assert 'attachment; filename="report.pdf"' in raw
        # Content-Type should include application/pdf
        assert "application/pdf" in raw


# ═══════════════════════════════════════════════════════════════════════════════
# GmailApiClient Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestGmailApiClient:
    """Client wrapper — auth, rate limiting, retry."""

    @patch("apps.sync.adapters.gmail.client.requests.request")
    def test_get_success(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{"emailAddress": "test@test.com"}'
        mock_resp.json.return_value = {"emailAddress": "test@test.com"}
        mock_request.return_value = mock_resp

        client = GmailApiClient(access_token="test_token")
        result = client.get("profile")

        assert result["emailAddress"] == "test@test.com"
        mock_request.assert_called_once()

    @patch("apps.sync.adapters.gmail.client.requests.request")
    def test_token_refresh_and_retry(self, mock_request):
        """Should refresh token on 401 and retry."""
        resp_401 = MagicMock()
        resp_401.status_code = 401
        resp_401.content = b"unauthorized"

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.content = b'{"emailAddress": "test@test.com"}'
        resp_200.json.return_value = {"emailAddress": "test@test.com"}

        mock_request.side_effect = [resp_401, resp_200]

        with patch.object(GmailApiClient, "refresh_access_token", return_value=True):
            client = GmailApiClient(access_token="old_token", refresh_token="refresh_token")
            result = client.get("profile")

        assert result["emailAddress"] == "test@test.com"
        assert mock_request.call_count == 2

    @patch("apps.sync.adapters.gmail.client.requests.request")
    def test_404_raises_not_found(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.content = b"not found"
        mock_request.return_value = mock_resp

        client = GmailApiClient(access_token="test_token")
        with pytest.raises(GmailNotFoundError):
            client.get("messages/invalid")

    @patch("apps.sync.adapters.gmail.client.requests.request")
    def test_429_rate_limit_retry(self, mock_request):
        """Should retry with backoff on 429."""
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "1"}
        resp_429.content = b"rate limited"

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.content = b"{}"
        resp_200.json.return_value = {}

        mock_request.side_effect = [resp_429, resp_200]

        client = GmailApiClient(access_token="test_token")
        client.MAX_RETRIES = 2  # Reduce for test speed
        result = client.get("messages")

        assert result == {}
        assert mock_request.call_count == 2

    @patch("apps.sync.adapters.gmail.client.requests.request")
    def test_server_error_retry(self, mock_request):
        """Should retry on 500 with exponential backoff."""
        resp_500 = MagicMock()
        resp_500.status_code = 500
        resp_500.content = b"server error"

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.content = b"{}"
        resp_200.json.return_value = {}

        mock_request.side_effect = [resp_500, resp_200]

        client = GmailApiClient(access_token="test_token")
        client.MAX_RETRIES = 2
        result = client.get("messages")

        assert result == {}
        assert mock_request.call_count == 2

    def test_backoff_calculation(self):
        client = GmailApiClient(access_token="token")
        assert client._get_backoff(1) == 5     # 5 * 2^0 = 5
        assert client._get_backoff(2) == 10    # 5 * 2^1 = 10
        assert client._get_backoff(3) == 20    # 5 * 2^2 = 20
        assert client._get_backoff(4) == 40    # 5 * 2^3 = 40
        # Cap at max
        assert client._get_backoff(10) == 300  # Max

    @patch("apps.sync.adapters.gmail.client.requests.request")
    def test_post_success(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{"id": "sent_1"}'
        mock_resp.json.return_value = {"id": "sent_1"}
        mock_request.return_value = mock_resp

        client = GmailApiClient(access_token="token")
        result = client.post("messages/send", body={"raw": "encoded"})

        assert result["id"] == "sent_1"
        # Verify POST was called with Authorization header
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "POST"
        assert "Authorization" in kwargs["headers"]

    @patch("apps.sync.adapters.gmail.client.requests.request")
    def test_delete_returns_empty(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.content = b""
        mock_request.return_value = mock_resp

        client = GmailApiClient(access_token="token")
        result = client.delete("messages/msg_1/trash")

        assert result == {}
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "DELETE"

    @patch("apps.sync.adapters.gmail.client.requests.request")
    def test_daily_limit_exceeded_raises_error(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.content = b'{"error": "dailyLimitExceeded"}'
        mock_resp.text = '{"error": "dailyLimitExceeded"}'
        mock_request.return_value = mock_resp

        client = GmailApiClient(access_token="token")
        with pytest.raises(GmailRateLimitError, match="Daily API quota exceeded"):
            client.get("messages")

    @patch("apps.sync.adapters.gmail.client.requests.request")
    def test_all_retries_exhausted_raises_error(self, mock_request):
        """MAX_RETRIES exhausted on server error should raise GmailApiError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.content = b"server error"
        mock_request.return_value = mock_resp

        client = GmailApiClient(access_token="token")
        client.MAX_RETRIES = 2
        with pytest.raises(GmailApiError, match="Request failed after"):
            client.get("messages")

    @patch("apps.sync.adapters.gmail.client.requests.request")
    def test_refresh_access_token_no_refresh_token(self, mock_request):
        """refresh_access_token returns False when no refresh token set."""
        client = GmailApiClient(access_token="token")
        result = client.refresh_access_token()
        assert result is False
        mock_request.assert_not_called()

    @patch("apps.sync.adapters.gmail.client.requests.post")
    def test_refresh_access_token_success(self, mock_post):
        """Full refresh_access_token flow with successful token exchange."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "new_token"}
        mock_post.return_value = mock_resp

        client = GmailApiClient(access_token="old_token", refresh_token="refresh_token")
        result = client.refresh_access_token()

        assert result is True
        assert client.access_token == "new_token"

    @patch("apps.sync.adapters.gmail.client.requests.post")
    def test_refresh_access_token_failure(self, mock_post):
        """refresh_access_token returns False when token endpoint fails."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "invalid_grant"
        mock_post.return_value = mock_resp

        client = GmailApiClient(access_token="old_token", refresh_token="bad_refresh")
        result = client.refresh_access_token()

        assert result is False

    def test_quota_tracking(self):
        client = GmailApiClient(access_token="token")
        assert client.get_quota_used() == 0


# ═══════════════════════════════════════════════════════════════════════════════
# GmailAdapter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestGmailAdapter:
    """GmailAdapter — full adapter class."""

    def build_history_response(self):
        return {
            "history": [
                {
                    "id": "100001",
                    "messagesAdded": [
                        {"message": {"id": "msg_new_1", "threadId": "thread_1", "labelIds": ["INBOX", "UNREAD"]}}
                    ],
                },
                {
                    "id": "100002",
                    "messagesDeleted": [
                        {"message": {"id": "msg_deleted_1"}}
                    ],
                },
            ],
            "historyId": "12346",
        }

    def build_message_response(self, msg_id="msg_new_1", **overrides):
        result = {
            "id": msg_id,
            "threadId": "thread_1",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "Test snippet",
            "sizeEstimate": 500,
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "From", "value": "Alice <alice@acme.com>"},
                    {"name": "To", "value": "bob@example.com"},
                    {"name": "Subject", "value": "Test Email"},
                    {"name": "Date", "value": "Mon, 29 Jun 2026 10:30:00 +0000"},
                    {"name": "Message-ID", "value": f"<{msg_id}@mail.gmail.com>"},
                ],
                "body": {"data": base64.b64encode(b"Hello").decode("utf-8")},
            },
            "internalDate": "1759102200000",
        }
        result.update(overrides)
        return result

    def test_get_initial_cursor(self, monkeypatch):
        adapter = GmailAdapter(access_token="token")
        monkeypatch.setattr(
            adapter._client, "get",
            lambda path, params=None: {"historyId": "12345", "emailAddress": "test@test.com"},
        )
        cursor = adapter.get_initial_cursor()
        assert cursor["historyId"] == 12345
        assert "watch_expiration" in cursor

    def test_get_email_delta_no_cursor_triggers_full_sync(self, monkeypatch):
        """Passing None should trigger full sync."""
        adapter = GmailAdapter(access_token="token")

        def mock_get(path, params=None):
            if path == "messages":
                return {"messages": [{"id": "msg_1"}], "nextPageToken": None}
            if path.startswith("messages/"):
                return self.build_message_response(path.split("/")[-1])
            if path == "profile":
                return {"historyId": "50000"}
            if path == "history":
                return self.build_history_response()
            return {}

        monkeypatch.setattr(adapter._client, "get", mock_get)

        result = adapter.get_email_delta(None)
        assert isinstance(result, DeltaResult)
        assert len(result.items) > 0
        assert result.new_cursor.get("historyId") == 50000

    def test_delta_sync_returns_new_emails_and_deletions(self, monkeypatch):
        """Delta sync via history API returns EmailMessage items."""
        adapter = GmailAdapter(access_token="token")

        call_count = {"history": 0, "messages": 0}

        def mock_get(path, params=None):
            if path == "history":
                call_count["history"] += 1
                return self.build_history_response()
            if path == "messages/msg_new_1":
                call_count["messages"] += 1
                return self.build_message_response()
            if path == "messages/msg_deleted_1":
                call_count["messages"] += 1
                return self.build_message_response("msg_deleted_1")
            return {}

        monkeypatch.setattr(adapter._client, "get", mock_get)

        result = adapter._delta_sync(start_history_id=12345)

        assert isinstance(result, DeltaResult)
        assert len(result.items) >= 1
        assert "msg_deleted_1" in result.deleted_ids
        assert result.new_cursor.get("historyId") == 12346
        assert not result.full_resync_required

    def test_delta_sync_expired_history_returns_full_resync(self, monkeypatch):
        """HTTP 404 on history.list → full_resync_required."""
        from apps.sync.adapters.gmail.client import GmailNotFoundError

        adapter = GmailAdapter(access_token="token")

        def mock_get(path, params=None):
            if path == "history":
                raise GmailNotFoundError("History expired")
            return {}

        monkeypatch.setattr(adapter._client, "get", mock_get)

        result = adapter.get_email_delta({"historyId": 1})
        assert result.full_resync_required
        assert len(result.items) == 0

    def test_send_email(self, monkeypatch):
        adapter = GmailAdapter(access_token="token")

        def mock_post(path, body=None):
            return {"id": "sent_123", "threadId": "thread_abc"}

        monkeypatch.setattr(adapter._client, "post", mock_post)

        result = adapter.send_email(
            OutgoingEmail(
                to_addresses=["alice@acme.com"],
                subject="Hello",
                body_text="Hi",
            )
        )
        assert isinstance(result, EmailSendResult)
        assert result.provider_id == "sent_123"
        assert result.thread_id == "thread_abc"

    def test_mark_read(self, monkeypatch):
        adapter = GmailAdapter(access_token="token")
        calls = []

        def mock_post(path, body=None):
            calls.append((path, body))
            return {}

        monkeypatch.setattr(adapter._client, "post", mock_post)

        adapter.mark_read("msg_1", is_read=True)
        assert len(calls) == 1
        assert calls[0][1] == {"removeLabelIds": ["UNREAD"]}

        adapter.mark_read("msg_1", is_read=False)
        assert len(calls) == 2
        assert calls[1][1] == {"addLabelIds": ["UNREAD"]}

    def test_validate_connection_valid(self, monkeypatch):
        adapter = GmailAdapter(access_token="token")
        monkeypatch.setattr(
            adapter._client, "get",
            lambda path, params=None: {"emailAddress": "test@test.com"},
        )
        status = adapter.validate_connection()
        assert status.is_valid
        assert status.account_email == "test@test.com"

    def test_validate_connection_expired(self, monkeypatch):
        adapter = GmailAdapter(access_token="token")
        monkeypatch.setattr(
            adapter._client, "get",
            lambda path, params=None: (_ for _ in ()).throw(GmailAuthError("expired")),
        )
        status = adapter.validate_connection()
        assert not status.is_valid
        assert status.error == "token_expired"

    def test_refresh_token_success(self, monkeypatch):
        adapter = GmailAdapter(access_token="old_token", refresh_token="rtoken")
        monkeypatch.setattr(adapter._client, "refresh_access_token", lambda: True)
        # Set access_token attribute directly after mocking
        adapter._client._access_token = "new_token"

        result = adapter.refresh_token()
        assert result.success
        assert result.access_token == "new_token"

    def test_move_to_trash(self, monkeypatch):
        adapter = GmailAdapter(access_token="token")
        calls = []

        def mock_post(path, body=None):
            calls.append((path, body))
            return {}

        monkeypatch.setattr(adapter._client, "post", mock_post)

        adapter.move_to_trash("msg_1")
        assert len(calls) == 1
        assert calls[0][0] == "messages/msg_1/trash"

    def test_refresh_token_failure(self, monkeypatch):
        adapter = GmailAdapter(access_token="old_token", refresh_token="rtoken")
        monkeypatch.setattr(adapter._client, "refresh_access_token", lambda: False)

        result = adapter.refresh_token()
        assert not result.success
        assert result.error == "token_refresh_failed"

    def test_full_sync_respects_time_range(self, monkeypatch):
        """Full sync should query messages within the specified range."""
        adapter = GmailAdapter(access_token="token")

        def mock_get(path, params=None):
            if path == "messages":
                return {"messages": [{"id": "old_1"}, {"id": "old_2"}], "nextPageToken": None}
            if path.startswith("messages/"):
                return self.build_message_response(path.split("/")[-1])
            if path == "profile":
                return {"historyId": "99999"}
            return {}

        monkeypatch.setattr(adapter._client, "get", mock_get)

        result = adapter._full_sync_time_range("after:2026/01/01 before:2026/06/01")

        assert len(result.items) > 0
        assert result.new_cursor.get("historyId") == 99999
        assert result.has_more

    def test_delta_sync_pagination(self, monkeypatch):
        """Delta sync paginates through history using nextPageToken."""
        adapter = GmailAdapter(access_token="token")

        call_pages = iter([
            {
                "history": [
                    {"id": "1001", "messagesAdded": [{"message": {"id": "p1_msg_1", "threadId": "t1"}}]},
                ],
                "nextPageToken": "page2",
                "historyId": "20001",
            },
            {
                "history": [
                    {"id": "1002", "messagesAdded": [{"message": {"id": "p2_msg_2", "threadId": "t2"}}]},
                    {"id": "1003", "messagesDeleted": [{"message": {"id": "p2_del_1"}}]},
                ],
                "historyId": "20002",
            },
        ])

        def mock_get(path, params=None):
            if path == "history":
                page = next(call_pages)
                return page
            if path == "messages/p1_msg_1":
                return self.build_message_response("p1_msg_1")
            if path == "messages/p2_msg_2":
                return self.build_message_response("p2_msg_2")
            return {}

        monkeypatch.setattr(adapter._client, "get", mock_get)

        result = adapter._delta_sync(start_history_id=10000)

        # Should have items from both pages
        assert len(result.items) == 2
        assert "p2_del_1" in result.deleted_ids
        # Cursor should be the max historyId seen
        assert result.new_cursor.get("historyId") == 20002
        assert not result.full_resync_required

    def test_full_sync_pagination(self, monkeypatch):
        """Full sync paginates through messages using nextPageToken."""
        adapter = GmailAdapter(access_token="token")

        call_pages = iter([
            {
                "messages": [{"id": "fs_1"}, {"id": "fs_2"}],
                "nextPageToken": "page2",
            },
            {
                "messages": [{"id": "fs_3"}],
                "nextPageToken": None,
            },
        ])

        def mock_get(path, params=None):
            if path == "messages":
                page = next(call_pages)
                return page
            if path.startswith("messages/"):
                return self.build_message_response(path.split("/")[-1])
            if path == "profile":
                return {"historyId": "99999"}
            return {}

        monkeypatch.setattr(adapter._client, "get", mock_get)

        result = adapter._full_sync_time_range("after:2026/06/01")

        assert len(result.items) == 3
        assert result.new_cursor.get("historyId") == 99999
        assert result.has_more

    def test_delta_sync_label_updates(self, monkeypatch):
        """Delta sync processes labelAdded and labelRemoved records."""
        adapter = GmailAdapter(access_token="token")

        def mock_get(path, params=None):
            if path == "history":
                return {
                    "history": [
                        {
                            "id": "3001",
                            "labelsAdded": [
                                {"message": {"id": "label_add_msg", "threadId": "t1"}, "labelIds": ["STARRED"]},
                            ],
                            "labelsRemoved": [
                                {"message": {"id": "label_rem_msg", "threadId": "t2"}, "labelIds": ["UNREAD"]},
                            ],
                        },
                    ],
                    "historyId": "30001",
                }
            if path == "messages/label_add_msg":
                return self.build_message_response("label_add_msg", labelIds=["INBOX", "STARRED"])
            if path == "messages/label_rem_msg":
                return self.build_message_response("label_rem_msg", labelIds=["INBOX"])
            return {}

        monkeypatch.setattr(adapter._client, "get", mock_get)

        result = adapter._delta_sync(start_history_id=30000)

        assert len(result.items) >= 2
        assert result.new_cursor.get("historyId") == 30001
        assert not result.full_resync_required

    def test_fetch_and_convert_not_found(self, monkeypatch):
        """_fetch_and_convert returns None when message is not found."""
        from apps.sync.adapters.gmail.client import GmailNotFoundError

        adapter = GmailAdapter(access_token="token")

        def mock_get(path, params=None):
            if path == "messages/missing":
                raise GmailNotFoundError("Not found")
            return {}

        monkeypatch.setattr(adapter._client, "get", mock_get)

        result = adapter._fetch_and_convert("missing")
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# Contact Linker Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestContactLinker:
    """4-pass contact matching."""

    def test_match_by_email_direct(self, db, tenant_id):
        """Pass 1: Direct email match."""
        from apps.contacts.models import Contact

        contact = Contact.objects.create(
            tenant_id=tenant_id,
            first_name="Alice",
            last_name="Smith",
            email="alice@acme.com",
        )

        email_msg = EmailMessage(
            provider_id="msg_1",
            thread_id="thread_1",
            message_id="<1@mail.com>",
            subject="Hello",
            from_address="alice@acme.com",
            from_name="Alice Smith",
            to_addresses=["bob@test.com"],
            sent_at=tz.now(),
        )

        linker = ContactLinker(tenant_id=str(tenant_id))
        result = linker._match_by_email("alice@acme.com")
        assert result is not None
        assert result.id == contact.id

    def test_no_match_for_unknown_email(self, db, tenant_id):
        linker = ContactLinker(tenant_id=str(tenant_id))
        result = linker._match_by_email("unknown@nowhere.com")
        assert result is None

    def test_match_by_domain(self, db, tenant_id):
        """Pass 2: Domain match against accounts."""
        from apps.contacts.models import Account

        account = Account.objects.create(
            tenant_id=tenant_id,
            name="Acme Corp",
            domain="acme.com",
        )

        email_msg = EmailMessage(
            provider_id="msg_1",
            thread_id="thread_1",
            message_id="<1@mail.com>",
            subject="Hello",
            from_address="newguy@acme.com",
            from_name="New Guy",
            to_addresses=["bob@test.com"],
            sent_at=tz.now(),
        )

        linker = ContactLinker(tenant_id=str(tenant_id))
        result = linker._match_by_domain("newguy@acme.com")
        assert result is not None
        assert result.id == account.id

    def test_create_lead_from_email(self, db, tenant_id, user):
        """Pass 4: Create lead for unknown sender."""
        email_msg = EmailMessage(
            provider_id="msg_1",
            thread_id="thread_1",
            message_id="<1@mail.com>",
            subject="Hello",
            from_address="stranger@unknown.com",
            from_name="John Doe",
            to_addresses=["bob@test.com"],
            sent_at=tz.now(),
        )

        linker = ContactLinker(tenant_id=str(tenant_id), user_id=str(user.id))
        contact = linker._create_lead_from_email(email_msg)
        assert contact is not None
        assert contact.source == "email_inbound"
        assert contact.first_name == "John"
        assert contact.last_name == "Doe"
        assert contact.email == "stranger@unknown.com"

    def test_full_link_flow(self, db, tenant_id):
        """Full 4-pass linking via the link() method."""
        from apps.contacts.models import Contact
        from apps.email.models import EmailMessage as CRMMessage

        # Create a matching contact
        Contact.objects.create(
            tenant_id=tenant_id,
            first_name="Alice",
            last_name="Smith",
            email="alice@acme.com",
        )

        email = EmailMessage(
            provider_id="msg_1",
            thread_id="thread_1",
            message_id="<1@mail.com>",
            subject="Hello",
            from_address="alice@acme.com",
            from_name="Alice Smith",
            to_addresses=["bob@test.com"],
            sent_at=tz.now(),
        )

        crm_email = CRMMessage(
            tenant_id=tenant_id,
            message_id="msg_1",
            thread_id="thread_1",
            direction="inbound",
            from_email="alice@acme.com",
            to_emails=["bob@test.com"],
            subject="Hello",
            sent_at=tz.now(),
        )

        linker = ContactLinker(tenant_id=str(tenant_id))
        result = linker.link(email, crm_email)
        assert result.match_method in ("email",)
        assert result.contact_matched is not None

    def test_thread_deal_linking(self, db, tenant_id):
        """Pass 3: Thread match copies deal_id from existing thread email."""
        from apps.pipelines.models import Deal, Pipeline, Stage
        from apps.email.models import EmailMessage as CRMMessage

        # Create a pipeline and stage for the deal
        pipeline = Pipeline.objects.create(
            tenant_id=tenant_id, name="Sales Pipeline", is_active=True,
        )
        stage = Stage.objects.create(
            tenant_id=tenant_id, pipeline=pipeline, name="Qualified", display_order=1,
        )
        deal = Deal.objects.create(
            tenant_id=tenant_id,
            pipeline=pipeline,
            stage=stage,
            name="Test Deal",
            value=10000,
        )

        # Create an existing email in this thread linked to the deal
        existing_email = CRMMessage.objects.create(
            tenant_id=tenant_id,
            message_id="existing_thread_email",
            thread_id="thread_deal_1",
            external_thread_id="thread_deal_1",
            direction="inbound",
            from_email="alice@acme.com",
            to_emails=["bob@test.com"],
            subject="Regarding the deal",
            sent_at=tz.now(),
            deal=deal,
        )

        # Now a new email in the same thread — linker should pick up the deal_id
        email_msg = EmailMessage(
            provider_id="new_email_thread",
            thread_id="thread_deal_1",
            message_id="<new@mail.com>",
            subject="Re: Regarding the deal",
            from_address="bob@test.com",
            from_name="Bob",
            to_addresses=["alice@acme.com"],
            sent_at=tz.now(),
        )

        crm_email = CRMMessage(
            tenant_id=tenant_id,
            message_id="new_email_thread",
            thread_id="thread_deal_1",
            direction="inbound",
            from_email="bob@test.com",
            to_emails=["alice@acme.com"],
            subject="Re: Regarding the deal",
            sent_at=tz.now(),
        )

        linker = ContactLinker(tenant_id=str(tenant_id))
        result = linker.link(email_msg, crm_email)
        assert result.deal_matched is not None
        assert str(result.deal_matched) == str(deal.id)
        assert crm_email.deal_id == deal.id

    def test_full_link_flow_domain_match(self, db, tenant_id):
        """Pass 2: Domain match occurs when no direct contact is found."""
        from apps.contacts.models import Account
        from apps.email.models import EmailMessage as CRMMessage

        # Create an account with matching domain (no contact)
        Account.objects.create(
            tenant_id=tenant_id, name="Acme Corp", domain="acme.com",
        )

        email = EmailMessage(
            provider_id="msg_domain",
            thread_id="thread_d",
            message_id="<d@mail.com>",
            subject="Hello from unknown",
            from_address="newguy@acme.com",
            from_name="New Guy",
            to_addresses=["bob@test.com"],
            sent_at=tz.now(),
        )

        crm_email = CRMMessage(
            tenant_id=tenant_id,
            message_id="msg_domain",
            thread_id="thread_d",
            direction="inbound",
            from_email="newguy@acme.com",
            to_emails=["bob@test.com"],
            subject="Hello from unknown",
            sent_at=tz.now(),
        )

        linker = ContactLinker(tenant_id=str(tenant_id))
        result = linker.link(email, crm_email)
        # Pass 2 matches the account, but Pass 4 also creates a lead since
        # no contact was found. Both should be set.
        assert result.account_matched is not None
        assert result.contact_matched is not None
        assert result.contact_matched.source == "email_inbound"

    def test_full_link_flow_lead_creation(self, db, tenant_id, user):
        """Pass 4: Unknown sender creates a lead via link()."""
        from apps.email.models import EmailMessage as CRMMessage

        # No contact, no account for this domain — should create lead
        email = EmailMessage(
            provider_id="msg_lead",
            thread_id="thread_l",
            message_id="<l@mail.com>",
            subject="New inquiry",
            from_address="stranger@unknown.com",
            from_name="Stranger Danger",
            to_addresses=["bob@test.com"],
            sent_at=tz.now(),
        )

        crm_email = CRMMessage(
            tenant_id=tenant_id,
            message_id="msg_lead",
            thread_id="thread_l",
            direction="inbound",
            from_email="stranger@unknown.com",
            to_emails=["bob@test.com"],
            subject="New inquiry",
            sent_at=tz.now(),
        )

        linker = ContactLinker(tenant_id=str(tenant_id), user_id=str(user.id))
        result = linker.link(email, crm_email)
        assert result.match_method == "new_lead"
        assert result.contact_matched is not None
        assert result.contact_matched.source == "email_inbound"
        assert result.contact_matched.email == "stranger@unknown.com"


# ═══════════════════════════════════════════════════════════════════════════════
# Thread Matcher Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestThreadMatcher:
    """Thread grouping logic."""

    def test_get_or_create_thread_new(self, db, tenant_id):
        matcher = ThreadMatcher(tenant_id=str(tenant_id))
        email = EmailMessage(
            provider_id="msg_1",
            thread_id="gmail_thread_1",
            message_id="<1@mail.com>",
            subject="Hello",
            from_address="alice@acme.com",
            from_name="Alice",
            to_addresses=["bob@test.com"],
            sent_at=tz.now(),
        )

        thread, created = matcher.get_or_create_thread(email)
        assert created
        assert thread.normalized_subject == "hello"
        assert "alice@acme.com" in thread.participants

    def test_get_or_create_thread_existing_by_external_thread(self, db, tenant_id):
        from apps.sync.models import EmailThread

        # Create a thread
        thread = EmailThread.objects.create(
            tenant_id=tenant_id,
            normalized_subject="hello",
            email_count=0,
        )

        matcher = ThreadMatcher(tenant_id=str(tenant_id))

        # Create an email that references this external thread
        from apps.email.models import EmailMessage as CRMMessage

        CRMMessage.objects.create(
            tenant_id=tenant_id,
            message_id="existing_msg",
            thread_id="gmail_thread_1",
            external_thread_id="gmail_thread_1",
            direction="inbound",
            from_email="alice@acme.com",
            to_emails=["bob@test.com"],
            subject="Hello",
            sent_at=tz.now(),
            # Link to our thread
            crm_thread=thread,
        )

        # Now a new email with same Gmail threadId should match
        email = EmailMessage(
            provider_id="msg_2",
            thread_id="gmail_thread_1",
            message_id="<2@mail.com>",
            subject="Re: Hello",
            from_address="bob@test.com",
            from_name="Bob",
            to_addresses=["alice@acme.com"],
            sent_at=tz.now(),
        )

        matched_thread, created = matcher.get_or_create_thread(email)
        assert not created
        assert matched_thread.id == thread.id


# ═══════════════════════════════════════════════════════════════════════════════
# SyncLock Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyncLock:
    """Concurrent sync prevention."""

    def test_acquire_release(self):
        conn_id = str(uuid.uuid4())
        assert SyncLock.acquire(conn_id)
        # Second acquire should fail
        assert not SyncLock.acquire(conn_id)
        SyncLock.release(conn_id)
        # After release, should be able to acquire again
        assert SyncLock.acquire(conn_id)
        SyncLock.release(conn_id)

    def test_sync_with_lock_skips_if_locked(self):
        conn_id = str(uuid.uuid4())
        call_count = [0]

        def sync_fn():
            call_count[0] += 1

        # First call should execute sync_fn
        SyncLock.sync_with_lock(conn_id, sync_fn)
        assert call_count[0] == 1

        # Acquire lock manually so second call is blocked
        assert SyncLock.acquire(conn_id)
        # Third call should skip (manually locked)
        SyncLock.sync_with_lock(conn_id, sync_fn)
        assert call_count[0] == 1  # not incremented

        # Release and try again
        SyncLock.release(conn_id)
        SyncLock.sync_with_lock(conn_id, sync_fn)
        assert call_count[0] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# API Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyncAPI:
    """Sync connection API endpoints."""

    BASE_URL = "/api/sync/"

    def test_list_connections_empty(self, auth_client, db):
        resp = auth_client.get(f"{self.BASE_URL}connections/")
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_list_states_empty(self, auth_client, db):
        resp = auth_client.get(f"{self.BASE_URL}states/")
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_gmail_auth_url(self, auth_client, db):
        """GET auth URL — returns a Google OAuth URL with state."""
        with patch("apps.sync.oauth._store_state"):
            resp = auth_client.post(f"{self.BASE_URL}connections/gmail/auth-url/")
            assert resp.status_code == 200
            data = resp.json()
            assert "url" in data
            assert "state" in data
            assert "accounts.google.com" in data["url"]

    def test_gmail_callback_invalid_state(self, auth_client, db):
        """POST callback with invalid state returns 400."""
        with patch("apps.sync.oauth._verify_state", return_value=False):
            resp = auth_client.post(
                f"{self.BASE_URL}connections/gmail/callback/",
                {"code": "test_code", "state": "bad_state"},
                format="json",
            )
            assert resp.status_code == 400
            assert "state" in resp.json()["error"].lower()

    def test_gmail_callback_missing_fields(self, auth_client, db):
        resp = auth_client.post(
            f"{self.BASE_URL}connections/gmail/callback/",
            {"code": "test_code"},
            format="json",
        )
        assert resp.status_code == 400

    def test_create_connection(self, auth_client, user, db):
        payload = {
            "provider": "gmail",
            "provider_account": "test@gmail.com",
            "sync_interval_seconds": 60,
        }
        resp = auth_client.post(f"{self.BASE_URL}connections/", payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["provider"] == "gmail"
        assert data["status"] == "active"

    def test_trigger_manual_sync(self, auth_client, user, db):
        from apps.sync.models import SyncConnection

        conn = SyncConnection.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            provider="gmail",
            provider_account="test@test.com",
        )
        with patch("apps.sync.tasks.sync_email_delta.delay") as mock_task:
            resp = auth_client.post(f"{self.BASE_URL}connections/{conn.id}/sync/")
            assert resp.status_code == 200
            assert resp.json()["status"] == "sync_queued"
            mock_task.assert_called_once_with(
                connection_id=str(conn.id), trigger="manual"
            )

    def test_disconnect_connection(self, auth_client, user, db):
        from apps.sync.models import SyncConnection

        conn = SyncConnection.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            provider="gmail",
            provider_account="test@test.com",
        )
        resp = auth_client.post(f"{self.BASE_URL}connections/{conn.id}/disconnect/")
        assert resp.status_code == 200
        conn.refresh_from_db()
        assert conn.status == "disconnected"
        assert not conn.is_active

    def test_tenant_isolation(self, auth_client, user, db):
        """Another tenant's connection should not be visible."""
        from apps.sync.models import SyncConnection

        other_tenant = uuid.uuid4()
        conn = SyncConnection.objects.create(
            tenant_id=other_tenant,
            user=user,
            provider="gmail",
            provider_account="other@test.com",
        )
        resp = auth_client.get(f"{self.BASE_URL}connections/{conn.id}/")
        assert resp.status_code == 404 or resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# OAuth Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestOAuth:
    """OAuth callback flow."""

    BASE_URL = "/api/sync/"

    @patch("apps.sync.oauth._verify_state", return_value=True)
    @patch("apps.sync.oauth._exchange_code")
    @patch("apps.sync.oauth._get_user_email")
    def test_callback_success_creates_connection_and_state(
        self, mock_get_email, mock_exchange, mock_verify, auth_client, db,
    ):
        """POST callback with valid code creates SyncConnection + SyncState + enqueues sync."""
        mock_exchange.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }
        mock_get_email.return_value = "test@gmail.com"

        with patch("apps.sync.tasks.sync_email_delta.delay") as mock_task:
            resp = auth_client.post(
                f"{self.BASE_URL}connections/gmail/callback/",
                {"code": "valid_code", "state": "valid_state"},
                format="json",
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["provider"] == "gmail"
        assert data["email"] == "test@gmail.com"
        assert data["status"] == "syncing"
        assert "id" in data

        # Verify SyncState was created
        from apps.sync.models import SyncConnection, SyncState

        conn = SyncConnection.objects.get(id=data["id"])
        assert conn.provider_account == "test@gmail.com"
        assert conn.status == "active"

        state = SyncState.objects.get(connection=conn)
        assert state.sync_type == "email"
        assert state.state == "pending"

        # Verify delta sync was enqueued
        mock_task.assert_called_once_with(
            connection_id=str(conn.id), trigger="initial_oauth"
        )

    @patch("apps.sync.oauth._verify_state")
    @patch("apps.sync.oauth._exchange_code", return_value=None)
    def test_callback_exchange_failure(
        self, mock_exchange, mock_verify, auth_client, db,
    ):
        """POST callback when code exchange fails returns 400."""
        mock_verify.return_value = True
        resp = auth_client.post(
            f"{self.BASE_URL}connections/gmail/callback/",
            {"code": "bad_code", "state": "valid_state"},
            format="json",
        )
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# Error Handling Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Progressive backoff and failure escalation."""

    def test_handle_sync_error_five_failures_marks_error(self, db, tenant_id, user):
        """5 consecutive failures mark connection 'error'."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks import _handle_sync_error

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="gmail",
            provider_account="test@test.com",
            error_count=4,
            status="active",
        )

        # 5th failure
        _handle_sync_error(conn, Exception("Something went wrong"))
        conn.refresh_from_db()

        assert conn.status == "error"
        assert conn.error_count == 5
        assert "5 consecutive" in conn.last_error_message

    def test_handle_sync_error_backoff_interval(self, db, tenant_id, user):
        """3+ failures double the sync interval (up to 600s)."""
        from apps.sync.models import SyncConnection
        from apps.sync.tasks import _handle_sync_error

        conn = SyncConnection.objects.create(
            tenant_id=tenant_id,
            user=user,
            provider="gmail",
            provider_account="test@test.com",
            error_count=2,
            sync_interval_seconds=60,
            status="active",
        )

        # 3rd failure — doubles interval
        _handle_sync_error(conn, Exception("Fail 3"))
        conn.refresh_from_db()
        assert conn.error_count == 3
        assert conn.sync_interval_seconds == 120

        # 4th failure — doubles again
        _handle_sync_error(conn, Exception("Fail 4"))
        conn.refresh_from_db()
        assert conn.error_count == 4
        assert conn.sync_interval_seconds == 240