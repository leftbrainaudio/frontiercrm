"""Tenant, Team, and Role models for multi-tenant organization."""

from __future__ import annotations

import uuid

from django.db import models


class Tenant(models.Model):
    """Organization / workspace that owns data with row-level isolation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=100, unique=True, blank=True, null=True)
    logo_url = models.URLField(max_length=500, blank=True, default="")
    settings = models.JSONField(default=dict, blank=True)
    industry = models.CharField(max_length=100, blank=True, default="")
    max_users = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teams_tenant"
        indexes = [
            models.Index(fields=["subdomain"]),
        ]

    def __str__(self) -> str:
        return self.name


class Team(models.Model):
    """Group within a tenant for role-based access."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teams_team"
        unique_together = [("tenant", "name")]
        indexes = [
            models.Index(fields=["tenant"]),
        ]

    def __str__(self) -> str:
        return f"{self.tenant.name} / {self.name}"


class Role(models.Model):
    """Permission role within a tenant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="roles")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    permissions = models.JSONField(default=dict, blank=True)
    is_admin = models.BooleanField(default=False)
    inherits_from = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="inheriting_roles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teams_role"
        unique_together = [("tenant", "name")]
        indexes = [
            models.Index(fields=["tenant"]),
        ]

    def __str__(self) -> str:
        return f"{self.tenant.name} / {self.name}"

    @property
    def resolved_permissions(self) -> dict:
        """Merge inherited + own permissions (own wins)."""
        base: dict = {}
        if self.inherits_from:
            base = dict(self.inherits_from.resolved_permissions)
        base.update(self.permissions)
        return base


class Membership(models.Model):
    """User membership in a tenant with role and team assignments."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="memberships")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    is_owner = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "teams_membership"
        unique_together = [("user", "tenant")]
        indexes = [
            models.Index(fields=["tenant", "team"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.tenant.name}"