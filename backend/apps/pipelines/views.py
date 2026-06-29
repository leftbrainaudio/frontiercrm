"""Serializers + Viewsets for pipeline & deal models."""

from __future__ import annotations

from django_filters.rest_framework import FilterSet
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.contacts.csv_import import import_deals_csv

from .models import Deal, Pipeline, Stage

# -- Pipeline -----------------------------------------------------------------


class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        exclude = ("deleted_at",)
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


class PipelineSerializer(serializers.ModelSerializer):
    stages = StageSerializer(many=True, read_only=True)

    class Meta:
        model = Pipeline
        exclude = ("deleted_at",)
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


class PipelineViewSet(viewsets.ModelViewSet):
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    filterset_fields = ["is_default", "is_active"]
    search_fields = ["name", "description"]

    def get_queryset(self):
        return Pipeline.objects.filter(tenant_id=self.request.user.tenant_id, deleted_at__isnull=True)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)


class StageViewSet(viewsets.ModelViewSet):
    queryset = Stage.objects.all()
    serializer_class = StageSerializer
    filterset_fields = ["pipeline", "is_active"]

    def get_queryset(self):
        return Stage.objects.filter(
            pipeline__tenant_id=self.request.user.tenant_id,
            deleted_at__isnull=True,
        )

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)


# -- Deal ---------------------------------------------------------------------


class DealSerializer(serializers.ModelSerializer):
    win_probability = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    weighted_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    pipeline_name = serializers.ReadOnlyField(source="pipeline.name", default="")
    stage_name = serializers.ReadOnlyField(source="stage.name", default="")
    contact_name = serializers.SerializerMethodField()
    account_name = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        exclude = ("deleted_at",)
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at", "entered_stage_at", "closed_at")

    def get_contact_name(self, obj: Deal) -> str:
        return str(obj.contact) if obj.contact else ""

    def get_account_name(self, obj: Deal) -> str:
        return str(obj.account) if obj.account else ""


class DealListSerializer(DealSerializer):
    """Lightweight serializer for deal list views (no extra FK joins)."""

    class Meta(DealSerializer.Meta):
        exclude = None  # clear parent's exclude
        fields = (
            "id",
            "name",
            "value",
            "currency",
            "status",
            "pipeline_name",
            "stage_name",
            "win_probability",
            "weighted_value",
            "contact_name",
            "account_name",
            "expected_close_date",
            "owner_id",
            "created_at",
        )


