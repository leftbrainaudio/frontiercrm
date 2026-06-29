"""Gmail API client wrapper with auth, rate limiting, and retry logic."""
from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class GmailApiError(Exception):
    """Base error for Gmail API operations."""


class GmailAuthError(GmailApiError):
    """Token expired, revoked, or invalid."""


class GmailRateLimitError(GmailApiError):
    """Rate limited (HTTP 429) or quota exceeded."""


class GmailNotFoundError(GmailApiError):
    """Resource not found (HTTP 404)."""


class GmailApiClient:
    """Lightweight Gmail API client using raw HTTP requests.

    Handles auth, token refresh, rate limiting, and exponential backoff.
    Uses requests instead of google-api-python-client to keep deps minimal.
    """

    BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    MAX_RETRIES = 5
    RETRY_BACKOFF_BASE = 5  # seconds
    RETRY_BACKOFF_MAX = 300  # 5 minutes

    # Quota costs per operation type
    QUOTA_COST = {
        "messages.list": 5,
        "messages.get": 5,
        "messages.send": 25,
        "messages.modify": 5,
        "messages.trash": 5,
        "history.list": 5,
        "threads.list": 5,
        "profile.get": 1,
        "attachments.get": 5,
        "drafts.create": 10,
        "drafts.send": 25,
        "watch": 5,
    }

    def __init__(self, access_token: str, refresh_token: str | None = None):
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
        self._client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")
        self._quota_used: int = 0

    # ── Public API ──────────────────────────────────────────────────────────

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated GET request with retry + backoff."""
        return self._request("GET", path, params=params)

    def post(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated POST request with retry + backoff."""
        return self._request("POST", path, json=body)

    def delete(self, path: str) -> dict[str, Any]:
        """Make an authenticated DELETE request with retry + backoff."""
        return self._request("DELETE", path)

    # ── Token Management ────────────────────────────────────────────────────

    def refresh_access_token(self) -> bool:
        """Refresh the OAuth access token using the refresh token.

        Returns True if refresh succeeded, False otherwise.
        """
        if not self._refresh_token:
            logger.warning("No refresh token available for Gmail client")
            return False

        try:
            resp = requests.post(
                self.TOKEN_URL,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": self._refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=15,
            )
            if resp.status_code != 200:
                logger.error(f"Token refresh failed: {resp.status_code} {resp.text}")
                return False

            data = resp.json()
            self._access_token = data.get("access_token", self._access_token)
            logger.info("Gmail access token refreshed successfully")
            return True
        except requests.RequestException as e:
            logger.error(f"Token refresh request failed: {e}")
            return False

    @property
    def access_token(self) -> str:
        return self._access_token

    # ── Internal Helpers ────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an API request with retry logic and exponential backoff."""
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                headers = {"Authorization": f"Bearer {self._access_token}"}
                if json:
                    headers["Content-Type"] = "application/json"

                resp = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    timeout=30,
                )

                # Track quota cost
                cost = self.QUOTA_COST.get(path.split("?")[0], 5)
                self._quota_used += cost

                # Success
                if resp.status_code == 200:
                    return resp.json() if resp.content else {}

                # 204 No Content (DELETE, modify)
                if resp.status_code == 204:
                    return {}

                # Token expired — try refresh and retry once
                if resp.status_code == 401:
                    if attempt == 1 and self.refresh_access_token():
                        headers["Authorization"] = f"Bearer {self._access_token}"
                        continue  # retry with new token
                    raise GmailAuthError(
                        f"Token invalid or revoked: {resp.status_code} {resp.text[:200]}"
                    )

                # Rate limited
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", self._get_backoff(attempt)))
                    logger.warning(f"Rate limited, retrying in {retry_after}s (attempt {attempt})")
                    time.sleep(retry_after)
                    continue

                # Not found
                if resp.status_code == 404:
                    raise GmailNotFoundError(f"Resource not found: {path}")

                # Daily quota exceeded
                if resp.status_code == 403 and "dailyLimitExceeded" in resp.text:
                    raise GmailRateLimitError("Daily API quota exceeded")

                # Server errors — retry with backoff
                if resp.status_code in (500, 502, 503):
                    delay = self._get_backoff(attempt)
                    logger.warning(f"Server error {resp.status_code}, retrying in {delay}s")
                    time.sleep(delay)
                    continue

                # Other errors
                resp.raise_for_status()

            except (GmailAuthError, GmailNotFoundError, GmailRateLimitError):
                raise
            except requests.RequestException as e:
                last_error = e
                delay = self._get_backoff(attempt)
                logger.warning(f"Request failed ({e}), retrying in {delay}s (attempt {attempt})")
                time.sleep(delay)

        raise GmailApiError(f"Request failed after {self.MAX_RETRIES} retries: {last_error}") from last_error

    def _get_backoff(self, attempt: int) -> int:
        """Calculate exponential backoff delay for a given attempt number."""
        delay = self.RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
        return min(delay, self.RETRY_BACKOFF_MAX)

    def get_quota_used(self) -> int:
        """Return total quota units consumed by this client instance."""
        return self._quota_used


# ── Redis-backed sync lock ────────────────────────────────────────────────────


class SyncLock:
    """Prevent concurrent sync for the same connection using Redis.

    Falls back to in-process set when Redis is unavailable.
    """

    LOCK_PREFIX = "sync:lock:"
    LOCK_TTL = 300  # 5 minutes

    _local_locks: set[str] = set()

    @classmethod
    def acquire(cls, connection_id: str) -> bool:
        """Try to acquire lock. Returns True if acquired."""
        key = f"{cls.LOCK_PREFIX}{connection_id}"
        try:
            from django.core.cache import cache

            added = cache.add(key, str(time.time()), timeout=cls.LOCK_TTL)
            if added:
                return True
            return False
        except Exception:
            # Fallback: in-process lock (not perfect, but better than nothing)
            if key in cls._local_locks:
                return False
            cls._local_locks.add(key)
            return True

    @classmethod
    def release(cls, connection_id: str) -> None:
        """Release the lock for a connection."""
        key = f"{cls.LOCK_PREFIX}{connection_id}"
        try:
            from django.core.cache import cache

            cache.delete(key)
        except Exception:
            cls._local_locks.discard(key)

    @classmethod
    def sync_with_lock(cls, connection_id: str, sync_fn):
        """Acquire lock, run sync, release. Skip if locked."""
        if not cls.acquire(connection_id):
            logger.info(f"Sync already in progress for {connection_id}, skipping")
            return
        try:
            sync_fn()
        finally:
            cls.release(connection_id)