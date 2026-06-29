"""Tests for core infrastructure — pagination, exceptions, permissions, throttling, models."""

from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from unittest.mock import patch

from apps.core.exceptions import custom_exception_handler
from apps.core.models import TenantScopedModel, TimeStampedModel
from apps.core.pagination import StandardPagination
from apps.core.permissions import TenantAwarePermission

UserModel = get_user_model()


# ── Pagination Format ────────────────────────────────────────────────────────


class TestStandardPagination:
    """Verify paginated response includes all required fields."""

    def test_paginated_response_shape(self):
        """StandardPagination.get_paginated_response returns count, page,
        page_size, total_pages, next, previous, results."""
        drf_request = APIRequestFactory().get("/api/dummy/")

        # Build a mock paginator scenario
        class MockPage:
            paginator = type("Obj", (), {"count": 42, "num_pages": 2})()
            number = 1

        paginator = StandardPagination()
        paginator.request = drf_request
        paginator.page = MockPage()
        # get_page_size needs a DRF Request — mock it
        paginator.get_page_size = lambda req: 25
        # next/previous links need a full mock page — mock them too
        paginator.get_next_link = lambda: "http://testserver/api/dummy/?page=2"
        paginator.get_previous_link = lambda: None

        resp = paginator.get_paginated_response(["item1", "item2"])
        data = resp.data

        assert data["count"] == 42
        assert data["page"] == 1
        assert data["page_size"] == 25  # default
        assert data["total_pages"] == 2
        assert data["next"] == "http://testserver/api/dummy/?page=2"
        assert data["previous"] is None
        assert data["results"] == ["item1", "item2"]

    def test_pagination_class_used(self, auth_client, db):
        """Hitting a paginated endpoint returns the standard shape."""
        resp = auth_client.get("/api/teams/teams/")
        data = resp.data
        assert "count" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "next" in data
        assert "previous" in data
        assert "results" in data


# ── Exception Handler ────────────────────────────────────────────────────────


