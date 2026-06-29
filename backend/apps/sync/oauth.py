"""Gmail OAuth 2.0 flow — auth URL generation and callback handling."""
from __future__ import annotations

import json
import secrets
from typing import Any
from urllib.parse import urlencode

import requests
from django.conf import settings

# State token stored in cache
STATE_CACHE_PREFIX = "gmail_oauth_state:"
STATE_TTL = 600  # 10 minutes


def generate_oauth_url() -> dict[str, Any]:
    """Generate a Gmail OAuth URL with a state token.

    Stores the state token in Redis (via Django cache) for 10 minutes.

    Returns:
        dict with 'url' and 'state' keys
    """
    state = secrets.token_urlsafe(32)
    client_id = _get_client_id()
    redirect_uri = _get_redirect_uri()
    scopes = ["https://www.googleapis.com/auth/gmail.modify"]

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"

    # Store state in cache
    _store_state(state)

    return {"url": url, "state": state}


def handle_oauth_callback(code: str, state: str, tenant_id: str, user_id: str) -> dict[str, Any]:
    """Handle the Gmail OAuth callback.

    Verifies the state token, exchanges the auth code for tokens,
    and creates a SyncConnection record.

    Args:
        code: The authorization code from Google
        state: The state token for CSRF verification
        tenant_id: CRM tenant ID
        user_id: CRM user ID

    Returns:
        dict with connection details
    """
    # Verify state token
    if not _verify_state(state):
        raise ValueError("Invalid or expired state token")

    # Exchange authorization code for tokens
    token_data = _exchange_code(code)
    if not token_data:
        raise ValueError("Failed to exchange authorization code for tokens")

    access_token = token_data.get("access_token", "")
    refresh_token = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", 3600)

    # Get user email from Gmail profile
    email = _get_user_email(access_token)

    # Create SyncConnection
    from apps.sync.models import SyncConnection

    from django.utils import timezone as tz

    connection = SyncConnection.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        provider="gmail",
        provider_account=email,
        account_type="personal",
        access_token_encrypted=access_token,
        refresh_token_encrypted=refresh_token or "",
        token_expires_at=tz.now() + tz.timedelta(seconds=expires_in),
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
        status="active",
        is_active=True,
    )

    # Create SyncState
    from apps.sync.models import SyncState

    SyncState.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        connection=connection,
        sync_type="email",
        provider="gmail",
        state="pending",
        cursor_data={},
    )

    # Enqueue initial full sync
    from apps.sync.tasks import sync_email_delta

    sync_email_delta.delay(connection_id=str(connection.id), trigger="initial_oauth")

    return {
        "id": str(connection.id),
        "provider": "gmail",
        "email": email,
        "status": "syncing",
    }


def _get_client_id() -> str:
    return getattr(settings, "GOOGLE_CLIENT_ID", "")


def _get_client_secret() -> str:
    return getattr(settings, "GOOGLE_CLIENT_SECRET", "")


def _get_redirect_uri() -> str:
    return getattr(settings, "GMail_REDIRECT_URI", getattr(settings, "GOOGLE_REDIRECT_URI", ""))


def _store_state(state: str) -> None:
    """Store OAuth state token in cache for verification."""
    from django.core.cache import cache

    cache.set(f"{STATE_CACHE_PREFIX}{state}", True, timeout=STATE_TTL)


def _verify_state(state: str) -> bool:
    """Verify that a state token exists and is valid, then delete it (one-time use)."""
    from django.core.cache import cache

    key = f"{STATE_CACHE_PREFIX}{state}"
    if not cache.get(key):
        return False
    cache.delete(key)
    return True


def _exchange_code(code: str) -> dict[str, Any] | None:
    """Exchange an authorization code for OAuth tokens."""
    try:
        resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": _get_client_id(),
                "client_secret": _get_client_secret(),
                "redirect_uri": _get_redirect_uri(),
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except requests.RequestException:
        return None


def _get_user_email(access_token: str) -> str:
    """Fetch the user's Gmail email address from the token's profile."""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/profile",
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("emailAddress", "unknown@unknown.com")
    except requests.RequestException:
        pass
    return "unknown@unknown.com"