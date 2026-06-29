"""Serializers + Viewsets for tasks app."""

from __future__ import annotations

from django.utils import timezone
from django_filters.rest_framework import FilterSet
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import TaskItem


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskItem
        exclude = ()
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at", "completed_at")


class TaskFilter(FilterSet):
    class Meta:
        model = TaskItem
        fields = {
            "status": ["exact"],
            "priority": ["exact", "gte", "lte"],
            "owner_id": ["exact"],
            "assignee_id": ["exact"],
            "entity_type": ["exact"],
            "entity_id": ["exact"],
            "due_at": ["exact", "gte", "lte"],
        }


class TaskViewSet(viewsets.ModelViewSet):
    queryset = TaskItem.objects.all()
    serializer_class = TaskSerializer
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "due_at", "priority", "status"]

    def get_queryset(self):
        return TaskItem.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, owner_id=self.request.user.id)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None) -> Response:
        task = self.get_object()
        task.status = TaskItem.TaskStatus.DONE
        task.completed_at = timezone.now()
        task.save()
        return Response(self.get_serializer(task).data)
