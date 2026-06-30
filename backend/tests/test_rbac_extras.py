"""Extended RBAC tests: cross-app gates, edge cases, management endpoints."""

from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.core.permission_registry import PermissionRegistry
from apps.core.permissions import RolePermission
from apps.teams.models import Membership, Role, Tenant

UserModel = get_user_model()

# ── Shared Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def tenant(db) -> Tenant:
    return Tenant.objects.create(name="Test Tenant")


@pytest.fixture
def other_tenant(db) -> Tenant:
    return Tenant.objects.create(name="Other Tenant")


@pytest.fixture
def viewer_role(db, tenant) -> Role:
    """Viewer with only view permissions."""
    return Role.objects.create(
        tenant=tenant, name="Viewer", description="Read-only", is_admin=False,
        permissions={"contacts.view": True, "deals.view": True, "pipelines.view": True,
                     "activities.view": True, "email.view": True, "reports.view": True,
                     "forecast.view": True, "team.view": True},
    )


@pytest.fixture
def sales_rep_role(db, tenant) -> Role:
    return Role.objects.create(
        tenant=tenant, name="Sales Rep", description="Sales rep", is_admin=False,
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
        tenant=tenant, name="Manager", description="Manager", is_admin=False,
        permissions={
            "deals.create": True, "deals.edit": True, "deals.delete": True,
            "pipelines.manage": True,
            "team.view": True, "team.invite": True,
            "reports.view": True, "reports.export": True,
            "forecast.view": True, "forecast.manage": True,
            "activities.delete": True,
            "contacts.delete": True,
            "notes.delete": True, "files.delete": True, "email.delete": True,
        },
    )
    role.inherits_from = sales_rep_role
    role.save(update_fields=["inherits_from"])
    return role


@pytest.fixture
def admin_role(db, tenant) -> Role:
    return Role.objects.create(
        tenant=tenant, name="Admin", description="Admin", is_admin=True, permissions={},
    )


@pytest.fixture
def viewer_user(db, tenant, viewer_role) -> UserModel:
    user = UserModel.objects.create_user(
        email="viewer@example.com", username="viewer",
        password="testpass123", tenant_id=tenant.id,
    )
    Membership.objects.create(user=user, tenant=tenant, role=viewer_role, is_active=True)
    return user


@pytest.fixture
def sales_rep_user(db, tenant, sales_rep_role) -> UserModel:
    user = UserModel.objects.create_user(
        email="salesrep@example.com", username="salesrep",
        password="testpass123", tenant_id=tenant.id,
    )
    Membership.objects.create(user=user, tenant=tenant, role=sales_rep_role, is_active=True)
    return user


@pytest.fixture
def manager_user(db, tenant, manager_role) -> UserModel:
    user = UserModel.objects.create_user(
        email="manager@example.com", username="manager",
        password="testpass123", tenant_id=tenant.id,
    )
    Membership.objects.create(user=user, tenant=tenant, role=manager_role, is_active=True)
    return user


@pytest.fixture
def admin_user(db, tenant, admin_role) -> UserModel:
    user = UserModel.objects.create_user(
        email="admin@example.com", username="admin",
        password="testpass123", tenant_id=tenant.id,
    )
    Membership.objects.create(user=user, tenant=tenant, role=admin_role, is_active=True)
    return user


@pytest.fixture
def no_role_user(db, tenant) -> UserModel:
    """User with tenant but no role assigned."""
    user = UserModel.objects.create_user(
        email="norole@example.com", username="norole",
        password="testpass123", tenant_id=tenant.id,
    )
    return user


