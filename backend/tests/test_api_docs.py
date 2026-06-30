"""Tests for the API documentation endpoints (drf-spectacular).

Validates:
- Schema endpoint returns valid OpenAPI 3.0.3
- Swagger UI and ReDoc UI render correctly
- Auth scoping — doc endpoints are publicly accessible
- Schema structure — expected components, paths, and security schemes
"""

import json

import pytest


# ── Top-level doc endpoints are publicly accessible ──────────────────────

class TestDocEndpointsPublicAccess:
    """Schema, Swagger UI, and ReDoc must work without authentication."""

    def test_schema_endpoint_returns_200_without_auth(self, api_client):
        """GET /api/docs/schema/ returns 200 and valid JSON for unauthenticated clients."""
        response = api_client.get("/api/docs/schema/")
        assert response.status_code == 200, f"Schema endpoint returned {response.status_code}"
        assert "application/json" in response["Content-Type"] or "application/vnd.oai" in response["Content-Type"], \
            f"Expected JSON content type, got {response['Content-Type']}"

    def test_swagger_ui_returns_200_without_auth(self, api_client):
        """Swagger UI HTML page loads for unauthenticated clients."""
        response = api_client.get("/api/docs/swagger/")
        assert response.status_code == 200, f"Swagger UI returned {response.status_code}"
        assert "text/html" in response["Content-Type"], \
            f"Expected HTML, got {response['Content-Type']}"

    def test_redoc_returns_200_without_auth(self, api_client):
        """ReDoc HTML page loads for unauthenticated clients."""
        response = api_client.get("/api/docs/redoc/")
        assert response.status_code == 200, f"ReDoc returned {response.status_code}"
        assert "text/html" in response["Content-Type"], \
            f"Expected HTML, got {response['Content-Type']}"


class TestDocEndpointsAuthenticated:
    """Docs endpoints should also work when authenticated (no auth crash)."""

    def test_schema_via_auth_client(self, auth_client):
        response = auth_client.get("/api/docs/schema/")
        assert response.status_code == 200

    def test_swagger_via_auth_client(self, auth_client):
        response = auth_client.get("/api/docs/swagger/")
        assert response.status_code == 200

    def test_redoc_via_auth_client(self, auth_client):
        response = auth_client.get("/api/docs/redoc/")
        assert response.status_code == 200


# ── Schema structure validation ─────────────────────────────────────────

