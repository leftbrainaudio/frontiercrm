"""Tests for team management endpoints — CRUD, isolation, invite, constraints."""

from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.teams.models import Membership, Role, Team, Tenant

UserModel = get_user_model()

TEAMS_URL = "/api/teams/teams/"
ROLES_URL = "/api/teams/roles/"
MEMBERSHIPS_URL = "/api/teams/memberships/"
TENANTS_URL = "/api/teams/tenants/"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _create_tenant(name: str = "Acme Corp") -> Tenant:
    return Tenant.objects.create(
        id=uuid.uuid4(),
        name=name,
        subdomain=name.lower().replace(" ", "-"),
    )


@pytest.fixture
def tenant(db) -> Tenant:
    return _create_tenant("Test Tenant")


@pytest.fixture
def tenant_b(db) -> Tenant:
    return _create_tenant("Other Tenant")


@pytest.fixture
def user_with_tenant(db, tenant) -> UserModel:
    """Create a normal (non-staff) user belonging to *tenant*."""
    uid = uuid.uuid4()
    return UserModel.objects.create_user(
        email=f"user-{uid.hex[:8]}@frontiercrm.com",
        username=f"user-{uid.hex[:8]}",
        password="testpass123",
        tenant_id=tenant.id,
    )


@pytest.fixture
def staff_user(db, tenant) -> UserModel:
    """Create a staff user belonging to *tenant*."""
    uid = uuid.uuid4()
    return UserModel.objects.create_user(
        email=f"staff-{uid.hex[:8]}@frontiercrm.com",
        username=f"staff-{uid.hex[:8]}",
        password="testpass123",
        tenant_id=tenant.id,
        is_staff=True,
    )


