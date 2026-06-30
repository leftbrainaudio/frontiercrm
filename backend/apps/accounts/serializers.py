"""Serializers for accounts app."""

from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from apps.core.role_defaults import DEFAULT_ROLES
from apps.teams.models import Membership, Role, Team, Tenant

UserModel = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    """User registration serializer — also creates Tenant, default Roles, default Team, and Membership."""

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

        # Create default roles for this tenant
        roles: dict[str, Role] = {}
        for role_def in DEFAULT_ROLES:
            r = Role.objects.create(
                tenant=tenant,
                name=role_def["name"],
                description=role_def["description"],
                permissions=role_def["permissions"],
                is_admin=role_def.get("is_admin", False),
            )
            roles[role_def["name"]] = r

        # Set up inheritance (Manager -> Sales Rep)
        if "Manager" in roles and "Sales Rep" in roles:
            roles["Manager"].inherits_from = roles["Sales Rep"]
            roles["Manager"].save(update_fields=["inherits_from"])

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
            role=roles["Admin"],
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


# ── 2FA / TOTP Serializers ────────────────────────────────────────────────────


class TwoFactorSetupSerializer(serializers.Serializer):
    """Initiate 2FA setup — no input, generates secret and provisioning URI."""


class TwoFactorConfirmSerializer(serializers.Serializer):
    """Confirm 2FA setup with a TOTP code."""

    code = serializers.CharField(min_length=6, max_length=6)

    def validate_code(self, value: str) -> str:
        if not value.strip().isdigit():
            raise serializers.ValidationError("Code must be 6 digits.")
        return value.strip()


class TwoFactorVerifySerializer(serializers.Serializer):
    """Verify 2FA code during login using a 2fa_token."""

    two_factor_token = serializers.CharField(write_only=True, source="2fa_token")
    code = serializers.CharField()
    is_recovery = serializers.BooleanField(default=False, required=False)


class TwoFactorDisableSerializer(serializers.Serializer):
    """Disable 2FA with password + TOTP code."""

    password = serializers.CharField()
    code = serializers.CharField()


class TwoFactorRegenerateSerializer(serializers.Serializer):
    """Regenerate recovery codes with TOTP code verification."""

    code = serializers.CharField()


# ── SAML Serializers ──────────────────────────────────────────────────────────


class SamlProviderSerializer(serializers.ModelSerializer):
    """Create/read/update SAML provider configuration."""

    class Meta:
        model = None  # set at runtime
        fields = (
            "id", "idp_entity_id", "idp_sso_url", "idp_slo_url",
            "idp_x509_cert", "attribute_mapping", "default_role_id",
            "auto_create_users", "allowed_domains", "is_active",
            "sp_entity_id", "acs_url", "last_used_at", "tenant_id",
        )
        read_only_fields = ("id", "sp_entity_id", "acs_url", "last_used_at", "tenant_id")


class SamlLoginSerializer(serializers.Serializer):
    """Start SP-initiated SAML login."""

    email = serializers.EmailField()


class SamlDomainCheckSerializer(serializers.Serializer):
    """Check if an email domain has SAML configured."""

    email = serializers.EmailField()