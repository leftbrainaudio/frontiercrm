"""Viewset for the AuditLog model — paginated, filterable, read-only."""

from __future__ import annotations

from django_filters.rest_framework import FilterSet, filters
from rest_framework import viewsets

from apps.core.audit_serializers import AuditLogSerializer
from apps.core.models import AuditLog
from apps.core.permissions import RolePermission, TenantAwarePermission


class AuditLogFilter(FilterSet):
    entity_type = filters.CharFilter(lookup_expr="iexact")
    actor_id = filters.UUIDFilter(field_name="actor_id")
    date_from = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    date_to = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    action = filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = AuditLog
        fields = [
            "entity_type",
            "actor_id",
            "action",
            "date_from",
            "date_to",
        ]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("actor").all()
    serializer_class = AuditLogSerializer
    filterset_class = AuditLogFilter
    ordering_fields = ["created_at", "entity_type", "action"]
    ordering = ["-created_at"]
    permission_classes = [TenantAwarePermission, RolePermission]
    required_permission = "audit.log"

    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)