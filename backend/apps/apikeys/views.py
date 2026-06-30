"""Views for the API Keys management endpoints."""

from __future__ import annotations

from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import RolePermission, TenantAwarePermission

from .models import APIKey
from .serializers import APIKeySerializer


class APIKeyListCreateView(generics.ListCreateAPIView):
    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated, TenantAwarePermission, RolePermission]

    def get_queryset(self):
        return APIKey.objects.filter(tenant_id=self.request.user.tenant_id)

    def get_required_permission(self):
        if self.request.method == "POST":
            return "settings.manage"
        return "settings.view"

    def perform_create(self, serializer):
        serializer.save()


class APIKeyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated, TenantAwarePermission, RolePermission]
    lookup_field = "pk"

    def get_required_permission(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return "settings.manage"
        return "settings.view"

    def get_queryset(self):
        return APIKey.objects.filter(tenant_id=self.request.user.tenant_id)


class APIKeyRevokeView(generics.UpdateAPIView):
    """Revoke an API key without deleting it."""

    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated, TenantAwarePermission, RolePermission]
    lookup_field = "pk"

    def get_required_permission(self):
        return "settings.manage"

    def get_queryset(self):
        return APIKey.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_update(self, serializer):
        serializer.save(is_active=False, revoked_at=timezone.now())
