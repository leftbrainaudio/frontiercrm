"""Serializers for accounts app."""

from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from apps.teams.models import Membership, Role, Team, Tenant

UserModel = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    """User registration serializer — also creates Tenant, default Role, default Team, and Membership."""

    password = serializers.CharField(write_only=True, min_length=8)
    organization_name = serializers.CharField(write_only=True, required=False, help_text="Name of the tenant/organization")

    class Meta:
        model = UserModel
        fields = ("id", "email", "username", "password", "first_name", "last_name", "tenant_id", "organization_name")
        read_only_fields = ("id", "tenant_id")

    def create(self, validated_data: dict[str, Any]) -> Any:
        password = validated_data.pop("password")
        org_name = validated_data.pop("organization_name", None)

        # Create tenant with a display name
        email = validated_data.get("email", "user@unknown")
        tenant_name = org_name or f"{email.split('@')[0]}'s Organization"
        tenant = Tenant.objects.create(name=tenant_name)

        # Create default admin role for this tenant
        admin_role = Role.objects.create(
            tenant=tenant,
            name="Admin",
            description="Full administrative access",
            is_admin=True,
            permissions={
                "manage_team": True,
                "manage_billing": True,
                "manage_settings": True,
                "export_data": True,
            },
        )

        # Create default team for this tenant
        default_team = Team.objects.create(
            tenant=tenant,
            name="Everyone",
            description="Default team — all members",
        )

        # Create the user
        user = UserModel(**validated_data, tenant_id=tenant.id)
        user.set_password(password)
        user.save()

        # Create membership linking user -> tenant with admin role
        Membership.objects.create(
            user=user,
            tenant=tenant,
            role=admin_role,
            team=default_team,
            is_owner=True,
        )

        return user


class UserSerializer(serializers.ModelSerializer):
    """Read/write serializer for User model."""

    class Meta:
        model = UserModel
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar_url",
            "phone",
            "timezone",
            "locale",
            "email_verified",
            "is_onboarded",
            "tenant_id",
            "is_active",
            "date_joined",
            "last_activity_at",
        )
        read_only_fields = ("id", "tenant_id", "date_joined", "last_activity_at")


class LoginSerializer(serializers.Serializer):
    """Login with email + password."""

    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        user = authenticate(email=data["email"], password=data["password"])
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled.")
        data["user"] = user
        return data


class MagicLinkRequestSerializer(serializers.Serializer):
    """Request a magic link via email."""

    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        try:
            UserModel.objects.get(email=value)
        except UserModel.DoesNotExist:
            raise serializers.ValidationError("No account with this email.") from None
        return value


class MagicLinkConfirmSerializer(serializers.Serializer):
    """Confirm a magic link token."""

    token = serializers.CharField()

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        user = authenticate(magic_link_token=data["token"])
        if user is None:
            raise serializers.ValidationError("Invalid or expired token.")
        data["user"] = user
        return data
