"""DRF authentication backend for API key authentication."""

from __future__ import annotations

import hashlib
from typing import Any

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request


class APIKeyAuthentication(BaseAuthentication):
    """Authenticate requests using an API key in the Authorization header.

    Header format: Authorization: Bearer fcrm_<key>

    If the token doesn't start with 'fcrm_', we skip authentication
    (allowing SimpleJWT to handle it via the fallback chain).
    """

    keyword = "Bearer"

    def authenticate(self, request: Request) -> tuple[Any, dict] | None:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer fcrm_"):
            return None  # Let SimpleJWT handle it

        raw_key = auth_header.removeprefix("Bearer ").strip()

        # Hash and look up
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        from .models import APIKey

        try:
            api_key = APIKey.objects.select_related("user").get(
                key_hash=key_hash,
                is_active=True,
                revoked_at__isnull=True,
            )
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key.")

        # Check expiry
        if api_key.is_expired():
            raise AuthenticationFailed("API key has expired.")

        # Update last_used_at (best-effort, avoid write on every request)
        now = timezone.now()
        if api_key.last_used_at is None or (now - api_key.last_used_at).total_seconds() > 300:
            api_key.last_used_at = now
            api_key.last_ip_address = request.META.get("REMOTE_ADDR")
            api_key.save(update_fields=["last_used_at", "last_ip_address"])

        user = api_key.user

        # Tag the user so downstream code can distinguish API key auth from JWT auth
        user._api_key_auth = True
        user._api_key_permissions = api_key.permissions
        user._api_key_id = str(api_key.id)

        return (user, {"auth_type": "api_key", "api_key_id": str(api_key.id)})
