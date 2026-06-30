"""Slack webhook views — CRUD, test, and deactivate endpoints."""

from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.slack.models import SlackWebhook
from apps.slack.serializers import SlackWebhookSerializer
from apps.slack.services import send_test_message


class SlackWebhookViewSet(viewsets.ModelViewSet):
    queryset = SlackWebhook.objects.all()
    serializer_class = SlackWebhookSerializer

    def get_queryset(self):
        return SlackWebhook.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None):
        """Send a test Slack message to verify the webhook URL."""
        webhook = self.get_object()
        result = send_test_message(webhook)
        if result["status"] == "delivered":
            return Response({"status": "delivered"})
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def deactivate(self, request: Request, pk=None):
        """Deactivate a webhook (stop sending notifications)."""
        webhook = self.get_object()
        webhook.is_active = False
        webhook.save(update_fields=["is_active", "updated_at"])
        return Response({"status": "deactivated"})