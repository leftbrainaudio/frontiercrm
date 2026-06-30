"""User model for FrontierCRM — extends AbstractUser with tenant and profile fields."""

from __future__ import annotations

import uuid
from functools import cached_property
from typing import Any

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with tenant-scoped identity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, null=True, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    timezone = models.CharField(max_length=50, default="UTC")
    locale = models.CharField(max_length=10, default="en-US")
    email_verified = models.BooleanField(default=False)
    is_onboarded = models.BooleanField(default=False)
    onboarded_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    # Magic link auth
    magic_link_token = models.CharField(max_length=128, blank=True, default="")
    magic_link_created_at = models.DateTimeField(null=True, blank=True)
    # Google OAuth
    google_id = models.CharField(max_length=100, blank=True, default="")
    google_access_token = models.TextField(blank=True, default="")
    google_refresh_token = models.TextField(blank=True, default="")
    gmail_history_id = models.CharField(max_length=100, blank=True, default="")
    # Microsoft OAuth
    microsoft_id = models.CharField(max_length=100, blank=True, default="")
    microsoft_access_token = models.TextField(blank=True, default="")
    microsoft_refresh_token = models.TextField(blank=True, default="")
    # ── 2FA / TOTP ───────────────────────────────────────────────────────────
    totp_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=64, blank=True, default="")
    totp_created_at = models.DateTimeField(null=True, blank=True)
    recovery_codes = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["tenant_id", "email"]),
            models.Index(fields=["google_id"]),
            models.Index(fields=["microsoft_id"]),
        ]

    def __str__(self) -> str:
        return self.email or self.username

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.tenant_id:
            # tenant_id is set explicitly by ViewSet.perform_create or
            # SignupSerializer — this is a safety net for direct shell usage.
            pass
        super().save(*args, **kwargs)

    # ── RBAC helpers ──────────────────────────────────────────────────────

    @cached_property
    def membership(self) -> Any | None:
        """Get active membership for current tenant."""
        return self.memberships.filter(
            tenant_id=self.tenant_id, is_active=True
        ).select_related("role", "role__inherits_from").first()

    @cached_property
    def role(self) -> Any | None:
        """Get effective role for current tenant."""
        m = self.membership
        return m.role if m else None

    @cached_property
    def permissions(self) -> dict:
        """Get resolved permissions dict for current tenant's role.

        When the request was authenticated via API key, the key's scoped
        permissions are merged on top of the role permissions — key settings
        override role-level settings.
        """
        if not self.role:
            base: dict = {}
        elif self.role.is_admin:
            from apps.core.permission_registry import PermissionRegistry

            base = {k: True for k in PermissionRegistry.all_keys()}
        else:
            base = self.role.resolved_permissions

        # API key scope overrides role permissions when present
        if hasattr(self, "_api_key_permissions") and self._api_key_permissions:
            return {**base, **self._api_key_permissions}
        return base

    def has_permission(self, key: str) -> bool:
        """Check if user has a specific permission key."""
        return self.permissions.get(key, False)


class TenantScopedModel(models.Model):
    """Abstract base for models scoped to a tenant via tenant_id UUID."""

    tenant_id = models.UUIDField(db_index=True)

    class Meta:
        abstract = True


class SamlProvider(TenantScopedModel):
    """SAML 2.0 identity provider configuration, scoped to a tenant."""

    # Identity Provider metadata
    idp_entity_id = models.CharField(max_length=500, help_text="IdP Entity ID (issuer)")
    idp_sso_url = models.URLField(max_length=500, help_text="IdP Single Sign-On URL (HTTP-Redirect binding)")
    idp_slo_url = models.URLField(max_length=500, blank=True, default="", help_text="IdP Single Logout URL (optional)")
    idp_x509_cert = models.TextField(help_text="IdP X.509 certificate (PEM format)")

    # Attribute mapping — SAML attribute names → User model fields
    attribute_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text='SAML attribute mapping. E.g. {"email": "email", "first_name": "firstName"}',
    )

    # Service Provider settings
    sp_entity_id = models.CharField(max_length=500, help_text="SP Entity ID (auto-generated)")
    acs_url = models.URLField(max_length=500, help_text="Assertion Consumer Service URL (auto-generated)")
    audience = models.URLField(max_length=500, blank=True, default="", help_text="Optional: restrict to a specific IdP audience")

    # JIT provisioning
    default_role_id = models.UUIDField(null=True, blank=True, help_text="Role UUID assigned to JIT-provisioned users")
    auto_create_users = models.BooleanField(
        default=True,
        help_text="Automatically create user accounts on SAML login from this IdP",
    )
    allowed_domains = models.JSONField(
        default=list,
        blank=True,
        help_text="Restrict SAML login to specific email domains. Empty list = allow any domain.",
    )

    # Status
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_saml_provider"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id"],
                condition=models.Q(is_active=True),
                name="uq_active_saml_provider_per_tenant",
            ),
        ]

    def __str__(self) -> str:
        return f"SAML({self.idp_entity_id}) for tenant {self.tenant_id}"

    def save(self, *args, **kwargs):
        from django.conf import settings

        if not self.sp_entity_id:
            self.sp_entity_id = f"{settings.SAML_BASE_URL}/api/auth/saml/{self.tenant_id}/metadata/"
        if not self.acs_url:
            self.acs_url = f"{settings.SAML_BASE_URL}/api/auth/saml/{self.tenant_id}/acs/"
        super().save(*args, **kwargs)

    def get_sp_settings(self) -> dict:
        """Return the SP configuration dict for python3-saml."""
        return {
            "strict": True,
            "sp": {
                "entityId": self.sp_entity_id,
                "assertionConsumerService": {
                    "url": self.acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": self.idp_slo_url or "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
            },
            "idp": {
                "entityId": self.idp_entity_id,
                "singleSignOnService": {
                    "url": self.idp_sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "singleLogoutService": {
                    "url": self.idp_slo_url or "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": self.idp_x509_cert,
            },
        }