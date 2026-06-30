"""Streaming CSV export views for deals."""

from __future__ import annotations

import csv
import io
from datetime import date

from django.contrib.auth import get_user_model
from django.http import StreamingHttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.permissions import RolePermission, TenantAwarePermission

from .models import Deal

User = get_user_model()


def _resolve_owner_names(owner_ids: set[str | None]) -> dict[str, str]:
    """Batch resolve owner UUIDs to display names."""
    valid_ids = [oid for oid in owner_ids if oid]
    if not valid_ids:
        return {}
    users = User.objects.filter(id__in=valid_ids).values("id", "first_name", "last_name")
    return {
        str(u["id"]): f"{u['first_name']} {u['last_name']}".strip() or "Unknown"
        for u in users
    }


class DealExportView(APIView):
    """Streaming CSV export of deals, respecting tenant scope and filters.

    GET /api/deals/export/csv/?search=&status=open&pipeline=&...
    """

    permission_classes = [TenantAwarePermission, RolePermission]
    required_permission = "deals.export"

    def get(self, request):
        tenant_id = request.user.tenant_id
        queryset = Deal.objects.filter(
            tenant_id=tenant_id, deleted_at__isnull=True
        ).select_related("stage", "pipeline", "contact", "account")

        filter_backend = DjangoFilterBackend()
        queryset = filter_backend.filter_queryset(request, queryset, self)

        search_backend = filters.SearchFilter()
        queryset = search_backend.filter_queryset(request, queryset, self)

        owner_ids = set(queryset.values_list("owner_id", flat=True))
        owner_map = _resolve_owner_names(owner_ids)

        headers = [
            "name", "value", "currency", "status", "stage_name",
            "pipeline_name", "probability", "expected_close_date",
            "owner_name", "contact_name", "account_name",
            "description", "tags", "created_at", "updated_at",
        ]

        def stream():
            writer = csv.writer(io.StringIO())
            yield writer.writerow(headers)
            for deal in queryset.iterator(chunk_size=500):
                yield writer.writerow([
                    deal.name,
                    str(deal.value),
                    deal.currency,
                    deal.status,
                    deal.stage.name if deal.stage else "",
                    deal.pipeline.name if deal.pipeline else "",
                    str(deal.win_probability),
                    deal.expected_close_date.isoformat() if deal.expected_close_date else "",
                    owner_map.get(str(deal.owner_id), "") if deal.owner_id else "",
                    str(deal.contact) if deal.contact else "",
                    str(deal.account) if deal.account else "",
                    deal.description,
                    ",".join(deal.tags) if deal.tags else "",
                    deal.created_at.isoformat() if deal.created_at else "",
                    deal.updated_at.isoformat() if deal.updated_at else "",
                ])

        response = StreamingHttpResponse(
            streaming_content=stream(),
            content_type="text/csv",
        )
        filename = f"deals-{date.today().isoformat()}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    filterset_fields = {
        "pipeline": ["exact"],
        "stage": ["exact"],
        "status": ["exact"],
        "owner_id": ["exact"],
        "contact": ["exact"],
        "account": ["exact"],
        "value": ["exact", "gte", "lte"],
        "expected_close_date": ["exact", "gte", "lte"],
    }
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "value", "expected_close_date", "status"]