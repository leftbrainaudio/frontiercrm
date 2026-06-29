"""WebSocket consumers for real-time features."""

from __future__ import annotations

from typing import Any

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Push notifications to connected clients."""

    async def connect(self) -> None:
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        self.group_name = f"user_{self.user.id}_notifications"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_message(self, event: dict[str, Any]) -> None:
        await self.send_json(event["data"])


class ActivityConsumer(AsyncJsonWebsocketConsumer):
    """Real-time activity feed for a specific entity."""

    async def connect(self) -> None:
        self.entity_type = self.scope["url_route"]["kwargs"]["entity_type"]
        self.entity_id = self.scope["url_route"]["kwargs"]["entity_id"]
        self.group_name = f"activities_{self.entity_type}_{self.entity_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def activity_event(self, event: dict[str, Any]) -> None:
        await self.send_json(event["data"])
