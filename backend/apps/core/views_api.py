"""API views for core models — CustomFieldDef CRUD."""

from __future__ import annotations

from rest_framework import viewsets

from apps.core.permissions import TenantAwarePermission, RolePermission

from .models import CustomFieldDef
from .serializers import CustomFieldDefSerializer


class CustomFieldDefViewSet(viewsets.ModelViewSet):
    queryset = CustomFieldDef.objects.all()
    serializer_class = CustomFieldDefSerializer
    permission_classes = [TenantAwarePermission, RolePermission]

    def get_required_permission(self) -> str | None:
        return {
            "list": "settings.view",
            "retrieve": "settings.view",
            "create": "settings.edit",
            "update": "settings.edit",
            "partial_update": "settings.edit",
            "destroy": "settings.delete",
        }.get(self.action)

    def get_queryset(self):
        return CustomFieldDef.objects.filter(
            tenant_id=self.request.user.tenant_id,
            deleted_at__isnull=True,
        )

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)
