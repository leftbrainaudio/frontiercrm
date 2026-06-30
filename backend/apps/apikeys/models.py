"""API key model for programmatic / third-party access."""

from __future__ import annotations

import hashlib
import secrets

from django.db import models

from apps.core.models import TenantScopedModel


class APIKey(TenantScopedModel):
    """A named API key for programmatic access to the FrontierCRM API.

    The plaintext key is shown exactly once at creation.
    Only the SHA-256 hash is stored.
    """

    name = models.CharField(max_length=255, help_text="Human-readable label e.g. 'CI Pipeline'")
    key_prefix = models.CharField(
        max_length=16,
        editable=False,
        help_text="First 16 chars of the key for display/identification",
    )
    key_hash = models.CharField(
        max_length=128,
        editable=False,
        unique=True,
        help_text="SHA-256 hash of the full API key",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text="User who created/owns this key",
    )
    permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Override permissions dict — merged on top of the user's role permissions. "
                  "Leave empty to inherit all the user's role permissions.",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If set, the key is rejected after this time",
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Updated on every authenticated request (best-effort, throttled)",
    )
    last_ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the last request using this key",
    )
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If set, the key was explicitly revoked",
    )

    class Meta:
        db_table = "apikeys_key"
        indexes = [
            models.Index(fields=["key_hash"]),
            models.Index(fields=["tenant_id", "is_active"]),
            models.Index(fields=["tenant_id", "user"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.key_prefix}...)"

    def is_expired(self) -> bool:
        """Check if key has passed its expiration date."""
        from django.utils import timezone

        if self.expires_at and self.expires_at < timezone.now():
            return True
        return False

    def is_revoked(self) -> bool:
        """Check if key was explicitly revoked."""
        return self.revoked_at is not None

    @classmethod
    def generate_key(cls) -> str:
        """Generate a new API key in the format: fcrm_<random>"""
        random_part = secrets.token_urlsafe(48)  # 64 chars base64, 384 bits
        return f"fcrm_{random_part}"

    @classmethod
    def hash_key(cls, raw_key: str) -> str:
        """Return SHA-256 hex digest of the raw key."""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def get_key_prefix(cls, raw_key: str) -> str:
        """Return first 16 chars for display purposes."""
        return raw_key[:16]