@pytest.fixture
def auth_client_with_tenant(user_with_tenant, api_client):
    """Authenticated client for a non-staff user with a real Tenant."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user_with_tenant)
    refresh.access_token["tenant_id"] = str(user_with_tenant.tenant_id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    # Attach user for convenience
    api_client.user = user_with_tenant
    api_client.tenant_id = user_with_tenant.tenant_id
    return api_client


@pytest.fixture
def staff_auth_client(staff_user, api_client):
    """Authenticated client for a staff user."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(staff_user)
    refresh.access_token["tenant_id"] = str(staff_user.tenant_id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    api_client.user = staff_user
    api_client.tenant_id = staff_user.tenant_id
    return api_client


@pytest.fixture(autouse=True)
def _use_db(db):
    """Ensure every test gets the database."""
    pass


# ── Team CRUD ────────────────────────────────────────────────────────────────


class TestTeamCRUD:
    """Team list / create / update."""

    def test_list_teams(self, auth_client_with_tenant, tenant):
        Team.objects.create(tenant=tenant, name="Engineering")
        Team.objects.create(tenant=tenant, name="Sales")

        resp = auth_client_with_tenant.get(TEAMS_URL)
        assert resp.status_code == status.HTTP_200_OK
        names = [t["name"] for t in resp.data["results"]]
        assert "Engineering" in names
        assert "Sales" in names

    def test_create_team(self, auth_client_with_tenant, tenant):
        resp = auth_client_with_tenant.post(
            TEAMS_URL,
            {"name": "Engineering", "tenant": str(tenant.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["name"] == "Engineering"
        assert Team.objects.count() == 1

    def test_create_team_missing_name(self, auth_client_with_tenant, tenant):
        resp = auth_client_with_tenant.post(
            TEAMS_URL,
            {"tenant": str(tenant.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_team(self, auth_client_with_tenant, tenant):
        team = Team.objects.create(tenant=tenant, name="Engineering")
        resp = auth_client_with_tenant.patch(
            f"{TEAMS_URL}{team.id}/",
            {"name": "Engineering Pro"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        team.refresh_from_db()
        assert team.name == "Engineering Pro"


# ── Role CRUD ────────────────────────────────────────────────────────────────


class TestRoleCRUD:
    """Role list / create / update / filter-by-tenant."""

    def test_list_roles(self, auth_client_with_tenant, tenant):
        Role.objects.create(tenant=tenant, name="Admin", is_admin=True)
        Role.objects.create(tenant=tenant, name="Editor")

        resp = auth_client_with_tenant.get(ROLES_URL)
        assert resp.status_code == status.HTTP_200_OK
        names = [r["name"] for r in resp.data["results"]]
        assert "Admin" in names
        assert "Editor" in names

    def test_create_role(self, auth_client_with_tenant, tenant):
        resp = auth_client_with_tenant.post(
            ROLES_URL,
            {
                "name": "Admin",
                "tenant": str(tenant.id),
                "permissions": {"can_manage_users": True},
                "is_admin": True,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["name"] == "Admin"
        assert resp.data["is_admin"] is True
        assert resp.data["permissions"] == {"can_manage_users": True}

    def test_update_role(self, auth_client_with_tenant, tenant):
        role = Role.objects.create(tenant=tenant, name="Admin")
        resp = auth_client_with_tenant.patch(
            f"{ROLES_URL}{role.id}/",
            {"name": "Super Admin", "is_admin": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        role.refresh_from_db()
        assert role.name == "Super Admin"
        assert role.is_admin is True

    def test_roles_filtered_by_tenant(self, auth_client_with_tenant, tenant, tenant_b):
        """Roles from *tenant* appear, roles from *tenant_b* do not."""
        Role.objects.create(tenant=tenant, name="Tenant-A-Role")
        Role.objects.create(tenant=tenant_b, name="Tenant-B-Role")

        resp = auth_client_with_tenant.get(ROLES_URL)
        assert resp.status_code == status.HTTP_200_OK
        names = [r["name"] for r in resp.data["results"]]
        assert "Tenant-A-Role" in names
        assert "Tenant-B-Role" not in names


# ── Membership CRUD ──────────────────────────────────────────────────────────


class TestMembershipCRUD:
    """Membership list / create / field verification."""

    def test_list_memberships(self, auth_client_with_tenant, tenant, user_with_tenant):
        role = Role.objects.create(tenant=tenant, name="Member")
        Membership.objects.create(
            user=user_with_tenant, tenant=tenant, role=role
        )

        resp = auth_client_with_tenant.get(MEMBERSHIPS_URL)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) >= 1

    def test_create_membership(self, auth_client_with_tenant, tenant, user_with_tenant):
        role = Role.objects.create(tenant=tenant, name="Member")
        resp = auth_client_with_tenant.post(
            MEMBERSHIPS_URL,
            {
                "user": str(user_with_tenant.id),
                "tenant": str(tenant.id),
                "role": str(role.id),
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert Membership.objects.count() == 1

    def test_membership_fields(self, auth_client_with_tenant, tenant, user_with_tenant):
        """Verify user_email, tenant_name, role_name appear in response."""
        role = Role.objects.create(tenant=tenant, name="Manager")
        membership = Membership.objects.create(
            user=user_with_tenant, tenant=tenant, role=role
        )

        resp = auth_client_with_tenant.get(f"{MEMBERSHIPS_URL}{membership.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["user_email"] == user_with_tenant.email
        assert resp.data["tenant_name"] == tenant.name
        assert resp.data["role_name"] == role.name


# ── Tenant CRUD (staff-only) ────────────────────────────────────────────────


class TestTenantCRUD:
    """Tenant endpoints require IsAdminUser — 403 for non-staff."""

    def test_list_tenants_requires_staff(self, auth_client_with_tenant):
        resp = auth_client_with_tenant.get(TENANTS_URL)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_create_tenant_requires_staff(self, auth_client_with_tenant):
        resp = auth_client_with_tenant.post(
            TENANTS_URL,
            {"name": "Rogue Tenant"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_staff_can_list_tenants(self, staff_auth_client):
        resp = staff_auth_client.get(TENANTS_URL)
        assert resp.status_code == status.HTTP_200_OK

    def test_staff_can_create_tenant(self, staff_auth_client):
        resp = staff_auth_client.post(
            TENANTS_URL,
            {"name": "Official Tenant"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert Tenant.objects.filter(name="Official Tenant").exists()

    def test_staff_can_update_tenant(self, staff_auth_client, tenant):
        resp = staff_auth_client.patch(
            f"{TENANTS_URL}{tenant.id}/",
            {"name": "Updated Corp"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        tenant.refresh_from_db()
        assert tenant.name == "Updated Corp"


# ── Invite Action ────────────────────────────────────────────────────────────


class TestInvite:
    """POST /api/teams/memberships/invite/ with email and role_id."""

    def test_invite_new_user(self, auth_client_with_tenant, tenant):
        role = Role.objects.create(tenant=tenant, name="Member")
        resp = auth_client_with_tenant.post(
            f"{MEMBERSHIPS_URL}invite/",
            {"email": "newuser@example.com", "role_id": str(role.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["user_email"] == "newuser@example.com"
        assert resp.data["tenant_name"] == tenant.name
        assert Membership.objects.count() == 1

    def test_invite_existing_user(self, auth_client_with_tenant, tenant):
        """Inviting the same email twice returns 200 and the existing membership."""
        role = Role.objects.create(tenant=tenant, name="Member")
        # First invite
        auth_client_with_tenant.post(
            f"{MEMBERSHIPS_URL}invite/",
            {"email": "existing@example.com", "role_id": str(role.id)},
            format="json",
        )
        # Second invite
        resp = auth_client_with_tenant.post(
            f"{MEMBERSHIPS_URL}invite/",
            {"email": "existing@example.com", "role_id": str(role.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert Membership.objects.count() == 1

    def test_invite_missing_email(self, auth_client_with_tenant):
        resp = auth_client_with_tenant.post(
            f"{MEMBERSHIPS_URL}invite/",
            {"role_id": str(uuid.uuid4())},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in resp.data.get("error", "").lower()

    def test_invite_requires_auth(self, api_client):
        resp = api_client.post(
            f"{MEMBERSHIPS_URL}invite/",
            {"email": "anon@example.com"},
            format="json",
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ── Multi-Tenant Isolation ───────────────────────────────────────────────────


class TestMultiTenantIsolation:
    """Users in tenant A cannot see data belonging to tenant B."""

    def test_team_isolation(self, auth_client_with_tenant, tenant, tenant_b):
        Team.objects.create(tenant=tenant, name="Tenant-A-Team")
        Team.objects.create(tenant=tenant_b, name="Tenant-B-Team")

        resp = auth_client_with_tenant.get(TEAMS_URL)
        assert resp.status_code == status.HTTP_200_OK
        names = [t["name"] for t in resp.data["results"]]
        assert "Tenant-A-Team" in names
        assert "Tenant-B-Team" not in names

    def test_role_isolation(self, auth_client_with_tenant, tenant, tenant_b):
        Role.objects.create(tenant=tenant, name="Tenant-A-Role")
        Role.objects.create(tenant=tenant_b, name="Tenant-B-Role")

        resp = auth_client_with_tenant.get(ROLES_URL)
        assert resp.status_code == status.HTTP_200_OK
        names = [r["name"] for r in resp.data["results"]]
        assert "Tenant-A-Role" in names
        assert "Tenant-B-Role" not in names

    def test_membership_isolation(self, auth_client_with_tenant, tenant, tenant_b, user_with_tenant):
        """User belongs to tenant A; memberships in tenant B should be invisible."""
        uid_b = uuid.uuid4()
        user_b = UserModel.objects.create_user(
            email=f"user-b-{uid_b.hex[:8]}@example.com",
            username=f"user-b-{uid_b.hex[:8]}",
            password="testpass123",
            tenant_id=tenant_b.id,
        )
        Membership.objects.create(user=user_with_tenant, tenant=tenant)
        Membership.objects.create(user=user_b, tenant=tenant_b)

        resp = auth_client_with_tenant.get(MEMBERSHIPS_URL)
        assert resp.status_code == status.HTTP_200_OK
        # Should only see the membership for tenant A
        for m in resp.data["results"]:
            assert m["tenant_name"] == tenant.name


# ── Unique Together Constraints ──────────────────────────────────────────────


class TestUniqueTogether:
    """Verify that duplicate (tenant, name) pairs are rejected for Team and Role,
    and (user, tenant) pairs for Membership."""

    def test_duplicate_team_name_in_tenant(self, auth_client_with_tenant, tenant):
        Team.objects.create(tenant=tenant, name="Engineering")
        resp = auth_client_with_tenant.post(
            TEAMS_URL,
            {"name": "Engineering", "tenant": str(tenant.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_same_team_name_allowed_different_tenant(self, api_client, tenant, tenant_b):
        """Same name in different tenants is allowed (no conflict)."""
        Team.objects.create(tenant=tenant, name="Engineering")
        Team.objects.create(tenant=tenant_b, name="Engineering")
        assert Team.objects.count() == 2

    def test_duplicate_role_name_in_tenant(self, auth_client_with_tenant, tenant):
        Role.objects.create(tenant=tenant, name="Admin")
        resp = auth_client_with_tenant.post(
            ROLES_URL,
            {"name": "Admin", "tenant": str(tenant.id)},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_membership_user_tenant(self, auth_client_with_tenant, tenant, user_with_tenant):
        role = Role.objects.create(tenant=tenant, name="Member")
        Membership.objects.create(user=user_with_tenant, tenant=tenant, role=role)
        resp = auth_client_with_tenant.post(
            MEMBERSHIPS_URL,
            {
                "user": str(user_with_tenant.id),
                "tenant": str(tenant.id),
                "role": str(role.id),
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST