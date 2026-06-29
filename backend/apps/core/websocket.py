"""WebSocket URL patterns for real-time updates."""

from __future__ import annotations

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # Real-time notifications
    re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
    # Activity feed
    re_path(r"ws/activities/(?P<entity_type>\w+)/(?P<entity_id>[0-9a-f-]+)/$", consumers.ActivityConsumer.as_asgi()),
]
