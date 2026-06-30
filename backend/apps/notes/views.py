"""Serializers + Viewsets for notes app."""

from __future__ import annotations

from django_filters.rest_framework import FilterSet
from rest_framework import serializers, viewsets

from apps.core.permissions import RolePermission, TenantAwarePermission

from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        exclude = ()
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


class NoteFilter(FilterSet):
    class Meta:
        model = Note
        fields = {
            "entity_type": ["exact"],
            "entity_id": ["exact"],
            "owner_id": ["exact"],
            "is_pinned": ["exact"],
        }


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filterset_class = NoteFilter
    search_fields = ["title", "content"]
    permission_classes = [TenantAwarePermission, RolePermission]

    def get_required_permission(self) -> str | None:
        return {
            "list": None,  # notes are embedded in other views
            "retrieve": None,
            "create": "notes.create",
            "update": "notes.create",
            "partial_update": "notes.create",
            "destroy": "notes.delete",
        }.get(self.action)

    def get_queryset(self):
        return Note.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, owner_id=self.request.user.id)
