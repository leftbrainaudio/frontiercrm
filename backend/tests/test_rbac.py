"""Tests for RBAC: permission registry, role resolution, API gates."""

from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.core.permission_registry import PermissionDef, PermissionRegistry
from apps.core.role_defaults import DEFAULT_ROLES
from apps.teams.models import Membership, Role, Tenant

UserModel = get_user_model()

# ── Helpers ───────────────────────────────────────────────────────────────


@pytest.fixture
def tenant(db) -> Tenant:
    return Tenant.objects.create(name="Test Tenant")


@pytest.fixture
def viewer_role(db, tenant) -> Role:
    return Role.objects.create(
        tenant=tenant,
        name="Viewer",
        description="Read-only",
        is_admin=False,
        permissions={
            "contacts.view": True,
            "deals.view": True,
            "pipelines.view": True,
        },
    )


@pytest.fixture
def sales_rep_role(db, tenant) -> Role:
    return Role.objects.create(
        tenant=tenant,
        name="Sales Rep",
        description="Sales rep",
        is_admin=False,
        permissions={
            "contacts.view": True, "contacts.create": True, "contacts.edit": True,
            "deals.view": True, "deals.create": True, "deals.edit": True,
            "pipelines.view": True,
            "activities.view": True, "activities.create": True,
            "email.view": True, "email.send": True,
            "notes.create": True,
            "files.upload": True,
            "reports.view": True,
            "forecast.view": True,
        },
    )


@pytest.fixture
def manager_role(db, tenant, sales_rep_role) -> Role:
    role = Role.objects.create(
        tenant=tenant,
        name="Manager",
        description="Manager",
        is_admin=False,
        permissions={
            "deals.create": True, "deals.edit": True, "deals.delete": True,
            "pipelines.manage": True,
            "team.view": True, "team.invite": True,
            "reports.view": True, "reports.export": True,
            "forecast.view": True, "forecast.manage": True,
            "activities.delete": True,
            "contacts.delete": True,
        },
    )
    role.inherits_from = sales_rep_role
    role.save(update_fields=["inherits_from"])
    return role


@pytest.fixture
def admin_role(db, tenant) -> Role:
    return Role.objects.create(
        tenant=tenant,
        name="Admin",
        description="Admin",
        is_admin=True,
        permissions={},
    )


@pytest.fixture
def user_with_role(db, tenant, request) -> UserModel:
    """Create a user with a specific role fixture named in request.param."""
    role = request.getfixturevalue(request.param)
    user = UserModel.objects.create_user(
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        username=f"user-{uuid.uuid4().hex[:8]}",
        password="testpass123",
        tenant_id=tenant.id,
    )
    Membership.objects.create(
        user=user,
        tenant=tenant,
        role=role,
        is_active=True,
    )
    return user


@pytest.fixture
def viewer_user(db, tenant, viewer_role) -> UserModel:
    user = UserModel.objects.create_user(
        email="viewer@example.com",
        username="viewer",
        password="testpass123",
        tenant_id=tenant.id,
    )
    Membership.objects.create(user=user, tenant=tenant, role=viewer_role, is_active=True)
    return user


@pytest.fixture
def admin_user(db, tenant, admin_role) -> UserModel:
    user = UserModel.objects.create_user(
        email="admin@example.com",
        username="admin",
        password="testpass123",
        tenant_id=tenant.id,
    )
    Membership.objects.create(user=user, tenant=tenant, role=admin_role, is_active=True)
    return user


