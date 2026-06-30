"""URL routing for the audit log API endpoint."""

from __future__ import annotations

from django.urls import path

from apps.core.audit_views import AuditLogViewSet

# Register only the list endpoint — this is a read-only view
urlpatterns = [
    path(
        "audit/",
        AuditLogViewSet.as_view({"get": "list"}),
        name="audit-log-list",
    ),
]