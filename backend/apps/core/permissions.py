"""Base permissions with multi-tenant isolation."""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class TenantAwarePermission(BasePermission):
    """Enforce that users can only access records belonging to their tenant."""

    def has_permission(self, request: Request, view: Any) -> bool:
        """User must be authenticated and have a tenant."""
        if not request.user or not request.user.is_authenticated:
            return False
        # Public or auth endpoints bypass tenant check
        if getattr(view, "permission_bypass_tenant", False):
            return True
        return bool(request.user.tenant_id)

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Ensure the object belongs to the user's tenant."""
        if not request.user or not request.user.is_authenticated:
            return False
        obj_tenant_id = getattr(obj, "tenant_id", None)
        if obj_tenant_id is None:
            return True  # Non-tenant model
        return str(obj_tenant_id) == str(request.user.tenant_id)


class IsOwnerOrAdmin(BasePermission):
    """Object-level permission — owner or admin."""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return obj.owner == request.user or request.user.is_staff