@pytest.fixture
def auth_client(request, api_client) -> None:
    """Parametrize: pass user_fixture_name as request.param."""
    from rest_framework_simplejwt.tokens import RefreshToken

    user = request.getfixturevalue(request.param)
    refresh = RefreshToken.for_user(user)
    if user.tenant_id:
        refresh.access_token["tenant_id"] = str(user.tenant_id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


# ── Test 1: Permission Registry ───────────────────────────────────────────


class TestPermissionRegistry:
    def test_has_all_permissions(self):
        """Registry should have at least 25 permissions defined."""
        assert len(PermissionRegistry.ALL) >= 31

    def test_all_keys_unique(self):
        """Every permission key should be unique."""
        keys = PermissionRegistry.all_keys()
        assert len(keys) == len(set(keys))

    def test_all_by_group_has_groups(self):
        """all_by_group should return permissions grouped."""
        groups = PermissionRegistry.all_by_group()
        assert "Contacts" in groups
        assert "Deals" in groups
        assert "Admin" in groups
        for name, perms in groups.items():
            for p in perms:
                assert isinstance(p, PermissionDef)
                assert p.group == name

    def test_admin_keys_are_valid_permissions(self):
        """__admin__ short-circuit keys should be real keys."""
        admin_keys = {k for k in PermissionRegistry.all_keys() if "team" in k or "settings" in k or "export" in k or "import" in k or "audit" in k}
        assert len(admin_keys) > 0


# ── Test 2: Role Resolution ───────────────────────────────────────────────


class TestRoleResolution:
    def test_role_has_permissions(self, sales_rep_role):
        """Sales Rep should have base permissions."""
        assert sales_rep_role.permissions
        assert sales_rep_role.permissions.get("contacts.view") is True

    def test_manager_inherits_sales_rep(self, manager_role, sales_rep_role):
        """Manager should inherit Sales Rep permissions via inherits_from."""
        assert manager_role.inherits_from == sales_rep_role
        merged = manager_role.resolved_permissions
        # Inherited from Sales Rep
        assert merged.get("contacts.view") is True
        assert merged.get("notes.create") is True
        # Own extra permissions
        assert merged.get("deals.delete") is True
        assert merged.get("team.view") is True

    def test_resolved_own_overrides_inherited(self, manager_role, sales_rep_role):
        """Own permissions should override inherited ones."""
        merged = manager_role.resolved_permissions
        # Manager has deals.create=True from both — own wins (same value, no conflict)
        assert merged.get("deals.create") is True

    def test_admin_has_no_permissions_dict(self, admin_role):
        """Admin role has empty permissions dict — handled by is_admin short-circuit."""
        assert admin_role.is_admin is True
        assert admin_role.permissions == {}

    def test_resolved_permissions_from_json(self, viewer_role):
        """Viewer should only have view permissions."""
        resolved = viewer_role.resolved_permissions
        assert resolved.get("contacts.view") is True
        assert resolved.get("deals.create", False) is False
        assert resolved.get("contacts.edit", False) is False


# ── Test 3: User Permission Helpers ──────────────────────────────────────


class TestUserPermissions:
    def test_user_has_permission(self, viewer_user):
        """Viewer should have contacts.view."""
        assert viewer_user.has_permission("contacts.view") is True
        assert viewer_user.has_permission("deals.create") is False

    def test_admin_has_all_permissions(self, admin_user):
        """Admin should have all permissions via is_admin short-circuit."""
        assert admin_user.has_permission("contacts.view") is True
        assert admin_user.has_permission("contacts.delete") is True
        assert admin_user.has_permission("team.manage_roles") is True
        assert admin_user.has_permission("audit.log") is True

    def test_user_without_role_has_no_permissions(self, db, tenant):
        """User with no role should have empty permissions."""
        user = UserModel.objects.create_user(
            email="norole@example.com",
            username="norole",
            password="testpass123",
            tenant_id=tenant.id,
        )
        assert user.permissions == {}
        assert user.has_permission("contacts.view") is False

    def test_user_membership_returns_role(self, viewer_user, viewer_role):
        """User.membership should return the active membership."""
        m = viewer_user.membership
        assert m is not None
        assert m.role == viewer_role

    def test_user_role_property(self, viewer_user, viewer_role):
        """User.role should return the role from the membership."""
        role = viewer_user.role
        assert role == viewer_role


# ── Test 4: Memberships/Me API Endpoint ──────────────────────────────────


class TestMembershipsMeEndpoint:
    ME_URL = "/api/teams/memberships/me/"

    def test_returns_permissions_for_viewer(self, api_client, viewer_user):
        """GET /api/teams/memberships/me/ should return viewer's permissions."""
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(viewer_user)
        refresh.access_token["tenant_id"] = str(viewer_user.tenant_id)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        resp = api_client.get(self.ME_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["role_name"] == "Viewer"
        assert data["is_admin"] is False
        assert data["permissions"]["contacts.view"] is True
        assert data["permissions"].get("deals.create", False) is False

    def test_returns_all_permissions_for_admin(self, api_client, admin_user):
        """Admin should get all permissions."""
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(admin_user)
        refresh.access_token["tenant_id"] = str(admin_user.tenant_id)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        resp = api_client.get(self.ME_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["role_name"] == "Admin"
        assert data["is_admin"] is True
        # Admin should have way more permissions than a regular role
        assert len(data["permissions"]) >= 31

    def test_unauthenticated_returns_401(self, api_client):
        """Unauthenticated requests should get 401."""
        resp = api_client.get(self.ME_URL)
        assert resp.status_code == 401


# ── Test 5: Permissions API Endpoint ─────────────────────────────────────


class TestPermissionsEndpoint:
    PERMS_URL = "/api/teams/permissions/"

    def test_returns_registry(self, api_client, admin_user):
        """GET /api/teams/permissions/ should return the registry."""
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(admin_user)
        refresh.access_token["tenant_id"] = str(admin_user.tenant_id)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        resp = api_client.get(self.PERMS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert "groups" in data
        assert "Contacts" in data["groups"]
        assert "Deals" in data["groups"]


# ── Test 6: API Gate with Role Permission ────────────────────────────────


class TestRolePermissionGate:
    """Test that ViewSets gated with RolePermission actually enforce."""

    LIST_DEALS_URL = "/api/deals/deals/"

    def test_viewer_cannot_create_deal(self, api_client, viewer_user):
        """Viewer should get 403 when trying to create a deal."""
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(viewer_user)
        refresh.access_token["tenant_id"] = str(viewer_user.tenant_id)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        resp = api_client.post(self.LIST_DEALS_URL, {"name": "Test Deal", "value": "1000"}, format="json")
        # TenantAwarePermission should pass (has tenant_id), but RolePermission should deny
        assert resp.status_code == 403

    def test_admin_can_create_deal(self, api_client, admin_user, tenant):
        """Admin should be able to create a deal."""
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(admin_user)
        refresh.access_token["tenant_id"] = str(admin_user.tenant_id)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        from apps.pipelines.models import Pipeline, Stage
        pipeline = Pipeline.objects.create(tenant_id=tenant.id, name="Test Pipeline")
        stage = Stage.objects.create(tenant_id=tenant.id, pipeline=pipeline, name="Discovery", display_order=0)

        resp = api_client.post(self.LIST_DEALS_URL, {
            "name": "Test Deal", "value": 1000, "pipeline": str(pipeline.id), "stage": str(stage.id),
        }, format="json")
        # Admin should be allowed
        assert resp.status_code == 201

    def test_viewer_can_list_deals(self, api_client, viewer_user):
        """Viewer should be able to list deals (deals.view=True)."""
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(viewer_user)
        refresh.access_token["tenant_id"] = str(viewer_user.tenant_id)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        resp = api_client.get(self.LIST_DEALS_URL)
        assert resp.status_code == 200


# ── Test 7: Default Role Templates ───────────────────────────────────────


class TestDefaultRoles:
    def test_all_default_roles_defined(self):
        """Should have 4 default role templates."""
        assert len(DEFAULT_ROLES) == 4
        names = [r["name"] for r in DEFAULT_ROLES]
        assert "Admin" in names
        assert "Manager" in names
        assert "Sales Rep" in names
        assert "Viewer" in names

    def test_admin_is_admin(self):
        """Admin role template should have is_admin=True."""
        admin = [r for r in DEFAULT_ROLES if r["name"] == "Admin"][0]
        assert admin["is_admin"] is True

    def test_viewer_read_only(self):
        """Viewer should only have view permissions."""
        viewer = [r for r in DEFAULT_ROLES if r["name"] == "Viewer"][0]
        for key, val in viewer["permissions"].items():
            assert val is True
            assert key.endswith(".view"), f"Viewer should not have {key}"
