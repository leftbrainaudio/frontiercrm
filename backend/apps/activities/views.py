"""Serializers + Viewsets for activities, notes, tasks, and email."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from django.db import models
from django.db.models import QuerySet
from django_filters import rest_framework as filters
from django_filters.rest_framework import FilterSet
from rest_framework import serializers, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import RolePermission, TenantAwarePermission

from apps.accounts.models import User
from apps.activities.models import Activity
from apps.contacts.models import Account, Contact
from apps.email.models import EmailMessage
from apps.files.models import FileUpload
from apps.notes.models import Note
from apps.pipelines.models import Deal
from apps.tasks.models import TaskItem


# ── Entity reference resolution ────────────────────────────────────────

ENTITY_RESOLVER: dict[str, tuple[type[models.Model], str]] = {
    "deal": (Deal, "name"),
    "contact": (Contact, "full_name"),
    "account": (Account, "name"),
    "email": (EmailMessage, "subject"),
    "note": (Note, "title"),
    "task": (TaskItem, "title"),
    "file_upload": (FileUpload, "original_filename"),
}


def _resolve_entity_names(activities: list[Activity]) -> dict[str, str]:
    """Build a lookup {entity_type:entity_id -> display_name} by batch-querying
    each referenced entity model."""
    refs: dict[str, set[str]] = {}
    for a in activities:
        et = a.entity_type
        eid = str(a.entity_id)
        if et and eid:
            refs.setdefault(et, set()).add(eid)

    lookup: dict[str, str] = {}
    for entity_type, id_set in refs.items():
        entry = ENTITY_RESOLVER.get(entity_type)
        if entry is None:
            continue
        model_cls, name_attr = entry
        qs: QuerySet = model_cls.objects.filter(id__in=list(id_set))
        for obj in qs:
            val = getattr(obj, name_attr, None)
            if callable(val):
                val = val()
            key = f"{entity_type}:{obj.id}"
            lookup[key] = str(val or "") if val else ""

    return lookup


def _resolve_actor_names(actor_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Build a lookup {actor_id -> {name, avatar_url}} from the User model."""
    if not actor_ids:
        return {}
    users = User.objects.filter(id__in=actor_ids).only("id", "first_name", "last_name", "avatar_url")
    result: dict[str, dict[str, Any]] = {}
    for u in users:
        uid = str(u.id)
        name = f"{u.first_name} {u.last_name}".strip() or u.email
        result[uid] = {"name": name, "avatar_url": u.avatar_url}
    return result


# ── Activity serializer / viewset (existing CRUD) ──────────────────────


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        exclude = ()
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


class ActivityFilter(FilterSet):
    start_date = filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="created_at", lookup_expr="lte")

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
    permission_classes = [TenantAwarePermission, RolePermission]

    def get_required_permission(self) -> str | None:
        return {
            "list": "activities.view",
            "retrieve": "activities.view",
            "create": "activities.create",
            "update": None,  # activities aren't typically edited
            "partial_update": None,
            "destroy": "activities.delete",
        }.get(self.action)

    def get_queryset(self):
        return Activity.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id, actor_id=self.request.user.id)


# ── Timeline endpoint ──────────────────────────────────────────────────


class ActorSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    avatar_url = serializers.URLField(required=False, allow_blank=True)


class EntitySerializer(serializers.Serializer):
    type = serializers.CharField()
    id = serializers.UUIDField()
    name = serializers.CharField(required=False, allow_blank=True, default="")
    url = serializers.CharField(required=False, allow_blank=True, default="")


class TimelineEntrySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    activity_type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.DateTimeField()
    actor = ActorSerializer(read_only=True)
    entity = EntitySerializer(read_only=True)
    metadata = serializers.JSONField()


class TimelinePagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("page", self.page.number),
                    ("page_size", self.get_page_size(self.request)),
                    ("total_pages", self.page.paginator.num_pages),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )


class TimelineView(APIView):
    """Paginated org-wide activity timeline with resolved actor + entity metadata.

    GET /api/activities/timeline/
      ?start_date=2026-01-01
      &end_date=2026-06-30
      &activity_type=note
      &actor_id=<uuid>
      &page=1
      &page_size=25
    """

    pagination_class = TimelinePagination

    def get(self, request: Request) -> Response:
        tenant_id = request.user.tenant_id

        # Base queryset — tenant-scoped, ordered by creation date desc
        qs = Activity.objects.filter(tenant_id=tenant_id)

        # Apply filters
        filterset = ActivityFilter(request.query_params, queryset=qs)
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)
        qs = filterset.qs.order_by("-created_at")

        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)

        # Resolve actor + entity metadata for this page
        actor_ids = list({str(a.actor_id) for a in page if a.actor_id})
        actor_lookup = _resolve_actor_names(actor_ids)
        entity_lookup = _resolve_entity_names(page)

        # Build serialized results
        results: list[dict[str, Any]] = []
        for a in page:
            aid = str(a.actor_id) if a.actor_id else None
            actor_data = (
                actor_lookup.get(aid, {"name": "", "avatar_url": ""})
                if aid
                else {"name": "", "avatar_url": ""}
            )
            actor_data["id"] = a.actor_id

            ekey = f"{a.entity_type}:{a.entity_id}"
            entity_name = entity_lookup.get(ekey, "")
            # Map entity types to actual frontend routes
            route_map = {
                "deal": "/pipeline",
                "contact": f"/contacts/{a.entity_id}",
                "account": f"/contacts?account={a.entity_id}",
                "email": f"/email",
                "note": f"/activities",
                "task": f"/activities",
            }
            entity_url = route_map.get(a.entity_type or "", "")

            results.append(
                {
                    "id": a.id,
                    "activity_type": a.activity_type,
                    "title": a.title,
                    "description": a.description,
                    "created_at": a.created_at.isoformat(),
                    "actor": {
                        "id": a.actor_id,
                        "name": actor_data.get("name", ""),
                        "avatar_url": actor_data.get("avatar_url", ""),
                    },
                    "entity": {
                        "type": a.entity_type or "",
                        "id": a.entity_id,
                        "name": entity_name,
                        "url": entity_url,
                    },
                    "metadata": a.metadata,
                }
            )

        return paginator.get_paginated_response(results)