class DealFilter(FilterSet):
    class Meta:
        model = Deal
        fields = {
            "pipeline": ["exact"],
            "stage": ["exact"],
            "status": ["exact"],
            "owner_id": ["exact"],
            "contact": ["exact"],
            "account": ["exact"],
            "value": ["exact", "gte", "lte"],
            "expected_close_date": ["exact", "gte", "lte"],
        }


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    filterset_class = DealFilter
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "value", "expected_close_date", "status"]
    parser_classes = [FormParser, MultiPartParser]

    def get_serializer_class(self):
        if self.action == "list":
            return DealListSerializer
        return DealSerializer

    def get_queryset(self):
        return Deal.objects.filter(
            tenant_id=self.request.user.tenant_id,
            deleted_at__isnull=True,
        )

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

    @action(detail=True, methods=["post"])
    def move_stage(self, request, pk=None) -> Response:
        """Move a deal to a new stage, updating probability and tracking."""
        deal = self.get_object()
        stage_id = request.data.get("stage_id")
        if not stage_id:
            return Response({"error": "stage_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_stage = Stage.objects.get(id=stage_id, pipeline=deal.pipeline, tenant_id=request.user.tenant_id)
        except Stage.DoesNotExist:
            return Response({"error": "Stage not found in this pipeline"}, status=status.HTTP_404_NOT_FOUND)

        old_stage_name = deal.stage.name
        deal.stage = new_stage
        deal.entered_stage_at = serializers.DateTimeField().to_internal_value(
            serializers.DateTimeField().to_representation(deal.updated_at)
        )

        # Log activity
        from apps.activities.models import Activity

        Activity.objects.create(
            tenant_id=request.user.tenant_id,
            activity_type=Activity.ActivityType.DEAL_STAGE_CHANGE,
            title=f"Deal moved from '{old_stage_name}' to '{new_stage.name}'",
            entity_type="deal",
            entity_id=deal.id,
            actor_id=request.user.id,
            metadata={"old_stage": old_stage_name, "new_stage": new_stage.name},
        )

        deal.save()
        return Response(self.get_serializer(deal).data)

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None) -> Response:
        """Change deal status (won/lost/abandoned) and log close."""
        deal = self.get_object()
        new_status = request.data.get("status")
        if new_status not in ("won", "lost", "abandoned", "open"):
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        old_status = deal.status
        deal.status = new_status
        if new_status in ("won", "lost"):
            from django.utils import timezone

            deal.closed_at = timezone.now()
            deal.close_reason = request.data.get("close_reason", "")

        from apps.activities.models import Activity

        Activity.objects.create(
            tenant_id=request.user.tenant_id,
            activity_type=Activity.ActivityType.DEAL_STATUS_CHANGE,
            title=f"Deal status changed from '{old_status}' to '{new_status}'",
            entity_type="deal",
            entity_id=deal.id,
            actor_id=request.user.id,
            metadata={"old_status": old_status, "new_status": new_status, "close_reason": deal.close_reason},
        )

        deal.save()
        return Response(self.get_serializer(deal).data)

    @action(detail=False, methods=["post"], parser_classes=[FormParser, MultiPartParser])
    def import_csv(self, request):
        """Upload a CSV file and import deals.

        DEPRECATED: Use POST /api/imports/deals/preview/ instead.
        """
        from apps.imports.models import ImportJob
        from apps.imports.views import _format_preview

        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            content = file.read().decode("utf-8-sig")
        except Exception:
            return Response({"error": "Failed to read file as UTF-8 text"}, status=status.HTTP_400_BAD_REQUEST)

        column_mapping = request.data.get("column_mapping")
        if column_mapping and isinstance(column_mapping, str):
            import json
            try:
                column_mapping = json.loads(column_mapping)
            except json.JSONDecodeError:
                return Response({"error": "Invalid column_mapping JSON"}, status=status.HTTP_400_BAD_REQUEST)

        dry_run = str(request.data.get("dry_run", "true")).lower() == "true"
        update_existing = str(request.data.get("update_existing", "false")).lower() == "true"
        conflict_strategy = "update" if update_existing else "skip"

        # Create an ImportJob internally for audit trail
        import_job = ImportJob.objects.create(
            tenant_id=request.user.tenant_id,
            created_by_id=request.user.id or request.user.pk,
            entity_type=ImportJob.EntityType.DEAL,
            status=ImportJob.Status.DRAFT,
            original_filename=file.name,
            file_size=file.size,
            file_content=content,
            column_mapping=column_mapping or {},
            conflict_strategy=conflict_strategy,
        )

        if dry_run:
            preview_data = _format_preview(
                import_deals_csv,
                tenant_id=str(request.user.tenant_id),
                file_content=content,
                column_mapping=column_mapping,
                dedup_key=None,
                conflict_strategy=conflict_strategy,
            )
            import_job.preview = preview_data
            import_job.status = ImportJob.Status.PREVIEWED
            import_job.save(update_fields=["preview", "status", "updated_at"])
            # Build backward-compatible response
            result_data = {
                "created_count": preview_data["created_rows"],
                "updated_count": preview_data["updated_rows"],
                "skipped_count": preview_data["skipped_rows"],
                "error_count": preview_data["error_rows"],
                "total_rows": preview_data["total_rows"],
                "import_job_id": str(import_job.id),
                "created": preview_data.get("sample_created", []),
                "updated": [],
                "skipped": preview_data.get("sample_skipped", []),
                "errors": preview_data.get("sample_errors", []),
            }
        else:
            result = import_deals_csv(
                tenant_id=str(request.user.tenant_id),
                file_content=content,
                column_mapping=column_mapping,
                dry_run=False,
                conflict_strategy=conflict_strategy,
                dedup_key=None,
            )
            d = result.to_dict()
            import_job.summary = {
                "total_rows": d["total_rows"],
                "created_count": d["created_count"],
                "updated_count": d["updated_count"],
                "skipped_count": d["skipped_count"],
                "error_count": d["error_count"],
                "errors": d["errors"][:50],
            }
            import_job.status = ImportJob.Status.COMPLETED
            import_job.save(update_fields=["summary", "status", "updated_at"])
            result_data = d

        result_data["import_job_id"] = str(import_job.id)

        response = Response(result_data)
        response["X-Deprecation"] = "use /api/imports/deals/preview/ instead"
        return response