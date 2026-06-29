"""Serializers + Viewsets for email messages."""

from __future__ import annotations

from django_filters.rest_framework import FilterSet
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import EmailMessage


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailMessage
        exclude = ()
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


class EmailFilter(FilterSet):
    class Meta:
        model = EmailMessage
        fields = {
            "direction": ["exact"],
            "from_email": ["exact", "icontains"],
            "thread_id": ["exact"],
            "entity_type": ["exact"],
            "entity_id": ["exact"],
            "is_read": ["exact"],
            "is_starred": ["exact"],
        }


class EmailViewSet(viewsets.ModelViewSet):
    queryset = EmailMessage.objects.all()
    serializer_class = EmailSerializer
    filterset_class = EmailFilter
    search_fields = ["subject", "body_text", "from_email"]
    ordering_fields = ["-sent_at"]

    def get_queryset(self):
        return EmailMessage.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

    @action(detail=True, methods=["post"])
    def toggle_star(self, request, pk=None) -> Response:
        email = self.get_object()
        email.is_starred = not email.is_starred
        email.save()
        return Response(self.get_serializer(email).data)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None) -> Response:
        email = self.get_object()
        email.is_read = True
        email.save()
        return Response(self.get_serializer(email).data)