def _auth(api_client, user):
    """Attach JWT auth for the given user."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    if user.tenant_id:
        refresh.access_token["tenant_id"] = str(user.tenant_id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")


# ── Test 1: RolePermission Edge Cases ─────────────────────────────────────


class TestRolePermissionEdgeCases:
    """Edge cases for the RolePermission class itself."""

    DEALS_URL = "/api/deals/deals/"

    def test_unauthenticated_returns_false(self, api_client):
        """Unauthenticated request → 401 (TenantAwarePermission denies first)."""
        resp = api_client.get(self.DEALS_URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_with_no_role_denied(self, api_client, no_role_user):
        """Authenticated user with no role should be denied (no permissions dict)."""
        _auth(api_client, no_role_user)
        resp = api_client.post(self.DEALS_URL, {"name": "Test"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_short_circuit_passes(self, api_client, admin_user):
        """__admin__ permission should pass for admin users."""
        # teams/roles destroy requires __admin__ (via admin_roles check) if we
        # test via team.manage_roles, admin has all permissions via is_admin.
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(admin_user)
        refresh.access_token["tenant_id"] = str(admin_user.tenant_id)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # Create a role first for the list endpoint (no permission required)
        # Test that admin can list roles (no permission required, passes)
        resp = api_client.get("/api/teams/roles/")
        assert resp.status_code == status.HTTP_200_OK

    def test_viewer_cannot_manage_role(self, api_client, viewer_user, tenant):
        """Viewer should NOT be able to create a role (requires team.manage_roles)."""
        _auth(api_client, viewer_user)
        resp = api_client.post("/api/teams/roles/", {
            "name": "My Role", "tenant": str(tenant.id),
        }, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_create_role(self, api_client, admin_user, tenant):
        """Admin is_admin short-circuit passes team.manage_roles."""
        _auth(api_client, admin_user)
        resp = api_client.post("/api/teams/roles/", {
            "name": "Custom Role", "description": "Custom", "tenant": str(tenant.id),
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_view_with_no_required_permission_allows(self, api_client, viewer_user):
        """Views with required_permission=None should not be gated."""
        _auth(api_client, viewer_user)
        # Notes list has no permission requirement
        resp = api_client.get("/api/notes/")
        assert resp.status_code == status.HTTP_200_OK

    def test_unauthenticated_denied_role_permission_direct(self):
        """RolePermission.has_permission returns False for unauthenticated."""
        from django.http import HttpRequest
        perm = RolePermission()
        req = HttpRequest()
        req.user = type("FakeUser", (), {"is_authenticated": False})()
        assert perm.has_permission(req, type("View", (), {})()) is False


# ── Test 2: Cross-App Permission Gates ────────────────────────────────────


class TestCrossAppContactGates:
    """Verify RolePermission enforces contacts CRUD."""

    ACCOUNTS_URL = "/api/contacts/accounts/"

    def test_viewer_cannot_create_account(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.post(self.ACCOUNTS_URL, {"name": "Acme"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_sales_rep_can_create_account(self, api_client, sales_rep_user, tenant):
        _auth(api_client, sales_rep_user)
        resp = api_client.post(self.ACCOUNTS_URL, {"name": "Acme Corp"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_viewer_can_list_accounts(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.get(self.ACCOUNTS_URL)
        assert resp.status_code == status.HTTP_200_OK

    def test_viewer_cannot_delete_account(self, api_client, viewer_user):
        """Viewer lacks contacts.delete."""
        _auth(api_client, viewer_user)
        resp = api_client.delete(f"{self.ACCOUNTS_URL}00000000-0000-0000-0000-000000000001/")
        # 403 before 404 — permission denied first
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete_account(self, api_client, admin_user, tenant):
        """Admin is_admin short-circuit should pass contacts.delete."""
        from apps.contacts.models import Account
        account = Account.objects.create(tenant_id=tenant.id, name="To Delete")
        _auth(api_client, admin_user)
        resp = api_client.delete(f"{self.ACCOUNTS_URL}{account.id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT


class TestCrossAppPipelineGates:
    """Verify RolePermission enforces pipelines CRUD."""

    PIPELINES_URL = "/api/deals/pipelines/"

    def test_viewer_cannot_create_pipeline(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.post(self.PIPELINES_URL, {"name": "New Pipeline"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_can_list_pipelines(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.get(self.PIPELINES_URL)
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_can_create_pipeline(self, api_client, admin_user, tenant):
        _auth(api_client, admin_user)
        resp = api_client.post(self.PIPELINES_URL, {
            "name": "Admin Pipeline", "tenant": str(tenant.id),
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_viewer_cannot_delete_pipeline(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.delete(f"{self.PIPELINES_URL}00000000-0000-0000-0000-000000000001/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestCrossAppActivityGates:
    """Verify RolePermission enforces activities CRUD."""

    ACTIVITIES_URL = "/api/activities/"

    def test_viewer_can_list_activities(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.get(self.ACTIVITIES_URL)
        assert resp.status_code == status.HTTP_200_OK

    def test_viewer_cannot_delete_activity(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.delete(f"{self.ACTIVITIES_URL}00000000-0000-0000-0000-000000000001/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete_activity(self, api_client, admin_user, tenant):
        _auth(api_client, admin_user)
        resp = api_client.delete(f"{self.ACTIVITIES_URL}00000000-0000-0000-0000-000000000001/")
        # 404 not 403 means admin permission passed
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestCrossAppNoteGates:
    """Verify RolePermission enforces notes CRUD."""

    NOTES_URL = "/api/notes/"

    def test_viewer_cannot_create_note(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.post(self.NOTES_URL, {"title": "Note", "content": "body"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_create_note(self, api_client, admin_user, tenant):
        _auth(api_client, admin_user)
        resp = api_client.post(self.NOTES_URL, {
            "title": "Note", "content": "body",
            "entity_type": "contact", "entity_id": "00000000-0000-0000-0000-000000000001",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_viewer_cannot_delete_note(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.delete(f"{self.NOTES_URL}00000000-0000-0000-0000-000000000001/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestCrossAppFileGates:
    """Verify RolePermission enforces file upload."""

    FILES_URL = "/api/files/"

    def test_viewer_cannot_upload_file(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.post(self.FILES_URL, {"file_name": "test.txt"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_upload_file(self, api_client, admin_user, tenant):
        _auth(api_client, admin_user)
        resp = api_client.post(self.FILES_URL, {
            "original_filename": "test.txt",
            "file_key": "uploads/test.txt",
            "file_size": 123,
            "mime_type": "text/plain",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED


class TestCrossAppEmailGates:
    """Verify RolePermission enforces email operations."""

    EMAILS_URL = "/api/emails/"

    def test_viewer_can_list_emails(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.get(self.EMAILS_URL)
        assert resp.status_code == status.HTTP_200_OK


class TestCrossAppReportGates:
    """Verify RolePermission enforces report views."""

    DASHBOARD_URL = "/api/reports/dashboard/"

    def test_viewer_can_view_dashboard(self, api_client, viewer_user):
        _auth(api_client, viewer_user)
        resp = api_client.get(self.DASHBOARD_URL)
        assert resp.status_code == status.HTTP_200_OK


class TestCrossAppExportGates:
    """Verify RolePermission enforces export endpoints."""

    EXPORT_CONTACTS_URL = "/api/export/contacts/"

    def test_viewer_cannot_export_contacts(self, api_client, viewer_user):
        """Viewer lacks contacts.export."""
        _auth(api_client, viewer_user)
        resp = api_client.get(self.EXPORT_CONTACTS_URL)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_export_contacts(self, api_client, admin_user, tenant):
        _auth(api_client, admin_user)
        resp = api_client.get(self.EXPORT_CONTACTS_URL)
        # Admin short-circuit passes — might return 200 or 400 (no data)
        assert resp.status_code in (status.HTTP_200_OK,)


# ── Test 3: Role Management Endpoints ─────────────────────────────────────


class TestRoleManagementEndpoints:
    """CRUD operations on roles via /api/teams/roles/."""

    ROLES_URL = "/api/teams/roles/"

    def test_list_roles_as_viewer(self, api_client, viewer_user, tenant):
        """Listing roles requires no specific permission."""
        # Create some roles
        Role.objects.create(tenant=tenant, name="Role A", is_admin=False)
        Role.objects.create(tenant=tenant, name="Role B", is_admin=False)
        _auth(api_client, viewer_user)
        resp = api_client.get(self.ROLES_URL)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        names = [r["name"] for r in data["results"]]
        assert "Viewer" in names

    def test_create_role_requires_manage_roles(self, api_client, viewer_user, tenant):
        _auth(api_client, viewer_user)
        resp = api_client.post(self.ROLES_URL, {
            "name": "Test Role", "tenant": str(tenant.id),
        }, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_create_role(self, api_client, admin_user, tenant):
        _auth(api_client, admin_user)
        resp = api_client.post(self.ROLES_URL, {
            "name": "Test Role", "tenant": str(tenant.id),
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_partial_update_role_requires_manage_roles(self, api_client, viewer_user, tenant):
        role = Role.objects.create(tenant=tenant, name="Target Role", is_admin=False)
        _auth(api_client, viewer_user)
        resp = api_client.patch(
            f"{self.ROLES_URL}{role.id}/",
            {"description": "Hacked"}, format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_update_role(self, api_client, admin_user, tenant):
        role = Role.objects.create(tenant=tenant, name="Update Role", is_admin=False)
        _auth(api_client, admin_user)
        resp = api_client.patch(
            f"{self.ROLES_URL}{role.id}/",
            {"description": "Updated"}, format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_destroy_role_requires_manage_roles(self, api_client, viewer_user, tenant):
        role = Role.objects.create(tenant=tenant, name="Delete Role", is_admin=False)
        _auth(api_client, viewer_user)
        resp = api_client.delete(f"{self.ROLES_URL}{role.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_destroy_role(self, api_client, admin_user, tenant):
        role = Role.objects.create(tenant=tenant, name="Delete Role", is_admin=False)
        _auth(api_client, admin_user)
        resp = api_client.delete(f"{self.ROLES_URL}{role.id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT


# ── Test 4: Membership Management Endpoints ───────────────────────────────


class TestMembershipManagementEndpoints:
    """PATCH/DELETE/Invite on memberships."""

    MEMBERSHIPS_URL = "/api/teams/memberships/"

    def test_list_members_requires_team_view(self, api_client, viewer_user, tenant):
        """Viewer has team.view in this test's viewer_role fixture."""
        _auth(api_client, viewer_user)
        resp = api_client.get(self.MEMBERSHIPS_URL)
        assert resp.status_code == status.HTTP_200_OK

    def test_update_member_role_requires_manage_roles(self, api_client, viewer_user, tenant):
        """Viewer lacks team.manage_roles → 403."""
        target_user = UserModel.objects.create_user(
            email="target@example.com", username="target",
            password="testpass123", tenant_id=tenant.id,
        )
        target_role = Role.objects.create(tenant=tenant, name="Target Role")
        membership = Membership.objects.create(user=target_user, tenant=tenant, role=target_role)
        _auth(api_client, viewer_user)
        new_role = Role.objects.create(tenant=tenant, name="New Role")
        resp = api_client.patch(
            f"{self.MEMBERSHIPS_URL}{membership.id}/",
            {"role": str(new_role.id)}, format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_update_member_role(self, api_client, admin_user, tenant):
        """Admin has team.manage_roles via is_admin short-circuit."""
        target_user = UserModel.objects.create_user(
            email="target@example.com", username="target",
            password="testpass123", tenant_id=tenant.id,
        )
        target_role = Role.objects.create(tenant=tenant, name="Target Role")
        membership = Membership.objects.create(user=target_user, tenant=tenant, role=target_role)
        _auth(api_client, admin_user)
        new_role = Role.objects.create(tenant=tenant, name="New Role")
        resp = api_client.patch(
            f"{self.MEMBERSHIPS_URL}{membership.id}/",
            {"role": str(new_role.id)}, format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_destroy_member_requires_team_remove(self, api_client, viewer_user, tenant):
        """Viewer lacks team.remove → 403."""
        target_user = UserModel.objects.create_user(
            email="target@example.com", username="target",
            password="testpass123", tenant_id=tenant.id,
        )
        membership = Membership.objects.create(user=target_user, tenant=tenant)
        _auth(api_client, viewer_user)
        resp = api_client.delete(f"{self.MEMBERSHIPS_URL}{membership.id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_invite_new_user_requires_team_invite(self, api_client, viewer_user, tenant):
        """Viewer lacks team.invite → 403."""
        _auth(api_client, viewer_user)
        resp = api_client.post(f"{self.MEMBERSHIPS_URL}invite/", {
            "email": "newuser@example.com",
        }, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_can_invite_user(self, api_client, manager_user, tenant):
        """Manager has team.invite permission."""
        _auth(api_client, manager_user)
        resp = api_client.post(f"{self.MEMBERSHIPS_URL}invite/", {
            "email": "newuser@example.com",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED


# ── Test 5: Role Inheritance Chain ────────────────────────────────────────


class TestRoleInheritanceChain:
    """Depth-2 inheritance: C → B → A."""

    def test_three_level_inheritance(self, tenant):
        """Role C inherits from B which inherits from A."""
        role_a = Role.objects.create(
            tenant=tenant, name="A", is_admin=False,
            permissions={"contacts.view": True, "contacts.create": True},
        )
        role_b = Role.objects.create(
            tenant=tenant, name="B", is_admin=False,
            permissions={"deals.view": True},
            inherits_from=role_a,
        )
        role_c = Role.objects.create(
            tenant=tenant, name="C", is_admin=False,
            permissions={"reports.view": True},
            inherits_from=role_b,
        )
        merged = role_c.resolved_permissions
        assert merged.get("contacts.view") is True  # From A
        assert merged.get("contacts.create") is True  # From A
        assert merged.get("deals.view") is True  # From B
        assert merged.get("reports.view") is True  # From C

    def test_deep_override(self, tenant):
        """Child overrides grandparent permission."""
        role_a = Role.objects.create(
            tenant=tenant, name="A", is_admin=False,
            permissions={"contacts.view": True, "deals.view": True},
        )
        role_b = Role.objects.create(
            tenant=tenant, name="B", is_admin=False,
            permissions={"deals.view": False},
            inherits_from=role_a,
        )
        merged = role_b.resolved_permissions
        assert merged.get("contacts.view") is True  # From A, not overridden
        assert merged.get("deals.view") is False  # B overrides A
        assert merged.get("contacts.create", False) is False  # Not defined

    def test_delete_inherited_role_sets_null(self, tenant):
        """Deleting inherited role should SET_NULL on inherits_from."""
        role_a = Role.objects.create(tenant=tenant, name="A", is_admin=False)
        role_b = Role.objects.create(tenant=tenant, name="B", inherits_from=role_a)
        role_a.delete()
        role_b.refresh_from_db()
        assert role_b.inherits_from is None


# ── Test 6: Tenant Isolation ──────────────────────────────────────────────


class TestRoleTenantIsolation:
    """Roles should be strictly tenant-scoped."""

    def test_role_tenant_isolation(self, tenant, other_tenant):
        """Roles from different tenants should not be visible to each other."""
        Role.objects.create(tenant=tenant, name="Tenant A Role")
        Role.objects.create(tenant=other_tenant, name="Tenant B Role")
        assert Role.objects.filter(tenant=tenant).count() == 1
        assert Role.objects.filter(tenant=other_tenant).count() == 1

    def test_membership_tenant_isolation(self, api_client, tenant, other_tenant, admin_user):
        """User should only see memberships in their tenant."""
        _auth(api_client, admin_user)

        # Create a role and membership in the *other* tenant
        other_role = Role.objects.create(tenant=other_tenant, name="Other Role")
        other_user = UserModel.objects.create_user(
            email="other@example.com", username="other",
            password="testpass123", tenant_id=other_tenant.id,
        )
        Membership.objects.create(user=other_user, tenant=other_tenant, role=other_role)

        # Admin user should only see their own tenant's memeberships
        resp = api_client.get("/api/teams/memberships/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        # Should only contain the admin's own membership
        assert len(data["results"]) == 1


# ── Test 7: Role Me Endpoint with No Membership ───────────────────────────


class TestMembershipsMeEdgeCases:
    """Edge cases for the /me/ endpoint."""

    ME_URL = "/api/teams/memberships/me/"

    def test_no_membership_returns_empty(self, api_client, db, tenant):
        """User with no membership should get empty response, not 500."""
        user = UserModel.objects.create_user(
            email="lonely@example.com", username="lonely",
            password="testpass123", tenant_id=tenant.id,
        )
        _auth(api_client, user)
        resp = api_client.get(self.ME_URL)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["role_name"] is None
        assert data["is_admin"] is False
        assert data["permissions"] == {}

    def test_me_returns_manager_permissions(self, api_client, manager_user):
        """/me/ should return merged (inherited + own) permissions for manager."""
        _auth(api_client, manager_user)
        resp = api_client.get(self.ME_URL)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["role_name"] == "Manager"
        # Inherited from Sales Rep
        assert data["permissions"].get("contacts.view") is True
        assert data["permissions"].get("notes.create") is True
        # Own permissions
        assert data["permissions"].get("team.invite") is True
        assert data["permissions"].get("activities.delete") is True
        # Not present
        assert data["permissions"].get("contacts.export", False) is False


# ── Test 8: Permissions Endpoint ──────────────────────────────────────────


class TestPermissionsEndpointExtended:
    """Extended coverage for the permissions registry endpoint."""

    PERMS_URL = "/api/teams/permissions/"

    def test_returns_all_groups(self, api_client, admin_user):
        _auth(api_client, admin_user)
        resp = api_client.get(self.PERMS_URL)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        expected_groups = {"Contacts", "Deals", "Pipelines", "Activities",
                           "Email", "Notes", "Files", "Reports", "Forecast", "Admin"}
        for g in expected_groups:
            assert g in data["groups"], f"Missing group: {g}"

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(self.PERMS_URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_permissions_count_matches(self, api_client, admin_user):
        """The number of permissions in the response should match the registry."""
        _auth(api_client, admin_user)
        resp = api_client.get(self.PERMS_URL)
        data = resp.json()
        api_count = sum(len(perms) for perms in data["groups"].values())
        assert api_count == len(PermissionRegistry.ALL)

    def test_exact_permission_count(self):
        """Registry should have exactly 37 permissions."""
        assert len(PermissionRegistry.ALL) == 37


# ── Test 9: Accounts RBAC Endpoints ──────────────────────────────────────


class TestAccountsRoleEndpoints:
    """RoleListCreateView under /api/accounts/roles/."""

    ACCOUNTS_ROLES_URL = "/api/accounts/roles/"

    def test_viewer_cannot_create_role_via_accounts(self, api_client, viewer_user, tenant):
        """POST /api/accounts/roles/ requires team.manage_roles."""
        _auth(api_client, viewer_user)
        resp = api_client.post(self.ACCOUNTS_ROLES_URL, {"name": "New Role"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_create_role_via_accounts(self, api_client, admin_user, tenant):
        """Admin short-circuit passes team.manage_roles."""
        _auth(api_client, admin_user)
        resp = api_client.post(self.ACCOUNTS_ROLES_URL, {
            "name": "Custom Role", "description": "Test",
            "tenant": str(tenant.id),
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_viewer_can_list_roles_via_accounts(self, api_client, viewer_user):
        """GET /api/accounts/roles/ requires no specific permission."""
        _auth(api_client, viewer_user)
        resp = api_client.get(self.ACCOUNTS_ROLES_URL)
        assert resp.status_code == status.HTTP_200_OK

    def test_roles_tenant_scoped(self, api_client, admin_user, tenant, other_tenant):
        """Roles from other tenant should not appear."""
        Role.objects.create(tenant=other_tenant, name="Other Tenant Role")
        _auth(api_client, admin_user)
        resp = api_client.get(self.ACCOUNTS_ROLES_URL)
        data = resp.json()
        for role in data["results"]:
            assert str(role["tenant"]) == str(tenant.id)


class TestUserRoleUpdateEndpoint:
    """UserRoleUpdateView under /api/accounts/users/{id}/role/."""

    def test_viewer_cannot_change_role(self, api_client, viewer_user, tenant):
        """PATCH /api/accounts/users/{id}/role/ requires team.manage_roles."""
        target = UserModel.objects.create_user(
            email="target@example.com", username="target",
            password="testpass123", tenant_id=tenant.id,
        )
        target_role = Role.objects.create(tenant=tenant, name="Target")
        Membership.objects.create(user=target, tenant=tenant, role=target_role)
        new_role = Role.objects.create(tenant=tenant, name="Promoted")
        _auth(api_client, viewer_user)
        resp = api_client.patch(
            f"/api/accounts/users/{target.id}/role/",
            {"role_id": str(new_role.id)}, format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_change_role(self, api_client, admin_user, tenant):
        """Admin can change another user's role."""
        target = UserModel.objects.create_user(
            email="target@example.com", username="target",
            password="testpass123", tenant_id=tenant.id,
        )
        target_role = Role.objects.create(tenant=tenant, name="Target")
        Membership.objects.create(user=target, tenant=tenant, role=target_role)
        new_role = Role.objects.create(tenant=tenant, name="Promoted")
        _auth(api_client, admin_user)
        resp = api_client.patch(
            f"/api/accounts/users/{target.id}/role/",
            {"role_id": str(new_role.id)}, format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        # Verify the membership was updated
        membership = Membership.objects.get(user=target, tenant=tenant)
        assert membership.role_id == new_role.id

    def test_change_role_wrong_tenant_404(self, api_client, admin_user, tenant, other_tenant):
        """Changing role in another tenant's membership should 404."""
        other_user = UserModel.objects.create_user(
            email="other@example.com", username="other",
            password="testpass123", tenant_id=other_tenant.id,
        )
        other_role = Role.objects.create(tenant=other_tenant, name="Other Role")
        Membership.objects.create(user=other_user, tenant=other_tenant, role=other_role)
        new_role = Role.objects.create(tenant=other_tenant, name="Promoted")
        _auth(api_client, admin_user)
        resp = api_client.patch(
            f"/api/accounts/users/{other_user.id}/role/",
            {"role_id": str(new_role.id)}, format="json",
        )
        # Admin's tenant doesn't have this membership -> 404
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ── Test 10: Object-Level Tenant Isolation ───────────────────────────────


class TestObjectLevelTenantIsolation:
    """TenantAwarePermission.has_object_permission enforcement."""

    def test_cross_tenant_object_access_denied(self, api_client, admin_user, tenant, other_tenant):
        """Admin from tenant A should not access an object from tenant B."""
        from apps.contacts.models import Account
        account_b = Account.objects.create(tenant_id=other_tenant.id, name="Other's Account")
        _auth(api_client, admin_user)
        resp = api_client.get(f"/api/contacts/accounts/{account_b.id}/")
        # 404 because get_queryset filters by tenant_id first
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_own_tenant_object_accessible(self, api_client, admin_user, tenant):
        """Admin should access objects in their own tenant."""
        from apps.contacts.models import Account
        account = Account.objects.create(tenant_id=tenant.id, name="My Account")
        _auth(api_client, admin_user)
        resp = api_client.get(f"/api/contacts/accounts/{account.id}/")
        assert resp.status_code == status.HTTP_200_OK


# ── Test 11: Membership Edge Cases ───────────────────────────────────────


class TestMembershipEdgeCases:
    """Inactive memberships, null roles, and multi-tenant users."""

    def test_inactive_membership_not_visible(self, api_client, tenant):
        """Inactive membership should not be returned as user.membership."""
        user = UserModel.objects.create_user(
            email="inactive@example.com", username="inactive",
            password="testpass123", tenant_id=tenant.id,
        )
        inactive_role = Role.objects.create(tenant=tenant, name="Inactive Role")
        Membership.objects.create(
            user=user, tenant=tenant, role=inactive_role,
            is_active=False,
        )
        # User has no active membership
        assert user.membership is None

    def test_membership_with_null_role_still_authenticated(self, api_client, tenant):
        """User with membership but null role should still be able to list."""
        user = UserModel.objects.create_user(
            email="nullrole@example.com", username="nullrole",
            password="testpass123", tenant_id=tenant.id,
        )
        Membership.objects.create(user=user, tenant=tenant, role=None)
        _auth(api_client, user)
        resp = api_client.get("/api/teams/roles/")
        assert resp.status_code == status.HTTP_200_OK

    def test_user_has_permission_null_role(self, tenant):
        """has_permission returns False when membership has null role."""
        user = UserModel.objects.create_user(
            email="nullrole2@example.com", username="nullrole2",
            password="testpass123", tenant_id=tenant.id,
        )
        Membership.objects.create(user=user, tenant=tenant, role=None)
        # Force cached_property re-eval
        for attr in ("membership", "role", "permissions"):
            if attr in user.__dict__:
                del user.__dict__[attr]
        assert user.has_permission("contacts.view") is False

    def test_permission_count_never_zero_for_admin(self, api_client, admin_user):
        """Admin should always have all permissions."""
        _auth(api_client, admin_user)
        resp = api_client.get("/api/teams/memberships/me/")
        data = resp.json()
        assert len(data["permissions"]) >= 37
        assert data["is_admin"] is True