"""GmailAdapter — Gmail API email sync implementation of SyncAdapter."""
from __future__ import annotations

import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from apps.sync.adapters.base import (
    ConnectionStatus,
    DeltaResult,
    EmailMessage,
    EmailSendResult,
    OutgoingEmail,
    SyncAdapter,
    TokenRefreshResult,
)
from apps.sync.adapters.gmail.client import GmailApiClient, GmailAuthError, GmailNotFoundError
from apps.sync.adapters.gmail.mime_builder import build_rfc2822_message
from apps.sync.adapters.gmail.mime_parser import parse_gmail_message

logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 100


class GmailAdapter(SyncAdapter):
    """Gmail API email sync adapter.

    Provider: 'gmail'
    Scope: 'https://www.googleapis.com/auth/gmail.modify'
    Sync method: History API (historyId-based delta)
    Send method: messages.send with RFC 2822 MIME
    """

    PROVIDER = "gmail"
    REQUIRED_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

    def __init__(self, access_token: str, refresh_token: str | None = None):
        self._client = GmailApiClient(access_token=access_token, refresh_token=refresh_token)

    # ── Cursor Management ─────────────────────────────────────────────────

    def get_initial_cursor(self) -> dict:
        """Fetch the latest historyId as the starting cursor.

        Returns: {'historyId': int, 'watch_expiration': None}
        """
        profile = self._client.get("profile")
        return {
            "historyId": int(profile.get("historyId", 0)),
            "watch_expiration": None,
        }

    # ── Delta Sync ────────────────────────────────────────────────────────

    def get_email_delta(self, cursor: dict | None) -> DeltaResult[EmailMessage]:
        """Fetch email changes since the given cursor.

        Uses the History API for delta, falling back to time-range query
        when historyId is too old.
        """
        if cursor is None or "historyId" not in cursor:
            return self._full_sync()

        try:
            return self._delta_sync(cursor["historyId"])
        except GmailNotFoundError:
            return DeltaResult(
                items=[],
                deleted_ids=[],
                new_cursor={},
                has_more=False,
                full_resync_required=True,
            )

    def _delta_sync(self, start_history_id: int) -> DeltaResult[EmailMessage]:
        """Delta sync via Gmail History API."""
        all_items: list[EmailMessage] = []
        all_deleted: list[str] = []
        latest_history_id = start_history_id
        page_token: str | None = None

        while True:
            params: dict[str, Any] = {
                "startHistoryId": start_history_id,
                "historyTypes": ["messageAdded", "messageDeleted", "labelAdded", "labelRemoved"],
                "maxResults": MAX_BATCH_SIZE,
            }
            if page_token:
                params["pageToken"] = page_token

            response = self._client.get("history", params=params)

            # Track the latest history ID
            if "historyId" in response:
                latest_history_id = max(latest_history_id, int(response["historyId"]))

            # Process history records
            for record in response.get("history", []):
                # Messages added
                for msg_added in record.get("messagesAdded", []):
                    msg = msg_added.get("message", {})
                    email_msg = self._fetch_and_convert(msg.get("id", ""))
                    if email_msg:
                        all_items.append(email_msg)

                # Messages deleted
                for msg_deleted in record.get("messagesDeleted", []):
                    msg = msg_deleted.get("message", {})
                    if msg.get("id"):
                        all_deleted.append(msg["id"])

                # Labels added
                for label_added in record.get("labelsAdded", []):
                    msg = label_added.get("message", {})
                    email_msg = self._fetch_label_update(
                        msg.get("id", ""),
                        added_labels=label_added.get("labelIds", []),
                    )
                    if email_msg:
                        all_items.append(email_msg)

                # Labels removed
                for label_removed in record.get("labelsRemoved", []):
                    msg = label_removed.get("message", {})
                    email_msg = self._fetch_label_update(
                        msg.get("id", ""),
                        removed_labels=label_removed.get("labelIds", []),
                    )
                    if email_msg:
                        all_items.append(email_msg)

            # Pagination
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return DeltaResult(
            items=all_items,
            deleted_ids=all_deleted,
            new_cursor={"historyId": latest_history_id},
            has_more=False,
            full_resync_required=False,
        )

    # ── Full Sync ─────────────────────────────────────────────────────────

    def _full_sync(self, days_back: int = 30) -> DeltaResult[EmailMessage]:
        """Full sync — time-range based query.

        Fetches messages from the last N days (default 30), then returns
        a cursor for future delta syncs.
        """
        after_ts = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y/%m/%d")
        return self._full_sync_time_range(f"after:{after_ts}")

    def _full_sync_time_range(self, query: str) -> DeltaResult[EmailMessage]:
        """Fetch all messages matching a Gmail search query."""
        messages: list[EmailMessage] = []
        page_token: str | None = None

        while True:
            params: dict[str, Any] = {
                "q": query,
                "maxResults": MAX_BATCH_SIZE,
            }
            if page_token:
                params["pageToken"] = page_token

            response = self._client.get("messages", params=params)

            for msg_ref in response.get("messages", []):
                msg = self._fetch_and_convert(msg_ref.get("id", ""))
                if msg:
                    messages.append(msg)

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        # Get latest historyId for future delta syncs
        profile = self._client.get("profile")

        return DeltaResult(
            items=messages,
            deleted_ids=[],
            new_cursor={"historyId": int(profile.get("historyId", 0))},
            has_more=True,  # More old emails may exist for backfill
            full_resync_required=False,
        )

    def _backfill_time_range(self, query: str) -> DeltaResult[EmailMessage]:
        """Backfill older emails within a specific time range.

        Used by the background backfill Celery task.
        """
        return self._full_sync_time_range(query)

    # ── Send Email ────────────────────────────────────────────────────────

    def send_email(self, message: OutgoingEmail) -> EmailSendResult:
        """Send an email via Gmail API.

        Composes a full RFC 2822 MIME message, base64url-encodes it,
        and sends via messages.send.
        """
        mime_message = build_rfc2822_message(message)
        encoded = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("ascii")

        sent = self._client.post("messages/send", body={"raw": encoded})

        return EmailSendResult(
            provider_id=sent.get("id", ""),
            thread_id=sent.get("threadId"),
            sent_at=datetime.now(timezone.utc).isoformat(),
        )

    # ── Modify Labels ─────────────────────────────────────────────────────

    def mark_read(self, provider_message_id: str, is_read: bool) -> None:
        """Mark a message as read or unread."""
        if is_read:
            self._client.post(
                f"messages/{provider_message_id}/modify",
                body={"removeLabelIds": ["UNREAD"]},
            )
        else:
            self._client.post(
                f"messages/{provider_message_id}/modify",
                body={"addLabelIds": ["UNREAD"]},
            )

    def move_to_trash(self, provider_message_id: str) -> None:
        """Move a message to trash."""
        self._client.post(f"messages/{provider_message_id}/trash")

    # ── Connection Validation ─────────────────────────────────────────────

    def validate_connection(self) -> ConnectionStatus:
        """Test that the OAuth token works and has the right scopes."""
        try:
            profile = self._client.get("profile")
            return ConnectionStatus(
                is_valid=True,
                account_email=profile.get("emailAddress"),
                scopes=["gmail.modify"],
            )
        except GmailAuthError:
            return ConnectionStatus(is_valid=False, error="token_expired")
        except Exception as e:
            return ConnectionStatus(is_valid=False, error=str(e))

    def refresh_token(self) -> TokenRefreshResult:
        """Refresh an expired Gmail OAuth token."""
        success = self._client.refresh_access_token()
        if success:
            return TokenRefreshResult(
                success=True,
                access_token=self._client.access_token,
            )
        return TokenRefreshResult(success=False, error="token_refresh_failed")

    # ── Internal Helpers ──────────────────────────────────────────────────

    def _fetch_and_convert(self, message_id: str) -> EmailMessage | None:
        """Fetch a single message and convert to CRM format."""
        if not message_id:
            return None
        try:
            raw = self._client.get(f"messages/{message_id}", params={"format": "full"})
            return parse_gmail_message(raw)
        except GmailNotFoundError:
            logger.warning("Message %s not found (may have been deleted)", message_id)
            return None
        except Exception as e:
            logger.error("Failed to fetch message %s: %s", message_id, e)
            return None

    def _fetch_label_update(
        self,
        message_id: str,
        added_labels: list[str] | None = None,
        removed_labels: list[str] | None = None,
    ) -> EmailMessage | None:
        """Fetch a message for label change tracking.

        Only returns the message if it has new content (label changes alone
        don't require full re-fetch — CRM can update labels independently).
        """
        return self._fetch_and_convert(message_id)