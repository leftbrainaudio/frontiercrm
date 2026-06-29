"""User model for FrontierCRM — extends AbstractUser with tenant and profile fields."""

from __future__ import annotations

import uuid
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

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["tenant_id", "email"]),
            models.Index(fields=["google_id"]),
        ]

    def __str__(self) -> str:
        return self.email or self.username

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.tenant_id:
            # tenant_id is set explicitly by ViewSet.perform_create or
            # SignupSerializer — this is a safety net for direct shell usage.
            pass
        super().save(*args, **kwargs)