class TestCustomExceptionHandler:
    """Custom exception handler wraps errors in consistent shape:
    {error: True, status_code: int, detail: str, errors: dict | None}."""

    def _make_context(self):
        """Create a minimal view/request context."""
        from rest_framework.views import APIView

        return {"view": APIView(), "args": (), "kwargs": {}}

    def test_validation_error_shape(self, rf):
        """A 400 ValidationError gets the standard envelope."""
        from rest_framework.exceptions import ValidationError

        exc = ValidationError({"name": ["This field is required."]})
        context = self._make_context()
        resp = custom_exception_handler(exc, context)

        assert resp is not None
        assert resp.data["error"] is True
        assert resp.data["status_code"] == 400
        assert resp.data["detail"] == "This field is required."
        assert resp.data["errors"] == {"name": ["This field is required."]}

    def test_not_found_shape(self, rf):
        """A 404 gets the standard envelope.
        DRF wraps a single string into {'detail': '...'}, so errors
        is a dict (the original DRF error data), not None."""
        from rest_framework.exceptions import NotFound

        exc = NotFound("Resource not found.")
        context = self._make_context()
        resp = custom_exception_handler(exc, context)

        assert resp is not None
        assert resp.data["error"] is True
        assert resp.data["status_code"] == 404
        assert resp.data["detail"] == "Resource not found."
        # DRF stores the detail in a dict, so errors is a dict not None
        assert isinstance(resp.data["errors"], dict)

    def test_permission_denied_shape(self, rf):
        """A 403 gets the standard envelope."""
        from rest_framework.exceptions import PermissionDenied

        exc = PermissionDenied("You do not have permission.")
        context = self._make_context()
        resp = custom_exception_handler(exc, context)

        assert resp is not None
        assert resp.data["error"] is True
        assert resp.data["status_code"] == 403
        assert resp.data["detail"] == "You do not have permission."
        assert isinstance(resp.data["errors"], dict)

    def test_auth_failed_shape(self, rf):
        """A 401 gets the standard envelope."""
        from rest_framework.exceptions import NotAuthenticated

        exc = NotAuthenticated("Authentication credentials were not provided.")
        context = self._make_context()
        resp = custom_exception_handler(exc, context)

        assert resp is not None
        assert resp.data["error"] is True
        assert resp.data["status_code"] == 401
        assert resp.data["detail"] == "Authentication credentials were not provided."

    def test_non_drf_exception_returns_none(self, rf):
        """Handler returns None for non-DRF exceptions (let Django handle)."""
        exc = ValueError("Something terrible happened.")
        context = self._make_context()
        resp = custom_exception_handler(exc, context)
        assert resp is None

    def test_actual_api_response(self, api_client):
        """Hitting an endpoint unauthenticated returns the custom shape."""
        resp = api_client.get("/api/teams/teams/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        data = resp.data
        assert data["error"] is True
        assert data["status_code"] == 401
        assert isinstance(data["detail"], str)
        # errors may be None for auth failures
        assert "errors" in data


# ── Permissions: TenantAwarePermission ───────────────────────────────────────


class TestTenantAwarePermission:
    """TenantAwarePermission behavior."""

    def test_unauthenticated_user_denied(self):
        request = APIRequestFactory().get("/")
        request.user = type("AnonUser", (), {"is_authenticated": False})()
        perm = TenantAwarePermission()
        assert perm.has_permission(request, None) is False

    def test_authenticated_with_tenant_allowed(self):
        request = APIRequestFactory().get("/")
        request.user = type(
            "AuthUser",
            (),
            {"is_authenticated": True, "tenant_id": uuid.uuid4()},
        )()
        perm = TenantAwarePermission()
        assert perm.has_permission(request, None) is True

    def test_authenticated_without_tenant_denied(self):
        request = APIRequestFactory().get("/")
        request.user = type(
            "AuthUser",
            (),
            {"is_authenticated": True, "tenant_id": None},
        )()
        perm = TenantAwarePermission()
        assert perm.has_permission(request, None) is False

    def test_object_permission_tenant_mismatch_denied(self):
        """Object-level check: obj.tenant_id must match user.tenant_id."""
        request = APIRequestFactory().get("/")
        user_tenant_id = uuid.uuid4()
        request.user = type(
            "AuthUser",
            (),
            {"is_authenticated": True, "tenant_id": user_tenant_id},
        )()

        obj = type("Obj", (), {"tenant_id": uuid.uuid4()})()  # different UUID
        perm = TenantAwarePermission()
        assert perm.has_object_permission(request, None, obj) is False

    def test_object_permission_tenant_match_allowed(self):
        request = APIRequestFactory().get("/")
        tid = uuid.uuid4()
        request.user = type(
            "AuthUser",
            (),
            {"is_authenticated": True, "tenant_id": tid},
        )()

        obj = type("Obj", (), {"tenant_id": tid})()
        perm = TenantAwarePermission()
        assert perm.has_object_permission(request, None, obj) is True

    def test_object_permission_no_tenant_id_allowed(self):
        """Non-tenant model (no tenant_id attr) gets a pass."""
        request = APIRequestFactory().get("/")
        request.user = type(
            "AuthUser",
            (),
            {"is_authenticated": True, "tenant_id": uuid.uuid4()},
        )()
        obj = type("Obj", (), {})()  # no tenant_id
        perm = TenantAwarePermission()
        assert perm.has_object_permission(request, None, obj) is True


# ── Rate Limiting ────────────────────────────────────────────────────────────


class TestRateLimiting:
    """Verify throttle class behavior directly (bypassing DRF cached settings
    which don't pick up override_settings)."""

    def test_user_rate_throttle_blocks_after_limit(self, db):
        """UserRateThrottle blocks the second request when rate is 1/minute."""
        from rest_framework.throttling import UserRateThrottle

        user = UserModel.objects.create_user(
            email="throttle@example.com",
            username="throttleuser",
            password="pass123",
            tenant_id=uuid.uuid4(),
        )
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        refresh.access_token["tenant_id"] = str(user.tenant_id)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        throttle = UserRateThrottle()
        throttle.rate = "1/minute"
        throttle.num_requests = 1
        throttle.duration = 60
        throttle.scope = "user"

        # First request — should be allowed
        request1 = client.get("/api/teams/teams/").wsgi_request
        request1.user = user
        assert throttle.allow_request(request1, None) is True

        # Second request — should be blocked
        request2 = client.get("/api/teams/teams/").wsgi_request
        request2.user = user
        assert throttle.allow_request(request2, None) is False

    def test_anon_rate_throttle_blocks_after_limit(self, db):
        """AnonRateThrottle blocks the second request when rate is 1/minute."""
        from rest_framework.throttling import AnonRateThrottle

        client = APIClient()

        throttle = AnonRateThrottle()
        throttle.rate = "1/minute"
        throttle.num_requests = 1
        throttle.duration = 60
        throttle.scope = "anon"

        # First request — should be allowed
        request1 = client.get("/api/teams/teams/").wsgi_request
        assert throttle.allow_request(request1, None) is True

        # Second request — should be blocked
        request2 = client.get("/api/teams/teams/").wsgi_request
        assert throttle.allow_request(request2, None) is False

    def test_throttle_returns_429_via_view(self, db):
        """Simulate a throttled API call by patching check_throttles
        to raise Throttled (which the custom exception handler wraps)."""
        from unittest.mock import patch
        from rest_framework.exceptions import Throttled

        user = UserModel.objects.create_user(
            email="throttle-e2e@example.com",
            username="throttlee2e",
            password="pass123",
            tenant_id=uuid.uuid4(),
        )
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        refresh.access_token["tenant_id"] = str(user.tenant_id)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # First request — normal
        resp1 = client.get("/api/teams/teams/")
        assert resp1.status_code != status.HTTP_429_TOO_MANY_REQUESTS

        # Force throttling on the second request
        with patch(
            "rest_framework.views.APIView.check_throttles",
            side_effect=Throttled(wait=60),
        ):
            resp2 = client.get("/api/teams/teams/")
        assert resp2.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = resp2.data
        assert data["error"] is True
        assert data["status_code"] == 429


# ── TimeStampedModel ─────────────────────────────────────────────────────────


class TestTimeStampedModel:
    """Auto timestamps and soft delete via the Contact model
    (Contact inherits TenantScopedModel → TimeStampedModel)."""

    def test_auto_timestamps(self, db, tenant_id):
        """created_at and updated_at are set automatically on create."""
        from apps.contacts.models import Contact
        import datetime

        contact = Contact.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            tenant_id=tenant_id,
        )
        assert isinstance(contact.created_at, datetime.datetime)
        assert isinstance(contact.updated_at, datetime.datetime)

    def test_soft_delete(self, db, tenant_id):
        """soft_delete sets deleted_at and is_deleted returns True."""
        from apps.contacts.models import Contact

        contact = Contact.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            tenant_id=tenant_id,
        )
        assert contact.deleted_at is None
        assert contact.is_deleted is False

        contact.soft_delete()
        contact.refresh_from_db()
        assert contact.deleted_at is not None
        assert contact.is_deleted is True


