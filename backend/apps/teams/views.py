"""Serializers + Viewsets for team management."""

from __future__ import annotations

from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.accounts.models import User

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
    class Meta:
        model = Role
        exclude = ()
        read_only_fields = ("id", "created_at", "updated_at")


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source="user.email")
    tenant_name = serializers.ReadOnlyField(source="tenant.name")
    role_name = serializers.ReadOnlyField(source="role.name", default="")

    class Meta:
        model = Membership
        exclude = ()
        read_only_fields = ("id", "joined_at")


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

    def get_queryset(self):
        return Role.objects.filter(tenant_id=self.request.user.tenant_id)


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

    def get_queryset(self):
        return Membership.objects.filter(tenant_id=self.request.user.tenant_id)

    @action(detail=False, methods=["post"])
    def invite(self, request) -> Response:
        """Invite a user to the tenant."""
        email = request.data.get("email")
        role_id = request.data.get("role_id")
        if not email:
            return Response({"error": "email required"}, status=400)

        user, _ = User.objects.get_or_create(email=email, defaults={"username": email.split("@")[0]})
        membership, created = Membership.objects.get_or_create(
            user=user,
            tenant_id=request.user.tenant_id,
            defaults={"role_id": role_id},
        )
        return Response(MembershipSerializer(membership).data, status=201 if created else 200)
