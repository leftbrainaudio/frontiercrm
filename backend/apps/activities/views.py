"""Serializers + Viewsets for activities, notes, tasks, and email."""

from __future__ import annotations

from django_filters.rest_framework import FilterSet
from rest_framework import serializers, viewsets

from apps.activities.models import Activity


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        exclude = ()
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


class ActivityFilter(FilterSet):
    class Meta:
        model = Activity
        fields = {
            "activity_type": ["exact"],
            "entity_type": ["exact"],
            "entity_id": ["exact"],
            "actor_id": ["exact"],
        }


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    filterset_class = ActivityFilter
    ordering_fields = ["-created_at"]

    def get_queryset(self):
        return Activity.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, actor_id=self.request.user.id)