# ── TenantScopedModel ────────────────────────────────────────────────────────


class TestTenantScopedModel:
    """TenantScopedModel requires tenant_id."""

    def test_tenant_id_required(self, db):
        """TenantScopedModel subclasses require tenant_id on creation."""
        from apps.contacts.models import Contact

        with pytest.raises(Exception):
            Contact.objects.create(
                first_name="No",
                last_name="Tenant",
                email="notenant@example.com",
                # tenant_id omitted intentionally
            )

    def test_tenant_id_set_on_create(self, db, tenant_id):
        from apps.contacts.models import Contact

        contact = Contact.objects.create(
            first_name="Has",
            last_name="Tenant",
            email="hastenant@example.com",
            tenant_id=tenant_id,
        )
        assert contact.tenant_id == tenant_id

    def test_tenant_scoped_model_has_uuid_pk(self, db, tenant_id):
        from apps.contacts.models import Contact

        contact = Contact.objects.create(
            first_name="UUID",
            last_name="PK",
            email="uuidpk@example.com",
            tenant_id=tenant_id,
        )
        assert isinstance(contact.id, uuid.UUID)

    def test_tenant_scoped_str(self, db, tenant_id):
        from apps.contacts.models import Contact

        contact = Contact.objects.create(
            first_name="Str",
            last_name="Test",
            email="strtest@example.com",
            tenant_id=tenant_id,
        )
        # Contact overrides __str__ to return "Str Test"
        assert str(contact) == "Str Test"


# ── SearchService ─────────────────────────────────────────────────────────────


