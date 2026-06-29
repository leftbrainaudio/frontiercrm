"""Tests for TenantMiddleware — tenant resolution via JWT and subdomain."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from django.test import RequestFactory
from django.test.utils import override_settings

from config.middleware import PUBLIC_PATHS, TenantMiddleware


class TestTenantMiddleware:
    """Direct unit tests of TenantMiddleware.process_request."""

    def _middleware(self) -> TenantMiddleware:
        return TenantMiddleware(lambda req: None)

    def _factory(self) -> RequestFactory:
        return RequestFactory()

    # ── Public paths bypass tenant resolution ──────────────────────────────

    def test_admin_path_bypasses(self):
        """/admin/ paths skip tenant resolution entirely."""
        request = self._factory().get("/admin/")
        self._middleware().process_request(request)
        assert request.tenant_id is None
        assert request.tenant is None

    def test_auth_path_bypasses(self):
        """/api/auth/ paths skip tenant resolution."""
        request = self._factory().get("/api/auth/login/")
        self._middleware().process_request(request)
        assert request.tenant_id is None

    def test_health_path_bypasses(self):
        """/api/health/ paths skip tenant resolution."""
        request = self._factory().get("/api/health/")
        self._middleware().process_request(request)
        assert request.tenant_id is None

    def test_schema_path_bypasses(self):
        """/api/schema/ paths skip tenant resolution."""
        request = self._factory().get("/api/schema/")
        self._middleware().process_request(request)
        assert request.tenant_id is None

    def test_docs_path_bypasses(self):
        """/api/docs/ paths skip tenant resolution."""
        request = self._factory().get("/api/docs/")
        self._middleware().process_request(request)
        assert request.tenant_id is None

    def test_static_path_bypasses(self):
        """/static/ paths skip tenant resolution."""
        request = self._factory().get("/static/css/app.css")
        self._middleware().process_request(request)
        assert request.tenant_id is None

    def test_media_path_bypasses(self):
        """/media/ paths skip tenant resolution."""
        request = self._factory().get("/media/uploads/doc.pdf")
        self._middleware().process_request(request)
        assert request.tenant_id is None

    # ── Non-public paths without auth ──────────────────────────────────────

    def test_no_auth_sets_tenant_id_none(self):
        """Unauthenticated request on a non-public path leaves tenant_id=None."""
        request = self._factory().get("/api/contacts/")
        request.user = type("AnonUser", (), {"is_authenticated": False})()
        self._middleware().process_request(request)
        assert request.tenant_id is None
        assert request.tenant is None

    # ── JWT-based tenant resolution ────────────────────────────────────────

    def _make_jwt(self, tenant_id: str | None = None) -> str:
        """Create a real JWT access token, optionally with tenant_id claim."""
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken()
        if tenant_id is not None:
            token["tenant_id"] = tenant_id
        return str(token)

    def test_jwt_sets_tenant_id(self):
        """A valid JWT with tenant_id claim sets request.tenant_id."""
        tid = str(uuid.uuid4())
        jwt_token = self._make_jwt(tenant_id=tid)

        request = self._factory().get(
            "/api/contacts/",
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
        )
        self._middleware().process_request(request)

        assert request.tenant_id == tid

    def test_jwt_missing_tenant_id(self):
        """A valid JWT without tenant_id claim leaves tenant_id=None."""
        jwt_token = self._make_jwt()  # no tenant_id claim

        request = self._factory().get(
            "/api/contacts/",
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
        )
        self._middleware().process_request(request)

        assert request.tenant_id is None

    def test_jwt_decode_error_does_not_crash(self):
        """If the token is invalid, middleware handles gracefully (tenant_id=None)."""
        request = self._factory().get(
            "/api/contacts/",
            HTTP_AUTHORIZATION="Bearer invalid.token.here",
        )
        # Should not raise
        self._middleware().process_request(request)
        assert request.tenant_id is None

    # ── Subdomain-based tenant resolution ──────────────────────────────────

    @override_settings(ALLOWED_HOSTS=["*"])
    @patch("apps.teams.models.Tenant")
    def test_subdomain_lookup_sets_tenant_id(self, mock_tenant_model):
        """Subdomain in hostname is resolved via Tenant.objects.filter."""
        tid = uuid.uuid4()
        mock_tenant = mock_tenant_model.objects.filter.return_value.first.return_value
        mock_tenant.id = tid

        request = self._factory().get("/api/deals/", HTTP_HOST="acme.frontiercrm.com")
        request.user = type("AuthUser", (), {"is_authenticated": True})()
        self._middleware().process_request(request)

        assert request.tenant_id == tid

    @patch("apps.teams.models.Tenant")
    @override_settings(ALLOWED_HOSTS=["*"])
    def test_subdomain_no_match_leaves_tenant_none(self, mock_tenant_model):
        """Subdomain without a matching Tenant leaves tenant_id=None."""
        mock_tenant_model.objects.filter.return_value.first.return_value = None

        request = self._factory().get(
            "/api/contacts/",
            HTTP_HOST="nonexistent.frontiercrm.com",
        )
        request.user = type("AuthUser", (), {"is_authenticated": True})()
        self._middleware().process_request(request)

        assert request.tenant_id is None
        assert request.tenant is None

    @patch("apps.teams.models.Tenant")
    @override_settings(ALLOWED_HOSTS=["*"])
    def test_subdomain_lookup_skipped_for_unauthenticated(self, mock_tenant_model):
        """Subdomain resolution is skipped when user is not authenticated."""
        request = self._factory().get(
            "/api/contacts/",
            HTTP_HOST="acme.frontiercrm.com",
        )
        request.user = type("AnonUser", (), {"is_authenticated": False})()
        self._middleware().process_request(request)

        assert request.tenant_id is None
        mock_tenant_model.objects.filter.assert_not_called()

    @patch("apps.teams.models.Tenant")
    @override_settings(ALLOWED_HOSTS=["*"])
    def test_localhost_skips_subdomain_lookup(self, mock_tenant_model):
        """localhost hostname skips subdomain resolution."""
        request = self._factory().get("/api/contacts/", HTTP_HOST="localhost:8000")
        request.user = type("AuthUser", (), {"is_authenticated": True})()
        self._middleware().process_request(request)

        assert request.tenant_id is None
        mock_tenant_model.objects.filter.assert_not_called()

    @patch("apps.teams.models.Tenant")
    @override_settings(ALLOWED_HOSTS=["*"])
    def test_subdomain_exception_does_not_crash(self, mock_tenant_model):
        """If Tenant lookup raises, middleware handles gracefully."""
        mock_tenant_model.objects.filter.side_effect = Exception("db error")

        request = self._factory().get(
            "/api/contacts/",
            HTTP_HOST="acme.frontiercrm.com",
        )
        request.user = type("AuthUser", (), {"is_authenticated": True})()
        # Should not raise
        self._middleware().process_request(request)
        assert request.tenant_id is None

    # ── PUBLIC_PATHS regex ─────────────────────────────────────────────────

    def test_public_paths_regex_matches_api_auth(self):
        assert PUBLIC_PATHS.match("/api/auth/login/")
        assert PUBLIC_PATHS.match("/api/auth/register/")

    def test_public_paths_regex_matches_admin(self):
        assert PUBLIC_PATHS.match("/admin/")
        assert PUBLIC_PATHS.match("/admin/login/")

    def test_public_paths_regex_matches_health(self):
        assert PUBLIC_PATHS.match("/api/health/")

    def test_public_paths_regex_matches_schema(self):
        assert PUBLIC_PATHS.match("/api/schema/")

    def test_public_paths_regex_matches_docs(self):
        assert PUBLIC_PATHS.match("/api/docs/")

    def test_public_paths_regex_matches_static(self):
        assert PUBLIC_PATHS.match("/static/css/main.css")

    def test_public_paths_regex_matches_media(self):
        assert PUBLIC_PATHS.match("/media/uploads/file.pdf")

    def test_public_paths_regex_does_not_match_api_teams(self):
        assert not PUBLIC_PATHS.match("/api/teams/")
        assert not PUBLIC_PATHS.match("/api/contacts/")

    def test_public_paths_regex_does_not_match_api_search(self):
        assert not PUBLIC_PATHS.match("/api/search/")

    # ── Edge cases ─────────────────────────────────────────────────────────

    def test_root_path_is_not_public(self):
        """Root / is not a public path, tenant resolution runs."""
        request = self._factory().get("/")
        request.user = type("AnonUser", (), {"is_authenticated": False})()
        self._middleware().process_request(request)
        assert request.tenant_id is None  # just doesn't crash

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_jwt_takes_priority_over_subdomain(self):
        """If JWT has tenant_id, subdomain is not consulted."""
        from rest_framework_simplejwt.tokens import AccessToken

        tid = str(uuid.uuid4())
        token = AccessToken()
        token["tenant_id"] = tid
        jwt_token = str(token)

        request = self._factory().get(
            "/api/contacts/",
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
            HTTP_HOST="different.frontiercrm.com",
        )
        request.user = type("AuthUser", (), {"is_authenticated": True})()

        self._middleware().process_request(request)

        assert request.tenant_id == tid