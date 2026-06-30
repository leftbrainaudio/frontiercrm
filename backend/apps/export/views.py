"""Streaming CSV export views for contacts, deals, and pipeline reports.

Provides the unified /api/export/ namespace as specified in Phase 4.
Reuses existing export logic from apps.contacts.export_views and
apps.reports.views where available.
"""

from __future__ import annotations

import csv
import io
from datetime import date

from django.contrib.auth import get_user_model
from django.http import StreamingHttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.permissions import RolePermission, TenantAwarePermission
from apps.contacts.models import Account, Contact
from apps.pipelines.models import Deal

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


# ── Contacts Export ──────────────────────────────────────────────────────


class ExportContactsView(APIView):
    """Streaming CSV export of contacts, respecting tenant scope.

    GET /api/export/contacts/?format=csv
    """

    permission_classes = [TenantAwarePermission, RolePermission]
    required_permission = "contacts.export"

    def get(self, request):
        tenant_id = request.user.tenant_id
        queryset = Contact.objects.filter(
            tenant_id=tenant_id, deleted_at__isnull=True
        ).select_related("account")

        # Resolve owner names in a single batch
        owner_ids = set(queryset.values_list("owner_id", flat=True))
        owner_map = _resolve_owner_names(owner_ids)

        headers = [
            "first_name", "last_name", "email", "phone", "mobile",
            "job_title", "department", "street", "city", "state",
            "postal_code", "country", "source", "tags",
            "account_name", "owner_name", "created_at", "updated_at",
        ]

        def stream():
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(headers)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            for contact in queryset.iterator(chunk_size=500):
                writer.writerow([
                    contact.first_name,
                    contact.last_name,
                    contact.email,
                    contact.phone,
                    contact.mobile,
                    contact.job_title,
                    contact.department,
                    contact.street,
                    contact.city,
                    contact.state,
                    contact.postal_code,
                    contact.country,
                    contact.source,
                    ",".join(contact.tags) if contact.tags else "",
                    contact.account.name if contact.account else "",
                    owner_map.get(str(contact.owner_id), "") if contact.owner_id else "",
                    contact.created_at.isoformat() if contact.created_at else "",
                    contact.updated_at.isoformat() if contact.updated_at else "",
                ])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        response = StreamingHttpResponse(
            streaming_content=stream(),
            content_type="text/csv",
        )
        filename = f"contacts-{date.today().isoformat()}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


# ── Deals Export ─────────────────────────────────────────────────────────


class ExportDealsView(APIView):
    """Streaming CSV export of deals with stage, value, owner, close date.

    GET /api/export/deals/?format=csv
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        queryset = Deal.objects.filter(
            tenant_id=tenant_id,
            deleted_at__isnull=True,
        ).select_related("pipeline", "stage", "contact", "account")

        owner_ids = set(queryset.values_list("owner_id", flat=True))
        owner_map = _resolve_owner_names(owner_ids)

        headers = [
            "name", "value", "currency", "status", "pipeline_name",
            "stage_name", "probability", "win_probability", "weighted_value",
            "expected_close_date", "closed_at", "close_reason",
            "contact_name", "account_name", "owner_name",
            "description", "tags", "entered_stage_at",
            "created_at", "updated_at",
        ]

        def stream():
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(headers)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            for deal_obj in queryset.iterator(chunk_size=500):
                writer.writerow([
                    deal_obj.name,
                    str(deal_obj.value),
                    deal_obj.currency,
                    deal_obj.status,
                    deal_obj.pipeline.name if deal_obj.pipeline else "",
                    deal_obj.stage.name if deal_obj.stage else "",
                    str(deal_obj.stage.probability) if deal_obj.stage else "",
                    str(deal_obj.win_probability),
                    str(deal_obj.weighted_value),
                    deal_obj.expected_close_date.isoformat() if deal_obj.expected_close_date else "",
                    deal_obj.closed_at.isoformat() if deal_obj.closed_at else "",
                    deal_obj.close_reason,
                    deal_obj.contact.full_name if deal_obj.contact else "",
                    deal_obj.account.name if deal_obj.account else "",
                    owner_map.get(str(deal_obj.owner_id), "") if deal_obj.owner_id else "",
                    deal_obj.description,
                    ",".join(deal_obj.tags) if deal_obj.tags else "",
                    deal_obj.entered_stage_at.isoformat() if deal_obj.entered_stage_at else "",
                    deal_obj.created_at.isoformat() if deal_obj.created_at else "",
                    deal_obj.updated_at.isoformat() if deal_obj.updated_at else "",
                ])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        response = StreamingHttpResponse(
            streaming_content=stream(),
            content_type="text/csv",
        )
        filename = f"deals-{date.today().isoformat()}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


# ── Pipeline Report Export ───────────────────────────────────────────────


class ExportPipelineReportView(APIView):
    """Streaming CSV export of current pipeline report data.

    GET /api/export/reports/pipeline/?format=csv

    Exports the deals-by-stage breakdown: stage name, count, total value, probability.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from decimal import Decimal

        from django.db.models import Count, Q, Sum, Value
        from django.db.models.functions import Coalesce

        from apps.pipelines.models import Stage

        tenant_id = request.user.tenant_id
        open_filter = Q(deals__status="open", deals__deleted_at__isnull=True)

        # Aggregate deals by stage for the tenant's active pipelines
        stages = (
            Stage.objects.filter(
                pipeline__tenant_id=tenant_id,
                pipeline__is_active=True,
            )
            .annotate(
                deal_count=Count("deals", filter=open_filter),
                total_value=Coalesce(
                    Sum("deals__value", filter=open_filter),
                    Value(Decimal("0.00")),
                ),
            )
            .order_by("pipeline__name", "display_order")
            .select_related("pipeline")
        )

        headers = [
            "pipeline_name", "stage_name", "deal_count", "total_value",
            "probability", "display_order",
        ]

        def stream():
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(headers)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            for stage in stages.iterator(chunk_size=200):
                writer.writerow([
                    stage.pipeline.name if stage.pipeline else "",
                    stage.name,
                    stage.deal_count,
                    str(stage.total_value),
                    str(stage.probability),
                    stage.display_order,
                ])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        response = StreamingHttpResponse(
            streaming_content=stream(),
            content_type="text/csv",
        )
        filename = f"pipeline-report-{date.today().isoformat()}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