class TestSearchServiceCore:
    """Direct unit tests of SearchService with a mocked meilisearch.Client."""

    def _make_service(self):
        from apps.search.service import SearchService

        return SearchService()

    @patch("apps.search.service.Client")
    def test_index_document(self, mock_meili_client):
        """index_document calls client.index().add_documents()."""
        mock_instance = mock_meili_client.return_value
        mock_index = mock_instance.index.return_value

        service = self._make_service()
        service.index_document("contact", {"id": "123", "name": "Alice"})

        mock_instance.index.assert_called_once_with("frontiercrm_contact")
        mock_index.add_documents.assert_called_once_with(
            [{"id": "123", "name": "Alice"}]
        )

    @patch("apps.search.service.Client")
    def test_delete_document(self, mock_meili_client):
        """delete_document calls client.index().delete_document()."""
        mock_instance = mock_meili_client.return_value
        mock_index = mock_instance.index.return_value

        service = self._make_service()
        service.delete_document("contact", "doc-456")

        mock_instance.index.assert_called_once_with("frontiercrm_contact")
        mock_index.delete_document.assert_called_once_with("doc-456")

    @patch("apps.search.service.Client")
    def test_search(self, mock_meili_client):
        """search calls client.index().search() with correct params."""
        mock_instance = mock_meili_client.return_value
        mock_index = mock_instance.index.return_value
        mock_index.search.return_value = {"hits": [{"id": 1}], "total": 1}

        service = self._make_service()
        result = service.search(
            "contact",
            "Alice",
            filters="tenant_id = abc",
            page=2,
            hits_per_page=10,
        )

        mock_instance.index.assert_called_once_with("frontiercrm_contact")
        mock_index.search.assert_called_once_with(
            "Alice",
            {"filter": "tenant_id = abc", "page": 2, "hitsPerPage": 10},
        )
        assert result == {"hits": [{"id": 1}], "total": 1}

    @patch("apps.search.service.Client")
    def test_multi_search(self, mock_meili_client):
        """multi_search calls client.multi_search() with composite queries."""
        mock_instance = mock_meili_client.return_value
        mock_instance.multi_search.return_value = {"results": [{"hits": []}]}

        service = self._make_service()
        result = service.multi_search(["contact", "deal"], "hello", limit=5)

        mock_instance.multi_search.assert_called_once()
        call_args = mock_instance.multi_search.call_args[0][0]
        assert call_args == {
            "queries": [
                {"indexUid": "frontiercrm_contact", "q": "hello", "filter": None, "limit": 5},
                {"indexUid": "frontiercrm_deal", "q": "hello", "filter": None, "limit": 5},
            ]
        }
        assert result == {"results": [{"hits": []}]}

    @patch("apps.search.service.Client")
    def test_multi_search_single_model_returns_empty(self, mock_meili_client):
        """multi_search with a single model returns {} (no multi needed)."""
        mock_instance = mock_meili_client.return_value

        service = self._make_service()
        result = service.multi_search(["contact"], "hello")

        assert result == {}
        mock_instance.multi_search.assert_not_called()

    @patch("apps.search.service.Client")
    def test_health_returns_true(self, mock_meili_client):
        """health() returns True when client.health() succeeds."""
        mock_instance = mock_meili_client.return_value

        service = self._make_service()
        assert service.health() is True
        mock_instance.health.assert_called_once()

    @patch("apps.search.service.Client")
    def test_health_returns_false_on_exception(self, mock_meili_client):
        """health() returns False when client.health() raises."""
        mock_instance = mock_meili_client.return_value
        mock_instance.health.side_effect = Exception("Connection refused")

        service = self._make_service()
        assert service.health() is False
        mock_instance.health.assert_called_once()

    @patch("apps.search.service.Client")
    def test_configure_index(self, mock_meili_client):
        """configure_index calls client.index().update_settings()."""
        mock_instance = mock_meili_client.return_value
        mock_index = mock_instance.index.return_value

        service = self._make_service()
        settings = {"searchableAttributes": ["name", "email"]}
        service.configure_index("contact", settings)

        mock_instance.index.assert_called_once_with("frontiercrm_contact")
        mock_index.update_settings.assert_called_once_with(settings)

    @patch("apps.search.service.Client")
    def test_get_index_name_with_prefix(self, mock_meili_client):
        """get_index_name prepends the configured prefix."""
        service = self._make_service()
        assert service.get_index_name("contact") == "frontiercrm_contact"
        assert service.get_index_name("deal") == "frontiercrm_deal"
        assert service.get_index_name("account") == "frontiercrm_account"


# ── Gmail _parse_gmail_message ────────────────────────────────────────────────


