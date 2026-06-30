"""Serializers + Viewsets for team management with RBAC."""

from __future__ import annotations

import uuid

from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.core.permission_registry import PermissionRegistry
from apps.core.permissions import RolePermission, TenantAwarePermission

from .models import Membership, Role, Team, Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        exclude = ()
        read_only_fields = ("id", "created_at", "updated_at")


class RoleSerializer(serializers.ModelSerializer):
    resolved_permissions = serializers.ReadOnlyField()

    class Meta:
        model = Role
        exclude = ()
        read_only_fields = ("id", "created_at", "updated_at")


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source="user.email")
    user_name = serializers.SerializerMethodField()
    tenant_name = serializers.ReadOnlyField(source="tenant.name")
    role_name = serializers.ReadOnlyField(source="role.name", default="")
    role_is_admin = serializers.ReadOnlyField(source="role.is_admin", default=False)

    class Meta:
        model = Membership
        exclude = ()
        read_only_fields = ("id", "joined_at")

    def get_user_name(self, obj: Membership) -> str:
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class MembershipMeSerializer(serializers.Serializer):
    """Current user's membership info with resolved permissions."""

    id = serializers.UUIDField()
    role_id = serializers.UUIDField(allow_null=True)
    role_name = serializers.CharField(allow_null=True)
    is_admin = serializers.BooleanField()
    is_owner = serializers.BooleanField()
    permissions = serializers.JSONField()


# ── Views ────────────────────────────────────────────────────────────────


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAdminUser]


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def get_queryset(self):
        return Team.objects.filter(tenant_id=self.request.user.tenant_id)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [TenantAwarePermission, RolePermission]

    def get_queryset(self):
        return Role.objects.filter(tenant_id=self.request.user.tenant_id)

    def get_required_permission(self) -> str | None:
        if self.action in ("create", "update", "partial_update", "destroy"):
            return "team.manage_roles"
        return None  # listing roles requires auth but no specific permission


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [TenantAwarePermission, RolePermission]

    def get_queryset(self):
        return Membership.objects.filter(tenant_id=self.request.user.tenant_id)

    def get_required_permission(self) -> str | None:
        action_map = {
            "list": "team.view",
            "partial_update": "team.manage_roles",
            "update": "team.manage_roles",
            "destroy": "team.remove",
        }
        return action_map.get(self.action)

    @action(detail=False, methods=["get"])
    def me(self, request) -> Response:
        """Return current user's membership with resolved permissions.

        GET /api/teams/memberships/me/
        """
        membership = Membership.objects.filter(
            user=request.user,
            tenant_id=request.user.tenant_id,
            is_active=True,
        ).select_related("role").first()

        if not membership:
            return Response({
                "id": None,
                "role_id": None,
                "role_name": None,
                "is_admin": False,
                "is_owner": False,
                "permissions": {},
            })

        role = membership.role
        if role and role.is_admin:
            perms = {k: True for k in PermissionRegistry.all_keys()}
        elif role:
            perms = role.resolved_permissions
        else:
            perms = {}

        return Response({
            "id": membership.id,
            "role_id": role.id if role else None,
            "role_name": role.name if role else None,
            "is_admin": role.is_admin if role else False,
            "is_owner": membership.is_owner,
            "permissions": perms,
        })

    @action(detail=False, methods=["post"])
    def invite(self, request) -> Response:
        """Invite a user to the tenant. Requires team.invite permission."""
        if not request.user.has_permission("team.invite"):
            return Response({"error": "Permission denied"}, status=403)

        email = request.data.get("email")
        role_id = request.data.get("role_id")
        if not email:
            return Response({"error": "email required"}, status=400)

        # Resolve role: accept UUID or role name
        resolved_role_id = None
        if role_id:
            try:
                uuid.UUID(str(role_id))
                resolved_role_id = role_id
            except (ValueError, AttributeError):
                role = Role.objects.filter(
                    tenant_id=request.user.tenant_id,
                    name__iexact=str(role_id),
                ).first()
                resolved_role_id = role.id if role else None

        user, _ = User.objects.get_or_create(email=email, defaults={"username": email.split("@")[0]})
        membership, created = Membership.objects.get_or_create(
            user=user,
            tenant_id=request.user.tenant_id,
            defaults={"role_id": resolved_role_id},
        )
        return Response(MembershipSerializer(membership).data, status=201 if created else 200)


class PermissionViewSet(viewsets.ViewSet):
    """Read-only endpoint for the permission registry."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """GET /api/teams/permissions/ — list all available permissions."""
        groups = PermissionRegistry.all_by_group()
        result = {}
        for group_name, perms in groups.items():
            result[group_name] = [
                {"key": p.key, "label": p.label, "description": p.description}
                for p in perms
            ]
        return Response({"groups": result})