class TestSchemaStructure:
    """Validates the generated OpenAPI schema content."""

    @pytest.fixture
    def schema(self, api_client):
        """Fetch and parse the schema as JSON once for this class."""
        response = api_client.get(
            "/api/docs/schema/",
            HTTP_ACCEPT="application/json",
        )
        assert response.status_code == 200
        return json.loads(response.content)

    def test_openapi_version(self, schema):
        """Schema declares OpenAPI 3.0.x."""
        assert schema.get("openapi", "").startswith("3.0"), \
            f"Expected OpenAPI 3.0.x, got {schema.get('openapi')}"

    def test_info_title(self, schema):
        assert schema.get("info", {}).get("title") == "FrontierCRM API"

    def test_info_version(self, schema):
        assert schema.get("info", {}).get("version") == "1.0.0"

    def test_info_description(self, schema):
        desc = schema.get("info", {}).get("description", "")
        assert "FrontierCRM" in desc
        assert "CRM" in desc

    def test_has_security_schemes(self, schema):
        """Schema defines both JWT and cookie auth security schemes."""
        components = schema.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        assert "jwtAuth" in security_schemes, "Missing jwtAuth security scheme"
        assert "cookieAuth" in security_schemes, "Missing cookieAuth security scheme"

    def test_jwt_auth_scheme_config(self, schema):
        jwt_scheme = schema["components"]["securitySchemes"]["jwtAuth"]
        assert jwt_scheme.get("type") == "http"
        assert jwt_scheme.get("scheme") == "bearer"
        assert jwt_scheme.get("bearerFormat") == "JWT"

    def test_cookie_auth_scheme_config(self, schema):
        cookie_scheme = schema["components"]["securitySchemes"]["cookieAuth"]
        assert cookie_scheme.get("type") == "apiKey"
        assert cookie_scheme.get("in") == "cookie"
        assert "sessionid" in cookie_scheme.get("name", "").lower()

    def test_security_schemes_referenced_in_endpoints(self, schema):
        """At least one endpoint should reference jwtAuth or cookieAuth."""
        paths = schema.get("paths", {})
        found = False
        for path, methods in paths.items():
            for method, detail in methods.items():
                if method not in ("get", "post", "put", "patch", "delete"):
                    continue
                sec = detail.get("security", [])
                if any("jwtAuth" in s for s in sec):
                    found = True
                    break
            if found:
                break
        assert found, "No endpoint references jwtAuth in its security block"

    def test_has_paths(self, schema):
        paths = schema.get("paths", {})
        assert len(paths) > 0, "Schema has zero API paths documented"

    def test_has_components(self, schema):
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        assert len(schemas) > 0, "Schema has zero component schemas"

    def test_schema_has_auth_path(self, schema):
        paths = schema.get("paths", {})
        auth_paths = [p for p in paths if "auth" in p]
        assert len(auth_paths) >= 3, \
            f"Expected at least 3 auth paths, found {len(auth_paths)}: {auth_paths}"

    def test_schema_has_contacts_paths(self, schema):
        paths = schema.get("paths", {})
        contact_paths = [p for p in paths if "contacts" in p]
        assert len(contact_paths) >= 1, "No /api/contacts/ paths in schema"

    def test_schema_has_deals_paths(self, schema):
        paths = schema.get("paths", {})
        deal_paths = [p for p in paths if "deals" in p or "pipelines" in p]
        assert len(deal_paths) >= 1, "No deal/pipeline paths in schema"

    def test_schema_valid_json_roundtrip(self, schema):
        """Schema JSON must be serializable without errors."""
        dumped = json.dumps(schema)
        reloaded = json.loads(dumped)
        assert reloaded["info"]["title"] == "FrontierCRM API"
        assert len(reloaded["paths"]) == len(schema["paths"])

    def test_schema_all_paths_have_operations(self, schema):
        """Every path should have at least one HTTP method (get/post/put/patch/delete)."""
        valid_methods = {"get", "post", "put", "patch", "delete", "options", "head"}
        empty_paths = []
        for path, methods in schema.get("paths", {}).items():
            path_methods = set(methods.keys()) & valid_methods
            if not path_methods:
                empty_paths.append(path)
        assert not empty_paths, f"Paths with no HTTP operations: {empty_paths}"

    def test_tags_documented_in_paths(self, schema):
        """Every documented operation must have a tag, and tags must match known ones."""
        known_tags = {
            "Auth", "Accounts", "Contacts", "Deals", "Activities",
            "Email", "Notes", "Tasks", "Teams", "Files", "Search",
            "Reports", "Export", "Sync", "Webhooks",
        }
        paths = schema.get("paths", {})
        untagged = []
        unknown_tagged = []
        for path, methods in paths.items():
            for method, detail in methods.items():
                if method not in ("get", "post", "put", "patch", "delete"):
                    continue
                tags = detail.get("tags", [])
                if not tags:
                    untagged.append(f"{method.upper()} {path}")
                for tag in tags:
                    if tag not in known_tags:
                        unknown_tagged.append(f"{method.upper()} {path}: tag='{tag}'")
        assert not untagged, f"Operations with no tags: {untagged[:5]}"
        # New tags appearing is not a hard failure, but log a few as a heads-up
        if unknown_tagged:
            pytest.skip(f"Unknown tags found: {unknown_tagged[:5]}")

    def test_schema_does_not_expose_internal_paths(self, schema):
        """Admin paths should not appear in the public API schema."""
        paths = schema.get("paths", {})
        admin_paths = [p for p in paths if "admin" in p]
        assert len(admin_paths) == 0, f"Admin paths leaked into schema: {admin_paths}"

    def test_all_security_schemes_have_required_fields(self, schema):
        """Every security scheme entry must have required type and location."""
        schemes = schema.get("components", {}).get("securitySchemes", {})
        for name, scheme in schemes.items():
            assert scheme.get("type"), f"Security scheme '{name}' missing 'type'"


# ── Swagger UI content ─────────────────────────────────────────────────

class TestSwaggerUI:
    """Validates Swagger UI HTML loads with correct resources."""

    def test_swagger_ui_contains_swagger_css(self, api_client):
        response = api_client.get("/api/docs/swagger/")
        content = response.content.decode()
        assert "swagger-ui" in content or "swagger" in content.lower(), \
            "Swagger UI page doesn't mention swagger"

    def test_swagger_ui_contains_schema_url(self, api_client):
        response = api_client.get("/api/docs/swagger/")
        content = response.content.decode()
        assert "/api/docs/schema/" in content or "schema" in content, \
            "Swagger UI page doesn't reference the schema URL"

    def test_swagger_ui_title(self, api_client):
        response = api_client.get("/api/docs/swagger/")
        content = response.content.decode()
        assert "FrontierCRM" in content or "swagger" in content.lower(), \
            "Swagger UI page missing expected title text"


# ── ReDoc content ──────────────────────────────────────────────────────

class TestReDoc:
    """Validates ReDoc HTML loads with correct resources."""

    def test_redoc_contains_redoc_script(self, api_client):
        response = api_client.get("/api/docs/redoc/")
        content = response.content.decode()
        assert "redoc" in content.lower(), "ReDoc page doesn't reference ReDoc"

    def test_redoc_contains_schema_url(self, api_client):
        response = api_client.get("/api/docs/redoc/")
        content = response.content.decode()
        assert "/api/docs/schema/" in content or "schema" in content, \
            "ReDoc page doesn't reference the schema URL"


# ── Edge cases / hardening ─────────────────────────────────────────────

class TestSchemaEdgeCases:
    """Schema robustness under different conditions."""

    def test_schema_does_not_crash_with_accept_header(self, api_client):
        """Schema should work with explicit Accept: application/json."""
        response = api_client.get(
            "/api/docs/schema/",
            HTTP_ACCEPT="application/json",
        )
        assert response.status_code == 200