class TestParseGmailMessage:
    """Unit tests of _parse_gmail_message from apps.email.tasks."""

    def test_parse_basic_message(self):
        """A standard Gmail API response is parsed into EmailMessage fields."""
        from apps.email.tasks import _parse_gmail_message

        msg_data = {
            "id": "msg-abc123",
            "threadId": "thread-xyz789",
            "historyId": "h12345",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Hello World"},
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "To", "value": "bob@example.com, charlie@example.com"},
                    {"name": "Cc", "value": "dave@example.com"},
                    {"name": "Date", "value": "Mon, 10 Mar 2025 14:30:00 +0000"},
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": "SGVsbG8gV29ybGQ="},  # "Hello World"
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": "PHA+SGVsbG8gV29ybGQ8L3A+"},  # "<p>Hello World</p>"
                    },
                ],
            },
        }

        tenant_id = "tenant-uuid-1"
        result = _parse_gmail_message(msg_data, tenant_id)

        assert result is not None
        assert result["tenant_id"] == tenant_id
        assert result["message_id"] == "msg-abc123"
        assert result["thread_id"] == "thread-xyz789"
        assert result["direction"] == "inbound"
        assert result["from_email"] == "alice@example.com"
        assert result["to_emails"] == ["bob@example.com", "charlie@example.com"]
        assert result["cc_emails"] == ["dave@example.com"]
        assert result["subject"] == "Hello World"
        assert result["body_text"] == "Hello World"
        assert result["body_html"] == "<p>Hello World</p>"
        assert result["gmail_history_id"] == "h12345"

    def test_parse_no_parts_single_body(self):
        """A message with a single inline body (no parts) is parsed correctly."""
        from apps.email.tasks import _parse_gmail_message

        msg_data = {
            "id": "msg-single",
            "threadId": "thread-single",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Simple"},
                    {"name": "From", "value": "from@example.com"},
                    {"name": "To", "value": "to@example.com"},
                ],
                "body": {"data": "U2ltcGxlIEJvZHk="},  # "Simple Body"
            },
        }

        result = _parse_gmail_message(msg_data, "tenant-2")

        assert result is not None
        assert result["subject"] == "Simple"
        assert result["from_email"] == "from@example.com"
        assert result["to_emails"] == ["to@example.com"]
        assert result["body_text"] == "Simple Body"
        assert result["body_html"] == ""

    def test_parse_nested_parts(self):
        """Nested multipart structure is handled via recursive _extract_parts."""
        from apps.email.tasks import _parse_gmail_message

        msg_data = {
            "id": "msg-nested",
            "threadId": "thread-nest",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Nested"},
                    {"name": "From", "value": "nested@example.com"},
                    {"name": "To", "value": "you@example.com"},
                ],
                "parts": [
                    {
                        "mimeType": "multipart/alternative",
                        "parts": [
                            {
                                "mimeType": "text/plain",
                                "body": {"data": "TmVzdGVkIFRleHQ="},  # "Nested Text"
                            },
                            {
                                "mimeType": "text/html",
                                "body": {"data": "PHA+TmVzdGVkIEhUTUw8L3A+"},  # "<p>Nested HTML</p>"
                            },
                        ],
                    }
                ],
            },
        }

        result = _parse_gmail_message(msg_data, "tenant-3")

        assert result is not None
        assert result["subject"] == "Nested"
        assert result["body_text"] == "Nested Text"
        assert result["body_html"] == "<p>Nested HTML</p>"

    def test_parse_missing_headers(self):
        """Message with missing subject/from/to returns empty strings."""
        from apps.email.tasks import _parse_gmail_message

        msg_data = {
            "id": "msg-no-headers",
            "threadId": "thread-no",
            "payload": {
                "headers": [],
            },
        }

        result = _parse_gmail_message(msg_data, "tenant-4")

        assert result is not None
        assert result["subject"] == ""
        assert result["from_email"] == ""
        assert result["to_emails"] == []
        assert result["body_text"] == ""
        assert result["body_html"] == ""

    def test_parse_empty_to_list(self):
        """No 'to' header results in empty recipient list."""
        from apps.email.tasks import _parse_gmail_message

        msg_data = {
            "id": "msg-no-to",
            "threadId": "thread-nt",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "No To"},
                    {"name": "From", "value": "sender@example.com"},
                ],
            },
        }

        result = _parse_gmail_message(msg_data, "tenant-5")

        assert result is not None
        assert result["to_emails"] == []
        assert result["from_email"] == "sender@example.com"

    def test_parse_without_thread_id(self):
        """A message missing threadId gets an empty string."""
        from apps.email.tasks import _parse_gmail_message

        msg_data = {
            "id": "msg-no-thread",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "No Thread"},
                    {"name": "From", "value": "x@y.com"},
                    {"name": "To", "value": "a@b.com"},
                ],
            },
        }

        result = _parse_gmail_message(msg_data, "tenant-6")

        assert result is not None
        assert result["thread_id"] == ""
        assert result["message_id"] == "msg-no-thread"