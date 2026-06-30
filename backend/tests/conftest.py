"""Pytest configuration for FrontierCRM backend tests."""

from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

UserModel = get_user_model()


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def tenant(db) -> "Tenant":
    """Create a basic tenant for tests."""
    from apps.teams.models import Tenant
    return Tenant.objects.create(name=f"Test-Tenant-{uuid.uuid4().hex[:8]}")


@pytest.fixture
def default_role(db, tenant):
    """Create a default role with full permissions for test users."""
    from apps.teams.models import Role
    role = Role.objects.create(
        tenant=tenant,
        name="Test Admin",
        description="Default test role",
        is_admin=True,
        permissions={},
    )
    return role


@pytest.fixture
def user(db, tenant_id) -> UserModel:
    """Create a test user with a tenant and a role."""
    from apps.teams.models import Membership, Role, Tenant
    tenant = Tenant.objects.filter(id=tenant_id).first()
    if not tenant:
        tenant = Tenant.objects.create(id=tenant_id, name=f"Test-{uuid.uuid4().hex[:8]}")
    role = Role.objects.create(
        tenant=tenant,
        name="Test Admin",
        description="Default test role",
        is_admin=True,
        permissions={},
    )
    user = UserModel.objects.create_user(
        email=f"test-{uuid.uuid4().hex[:8]}@frontiercrm.com",
        username=f"testuser-{uuid.uuid4().hex[:8]}",
        password="testpass123",
        tenant_id=tenant_id,
    )
    Membership.objects.create(
        user=user,
        tenant=tenant,
        role=role,
        is_active=True,
    )
    return user


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_client(user, api_client) -> APIClient:
    """Return an API client authenticated with JWT (user has admin role)."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    if user.tenant_id:
        refresh.access_token["tenant_id"] = str(user.tenant_id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client