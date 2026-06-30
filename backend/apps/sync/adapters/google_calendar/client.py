"""Google Calendar API client wrapper with auth and error handling.

Pattern follows GmailApiClient in apps/sync/adapters/gmail/client.py.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class CalendarApiError(Exception):
    """Base error for Calendar API operations."""


class CalendarAuthError(CalendarApiError):
    """Token expired, revoked, or invalid."""


class CalendarRateLimitError(CalendarApiError):
    """Rate limited (HTTP 429) or quota exceeded."""


class CalendarNotFoundError(CalendarApiError):
    """Resource not found (HTTP 404)."""


class GoogleCalendarApiClient:
    """Lightweight Google Calendar v3 API client using raw HTTP requests.

    Handles auth, token refresh, rate limiting, and exponential backoff.
    Uses requests instead of google-api-python-client to keep deps minimal.
    """

    BASE_URL = "https://www.googleapis.com/calendar/v3"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    MAX_RETRIES = 5
    RETRY_BACKOFF_BASE = 5  # seconds
    RETRY_BACKOFF_MAX = 300  # 5 minutes

    def __init__(self, access_token: str, refresh_token: str | None = None):
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
        self._client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")

    # ── Public API ──────────────────────────────────────────────────────────

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated GET request with retry + backoff."""
        return self._request("GET", path, params=params)

    def post(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated POST request with retry + backoff."""
        return self._request("POST", path, json=body)

    def patch(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an authenticated PATCH request with retry + backoff."""
        return self._request("PATCH", path, json=body)

    def delete(self, path: str) -> dict[str, Any]:
        """Make an authenticated DELETE request with retry + backoff."""
        return self._request("DELETE", path)

    @staticmethod
    def build_event_body(
        summary: str,
        start: datetime,
        end: datetime,
        *,
        description: str | None = None,
        location: str | None = None,
        timezone: str = "UTC",
        all_day: bool = False,
        attendees: list[dict] | None = None,
        recurrence: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build Google Calendar API event body from normalized parameters."""
        body: dict[str, Any] = {
            "summary": summary[:500],
        }

        if all_day:
            body["start"] = {"date": start.date().isoformat(), "timeZone": timezone}
            body["end"] = {"date": end.date().isoformat(), "timeZone": timezone}
        else:
            body["start"] = {"dateTime": start.isoformat(), "timeZone": timezone}
            body["end"] = {"dateTime": end.isoformat(), "timeZone": timezone}

        if description:
            body["description"] = description[:5000]
        if location:
            body["location"] = location
        if attendees:
            body["attendees"] = [
                {
                    "email": a.get("email"),
                    "displayName": a.get("displayName"),
                }
                for a in attendees
                if a.get("email")
            ]
        if recurrence:
            body["recurrence"] = recurrence[:10]  # Cap at 10 RRULEs
            body["singleEvents"] = False

        return body

    # ── Token Management ────────────────────────────────────────────────────

    def refresh_access_token(self) -> bool:
        """Refresh the OAuth access token using the refresh token.

        Returns True if refresh succeeded, False otherwise.
        """
        if not self._refresh_token:
            logger.warning("No refresh token available for Calendar client")
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
                logger.error(f"Calendar token refresh failed: {resp.status_code} {resp.text}")
                return False

            data = resp.json()
            self._access_token = data.get("access_token", self._access_token)
            logger.info("Calendar access token refreshed successfully")
            return True
        except requests.RequestException as e:
            logger.error(f"Calendar token refresh request failed: {e}")
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

                # Success
                if resp.status_code == 200:
                    return resp.json() if resp.content else {}

                # 204 No Content
                if resp.status_code == 204:
                    return {}

                # Token expired — try refresh and retry once
                if resp.status_code == 401:
                    if attempt == 1 and self.refresh_access_token():
                        headers["Authorization"] = f"Bearer {self._access_token}"
                        continue  # retry with new token
                    raise CalendarAuthError(
                        f"Token invalid or revoked: {resp.status_code} {resp.text[:200]}"
                    )

                # Rate limited
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", self._get_backoff(attempt)))
                    logger.warning(f"Calendar rate limited, retrying in {retry_after}s (attempt {attempt})")
                    time.sleep(retry_after)
                    continue

                # Not found
                if resp.status_code == 404:
                    raise CalendarNotFoundError(f"Resource not found: {path}")

                # syncToken expired (410 Gone)
                if resp.status_code == 410:
                    raise CalendarNotFoundError(f"syncToken expired: {resp.text[:200]}")

                # Daily quota exceeded
                if resp.status_code == 403 and "dailyLimitExceeded" in resp.text:
                    raise CalendarRateLimitError("Daily API quota exceeded")

                # Server errors — retry with backoff
                if resp.status_code in (500, 502, 503):
                    delay = self._get_backoff(attempt)
                    logger.warning(f"Calendar server error {resp.status_code}, retrying in {delay}s")
                    time.sleep(delay)
                    continue

                # Other errors
                resp.raise_for_status()

            except (CalendarAuthError, CalendarNotFoundError, CalendarRateLimitError):
                raise
            except requests.RequestException as e:
                last_error = e
                delay = self._get_backoff(attempt)
                logger.warning(f"Calendar request failed ({e}), retrying in {delay}s (attempt {attempt})")
                time.sleep(delay)

        raise CalendarApiError(f"Request failed after {self.MAX_RETRIES} retries: {last_error}") from last_error

    def _get_backoff(self, attempt: int) -> int:
        """Calculate exponential backoff delay for a given attempt number."""
        delay = self.RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
        return min(delay, self.RETRY_BACKOFF_MAX)