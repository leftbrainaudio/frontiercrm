"""Tests for search endpoints — all mocked via SearchService."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

UserModel = get_user_model()

SEARCH_URL = "/api/search/"
HEALTH_URL = "/api/search/health/"
MOCK_PATH = "apps.search.views.SearchService"


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def search_user(db) -> UserModel:
    uid = uuid.uuid4()
    return UserModel.objects.create_user(
        email=f"search-{uid.hex[:8]}@frontiercrm.com",
        username=f"search-{uid.hex[:8]}",
        password="testpass123",
        tenant_id=uuid.uuid4(),
    )


@pytest.fixture
def auth(search_user, api_client):
    """Authenticated client for search tests."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(search_user)
    refresh.access_token["tenant_id"] = str(search_user.tenant_id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    api_client.user = search_user
    return api_client


# ── Authentication ───────────────────────────────────────────────────────────


class TestSearchAuth:
    """Search endpoints require authentication."""

    def test_search_requires_auth(self, api_client):
        resp = api_client.get(SEARCH_URL, {"q": "hello"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_health_requires_auth(self, api_client):
        resp = api_client.get(HEALTH_URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ── Query Validation ─────────────────────────────────────────────────────────


class TestSearchValidation:
    """Search returns 400 when 'q' is missing."""

    def test_get_without_q_returns_400(self, auth):
        resp = auth.get(SEARCH_URL)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_without_q_returns_400(self, auth):
        resp = auth.post(SEARCH_URL, {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ── Search — GET ─────────────────────────────────────────────────────────────


class TestSearchGET:
    """GET /api/search/?q=terms"""

    @patch(MOCK_PATH)
    def test_single_model_search_get(self, mock_service, auth):
        """Search with model parameter → single-model search."""
        mock_instance = mock_service.return_value
        mock_instance.search.return_value = {"hits": [{"id": 1}], "total": 1}

        resp = auth.get(SEARCH_URL, {"q": "hello", "model": "contact"})
        assert resp.status_code == status.HTTP_200_OK
        mock_instance.search.assert_called_once_with(
            model_name="contact",
            query="hello",
            filters=f"tenant_id = {auth.user.tenant_id}",
            page=1,
            hits_per_page=25,
        )

    @patch(MOCK_PATH)
    def test_multi_model_search_get(self, mock_service, auth):
        """Without model parameter → multi_search across all models."""
        mock_instance = mock_service.return_value
        mock_instance.multi_search.return_value = {"results": []}

        resp = auth.get(SEARCH_URL, {"q": "hello"})
        assert resp.status_code == status.HTTP_200_OK
        mock_instance.multi_search.assert_called_once()
        call_kwargs = mock_instance.multi_search.call_args[1]
        assert call_kwargs["query"] == "hello"
        assert "models" in call_kwargs
        assert "contact" in call_kwargs["models"]

    @patch(MOCK_PATH)
    def test_get_with_pagination_params(self, mock_service, auth):
        """Passing page and hits_per_page should be forwarded."""
        mock_instance = mock_service.return_value
        mock_instance.search.return_value = {"hits": [], "total": 0}

        auth.get(SEARCH_URL, {"q": "hello", "model": "deal", "page": "3", "hits_per_page": "10"})
        mock_instance.search.assert_called_once_with(
            model_name="deal",
            query="hello",
            filters=f"tenant_id = {auth.user.tenant_id}",
            page=3,
            hits_per_page=10,
        )


# ── Search — POST ────────────────────────────────────────────────────────────


class TestSearchPOST:
    """POST /api/search/ with q in body."""

    @patch(MOCK_PATH)
    def test_single_model_search_post(self, mock_service, auth):
        mock_instance = mock_service.return_value
        mock_instance.search.return_value = {"hits": [{"id": 42}], "total": 1}

        resp = auth.post(
            SEARCH_URL,
            {"q": "world", "model": "account"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        mock_instance.search.assert_called_once_with(
            model_name="account",
            query="world",
            filters=f"tenant_id = {auth.user.tenant_id}",
            page=1,
            hits_per_page=25,
        )

    @patch(MOCK_PATH)
    def test_multi_model_search_post(self, mock_service, auth):
        mock_instance = mock_service.return_value
        mock_instance.multi_search.return_value = {"results": []}

        resp = auth.post(
            SEARCH_URL,
            {"q": "world"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        mock_instance.multi_search.assert_called_once()
        assert mock_instance.multi_search.call_args[1]["query"] == "world"


# ── Search Health ────────────────────────────────────────────────────────────


class TestSearchHealth:
    """GET /api/search/health/"""

    @patch(MOCK_PATH)
    def test_health_healthy(self, mock_service, auth):
        mock_instance = mock_service.return_value
        mock_instance.health.return_value = True

        resp = auth.get(HEALTH_URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == {"status": "ok", "service": "meilisearch"}
        mock_instance.health.assert_called_once()

    @patch(MOCK_PATH)
    def test_health_unhealthy(self, mock_service, auth):
        mock_instance = mock_service.return_value
        mock_instance.health.return_value = False

        resp = auth.get(HEALTH_URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == {"status": "unavailable", "service": "meilisearch"}


# ── SearchService Unit Tests ─────────────────────────────────────────────────


class TestSearchServiceUnit:
    """Direct unit tests of SearchService with a mocked meilisearch.Client."""

    def _make_service(self):
        from apps.search.service import SearchService

        return SearchService()

    @patch("apps.search.service.Client")
    def test_index_document(self, mock_client):
        """index_document calls client.index(name).add_documents([doc])."""
        mock_instance = mock_client.return_value
        mock_index = mock_instance.index.return_value

        service = self._make_service()
        service.index_document("contact", {"id": "1", "name": "Alice"})

        mock_instance.index.assert_called_once_with("frontiercrm_contact")
        mock_index.add_documents.assert_called_once_with(
            [{"id": "1", "name": "Alice"}]
        )

    @patch("apps.search.service.Client")
    def test_delete_document(self, mock_client):
        """delete_document calls client.index(name).delete_document(doc_id)."""
        mock_instance = mock_client.return_value
        mock_index = mock_instance.index.return_value

        service = self._make_service()
        service.delete_document("deal", "doc-999")

        mock_instance.index.assert_called_once_with("frontiercrm_deal")
        mock_index.delete_document.assert_called_once_with("doc-999")

    @patch("apps.search.service.Client")
    def test_search(self, mock_client):
        """search calls client.index(name).search(query, options)."""
        mock_instance = mock_client.return_value
        mock_index = mock_instance.index.return_value
        mock_index.search.return_value = {"hits": [{"id": 42}], "total": 1}

        service = self._make_service()
        result = service.search("contact", "Alice", filters="tenant_id = x", page=1, hits_per_page=25)

        mock_instance.index.assert_called_once_with("frontiercrm_contact")
        mock_index.search.assert_called_once()
        args, kwargs = mock_index.search.call_args
        assert args[0] == "Alice"
        assert args[1] == {"filter": "tenant_id = x", "page": 1, "hitsPerPage": 25}
        assert result == {"hits": [{"id": 42}], "total": 1}

    @patch("apps.search.service.Client")
    def test_health_returns_true(self, mock_client):
        """health() returns True when client.health() succeeds."""
        mock_instance = mock_client.return_value

        service = self._make_service()
        assert service.health() is True
        mock_instance.health.assert_called_once()

    @patch("apps.search.service.Client")
    def test_health_returns_false(self, mock_client):
        """health() returns False when client.health() raises."""
        mock_instance = mock_client.return_value
        mock_instance.health.side_effect = ConnectionError("down")

        service = self._make_service()
        assert service.health() is False
        mock_instance.health.assert_called_once()

    @patch("apps.search.service.Client")
    def test_get_index_name(self, mock_client):
        """get_index_name prepends MEILISEARCH_INDEX_PREFIX."""
        service = self._make_service()
        assert service.get_index_name("contact") == "frontiercrm_contact"
        assert service.get_index_name("deal") == "frontiercrm_deal"