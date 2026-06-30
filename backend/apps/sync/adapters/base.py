"""Base classes and data models for the sync adapter pattern."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

T = TypeVar("T")


# ── Unified Data Models ──────────────────────────────────────────────────────


@dataclass
class AttachmentInfo:
    """Information about an email attachment."""

    attachment_id: str
    filename: str
    mime_type: str
    size: int
    storage_key: str = ""


@dataclass
class EmailMessage:
    """Normalized email message — used by all adapters."""

    provider_id: str
    thread_id: str | None
    message_id: str  # RFC 2822 Message-ID
    subject: str
    from_address: str
    from_name: str | None
    to_addresses: list[str]
    cc_addresses: list[str] = field(default_factory=list)
    bcc_addresses: list[str] = field(default_factory=list)
    body_text: str | None = None
    body_html: str | None = None
    snippet: str | None = None
    sent_at: datetime | None = None
    received_at: datetime | None = None
    is_read: bool = False
    is_starred: bool = False
    labels: list[str] = field(default_factory=list)
    attachments: list[AttachmentInfo] = field(default_factory=list)
    raw_headers: dict[str, str] = field(default_factory=dict)
    size_estimate: int = 0


@dataclass
class OutgoingEmail:
    """Email to be sent via a provider adapter."""

    to_addresses: list[str]
    cc_addresses: list[str] = field(default_factory=list)
    bcc_addresses: list[str] = field(default_factory=list)
    subject: str = ""
    body_html: str = ""
    body_text: str = ""
    attachments: list[AttachmentInfo] = field(default_factory=list)


@dataclass
class EmailSendResult:
    """Result of a send_email adapter call."""

    provider_id: str
    thread_id: str | None = None
    sent_at: str = ""


@dataclass
class ConnectionStatus:
    """Result of a validate_connection adapter call."""

    is_valid: bool
    account_email: str | None = None
    scopes: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class TokenRefreshResult:
    """Result of a refresh_token adapter call."""

    success: bool
    access_token: str = ""
    expires_in: int = 0
    error: str | None = None


@dataclass
class DeltaResult(Generic[T]):
    """Result of a delta sync operation."""

    items: list[T] = field(default_factory=list)
    deleted_ids: list[str] = field(default_factory=list)
    new_cursor: dict[str, Any] = field(default_factory=dict)
    has_more: bool = False
    full_resync_required: bool = False


# ── Abstract Base Adapter ────────────────────────────────────────────────────


class SyncAdapter(ABC):
    """Abstract interface for all sync providers."""

    PROVIDER = ""
    REQUIRED_SCOPES: list[str] = []

    # ========== Email ==========

    @abstractmethod
    def get_email_delta(self, cursor: dict | None) -> DeltaResult[EmailMessage]:
        """Fetch email changes since the given cursor."""
        ...

    @abstractmethod
    def send_email(self, message: OutgoingEmail) -> EmailSendResult:
        """Send an email via the provider."""
        ...

    @abstractmethod
    def mark_read(self, provider_message_id: str, is_read: bool) -> None:
        """Mark a message as read or unread."""
        ...

    @abstractmethod
    def get_initial_cursor(self) -> dict:
        """Fetch the starting cursor for delta sync."""
        ...

    @abstractmethod
    def validate_connection(self) -> ConnectionStatus:
        """Test that the OAuth token works and has the right scopes."""
        ...

    @abstractmethod
    def refresh_token(self) -> TokenRefreshResult:
        """Refresh an expired OAuth token."""
        ...


# ── Calendar Data Models ──────────────────────────────────────────────────


@dataclass
class CalendarEvent:
    """Normalized calendar event from any provider."""

    provider_id: str  # Google Calendar event ID
    calendar_id: str  # Usually "primary"
    i_cal_uid: str | None = None
    summary: str = ""
    description: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    all_day: bool = False
    timezone: str = "UTC"
    location: str | None = None
    hangout_link: str | None = None
    status: str = "confirmed"  # confirmed, tentative, cancelled
    recurrence: list[str] = field(default_factory=list)
    recurring_event_id: str | None = None
    original_start_time: datetime | None = None
    attendees: list[dict] = field(default_factory=list)
    creator: dict | None = None
    organizer: dict | None = None
    created: datetime | None = None
    updated: datetime | None = None
    html_link: str | None = None


@dataclass
class CalendarDeltaResult:
    """Result of a calendar delta sync operation."""

    items: list[CalendarEvent] = field(default_factory=list)
    deleted_ids: list[str] = field(default_factory=list)
    new_cursor: dict[str, Any] = field(default_factory=dict)
    has_more: bool = False
    full_resync_required: bool = False


class CalendarSyncAdapter(ABC):
    """Abstract interface for calendar sync providers."""

    PROVIDER = ""
    REQUIRED_SCOPES: list[str] = []

    @abstractmethod
    def get_calendar_delta(self, cursor: dict | None) -> CalendarDeltaResult:
        """Fetch calendar event changes since the given cursor.

        When cursor is None or expired, triggers a full sync within
        the default time window (last 90 days to next 30 days).
        """
        ...

    @abstractmethod
    def get_initial_cursor(self) -> dict:
        """Fetch the starting cursor for delta sync (syncToken or time)."""
        ...

    @abstractmethod
    def validate_connection(self) -> ConnectionStatus:
        """Test that the OAuth token works and has the right scopes."""
        ...

    @abstractmethod
    def refresh_token(self) -> TokenRefreshResult:
        """Refresh an expired OAuth token."""
        ...

    # ── Write Methods (Event Creation) ──────────────────────────────────────

    @abstractmethod
    def create_event(
        self,
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
        hangout_link: str | None = None,
        source_activity_id: str | None = None,
        source_entity_type: str | None = None,
        source_entity_id: str | None = None,
    ) -> CalendarEvent:
        """Create a new calendar event on the provider.

        Returns the full CalendarEvent as created by the provider
        (including the provider-assigned event ID).
        """
        ...

    @abstractmethod
    def update_event(
        self,
        event_id: str,
        *,
        summary: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        description: str | None = None,
        location: str | None = None,
        timezone: str | None = None,
        all_day: bool | None = None,
        attendees: list[dict] | None = None,
        recurrence: list[str] | None = None,
    ) -> CalendarEvent | None:
        """Update an existing calendar event on the provider.

        Returns the updated CalendarEvent, or None if the event
        was deleted on the provider side.
        """
        ...

    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event on the provider.

        Returns True if deletion succeeded, False if the event
        was already deleted or not found.
        """
        ...

    # ── Watch Channel Methods (Push Notifications) ──────────────────────

    @abstractmethod
    def setup_watch(
        self,
        channel_id: str,
        webhook_url: str,
        ttl_seconds: int = 604800,
    ) -> dict[str, Any]:
        """Register a watch channel for push notifications.

        Returns the provider's response including resourceId.
        """
        ...

    @abstractmethod
    def stop_watch(self, channel_id: str, resource_id: str) -> bool:
        """Stop a watch channel.

        Returns True if the channel was stopped, False if not found.
        """
        ...