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