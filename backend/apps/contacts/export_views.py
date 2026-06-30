"""Streaming CSV export views for contacts and accounts."""

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

from .models import Account, Contact

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


class ContactExportView(APIView):
    """Streaming CSV export of contacts, respecting tenant scope and search filters.

    GET /api/contacts/export/csv/?search=&first_name__icontains=&...
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        queryset = Contact.objects.filter(
            tenant_id=tenant_id, deleted_at__isnull=True
        ).select_related("account")

        # Apply the same filters/search as the list endpoint
        filter_backend = DjangoFilterBackend()
        queryset = filter_backend.filter_queryset(request, queryset, self)

        search_backend = filters.SearchFilter()
        queryset = search_backend.filter_queryset(request, queryset, self)

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
            writer = csv.writer(io.StringIO())
            yield writer.writerow(headers)
            for contact in queryset.iterator(chunk_size=500):
                yield writer.writerow([
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

        response = StreamingHttpResponse(
            streaming_content=stream(),
            content_type="text/csv",
        )
        filename = f"contacts-{date.today().isoformat()}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    # Make DjangoFilterBackend work (it needs these attributes)
    filterset_fields = {
        "first_name": ["exact", "icontains"],
        "last_name": ["exact", "icontains"],
        "email": ["exact", "icontains"],
        "job_title": ["exact", "icontains"],
        "department": ["exact", "icontains"],
        "city": ["exact", "icontains"],
        "state": ["exact", "icontains"],
        "country": ["exact"],
        "owner_id": ["exact"],
        "account": ["exact"],
        "source": ["exact"],
    }
    search_fields = ["first_name", "last_name", "email", "phone", "job_title"]
    ordering_fields = ["created_at", "last_name", "first_name", "email"]


class AccountExportView(APIView):
    """Streaming CSV export of accounts.

    GET /api/contacts/export/accounts/csv/?search=&name__icontains=&...
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        queryset = Account.objects.filter(tenant_id=tenant_id, deleted_at__isnull=True)

        filter_backend = DjangoFilterBackend()
        queryset = filter_backend.filter_queryset(request, queryset, self)

        search_backend = filters.SearchFilter()
        queryset = search_backend.filter_queryset(request, queryset, self)

        owner_ids = set(queryset.values_list("owner_id", flat=True))
        owner_map = _resolve_owner_names(owner_ids)

        headers = [
            "name", "domain", "industry", "description", "website", "phone",
            "address_line1", "address_line2", "city", "state", "postal_code", "country",
            "employees_count", "annual_revenue", "tags", "owner_name",
            "created_at", "updated_at",
        ]

        def stream():
            writer = csv.writer(io.StringIO())
            yield writer.writerow(headers)
            for account in queryset.iterator(chunk_size=500):
                yield writer.writerow([
                    account.name,
                    account.domain,
                    account.industry,
                    account.description,
                    account.website,
                    account.phone,
                    account.address_line1,
                    account.address_line2,
                    account.city,
                    account.state,
                    account.postal_code,
                    account.country,
                    account.employees_count or "",
                    str(account.annual_revenue) if account.annual_revenue else "",
                    ",".join(account.tags) if account.tags else "",
                    owner_map.get(str(account.owner_id), "") if account.owner_id else "",
                    account.created_at.isoformat() if account.created_at else "",
                    account.updated_at.isoformat() if account.updated_at else "",
                ])

        response = StreamingHttpResponse(
            streaming_content=stream(),
            content_type="text/csv",
        )
        filename = f"accounts-{date.today().isoformat()}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    filterset_fields = {
        "name": ["exact", "icontains"],
        "domain": ["exact", "icontains"],
        "industry": ["exact", "icontains"],
        "city": ["exact", "icontains"],
        "country": ["exact"],
        "owner_id": ["exact"],
    }
    search_fields = ["name", "domain", "industry", "city", "description"]
    ordering_fields = ["name", "created_at", "industry"]