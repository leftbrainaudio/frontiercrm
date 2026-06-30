"""Base permissions with multi-tenant isolation and role-based access."""

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


class RolePermission(BasePermission):
    """
    Role-based permission check. View must declare a `required_permission` attribute
    or a `get_required_permission` method.

    Usage:
        class DealViewSet(viewsets.ModelViewSet):
            permission_classes = [TenantAwarePermission, RolePermission]
            required_permission = "deals.view"

            def get_required_permission(self):
                action_map = {
                    "list": "deals.view",
                    "retrieve": "deals.view",
                    "create": "deals.create",
                    "update": "deals.edit",
                    "partial_update": "deals.edit",
                    "destroy": "deals.delete",
                }
                return action_map.get(self.action, "deals.view")
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Resolve the required permission key from the view
        required: str | None = None
        if hasattr(view, "get_required_permission"):
            required = view.get_required_permission()
        elif hasattr(view, "required_permission"):
            required = view.required_permission

        if required is None:
            return True  # No permission required — allow through

        if required == "__admin__":
            r = user.role
            return r.is_admin if r else False

        return user.has_permission(required)