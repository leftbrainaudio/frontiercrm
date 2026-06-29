"""ViewSet for the CSV import flow (preview → confirm + history)."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.contacts.csv_import import (
    ACCOUNT_FIELDS,
    CONTACT_FIELDS,
    DEAL_FIELDS,
    DEFAULT_DEDUP_KEYS,
    _parse_csv,
    auto_detect_mapping,
    import_accounts_csv,
    import_contacts_csv,
    import_deals_csv,
)

from .models import ImportJob
from .serializers import (
    ImportConfirmSerializer,
    ImportJobDetailSerializer,
    ImportJobListSerializer,
    ImportPreviewResponseSerializer,
    PreviewPayloadSerializer,
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_ROWS = 10_000

ENTITY_FIELD_SETS = {
    "contact": CONTACT_FIELDS | {"account_name"},
    "deal": DEAL_FIELDS | {"pipeline_name", "stage_name", "contact_email", "account_name"},
    "account": ACCOUNT_FIELDS,
}

IMPORT_FUNCTIONS = {
    "contact": import_contacts_csv,
    "deal": import_deals_csv,
    "account": import_accounts_csv,
}


def _format_preview(import_func, *, tenant_id, file_content, column_mapping,
                    dedup_key, conflict_strategy):
    """Run a dry-run import and format the result as a preview dict."""
    result = import_func(
        tenant_id=tenant_id,
        file_content=file_content,
        column_mapping=column_mapping,
        dedup_key=dedup_key,
        conflict_strategy=conflict_strategy,
        dry_run=True,
        skip_errors=True,
    )

    d = result.to_dict()
    preview = {
        "total_rows": d["total_rows"],
        "created_rows": d["created_count"],
        "updated_rows": d["updated_count"],
        "skipped_rows": d["skipped_count"],
        "error_rows": d["error_count"],
        "sample_created": d["created"][:5],
        "sample_skipped": d["skipped"][:5],
        "sample_errors": d["errors"][:5],
        "warnings": [],
    }

    if d["skipped_count"] and conflict_strategy == "skip":
        preview["warnings"].append(
            f"{d['skipped_count']} existing records will be skipped "
            f"(use conflict_strategy='update' to update them)"
        )

    return preview


class ImportViewSet(viewsets.GenericViewSet):
    """ViewSet for CSV import preview, confirm, and history.

    Routes:
      POST   /api/imports/<entity_type>/preview/    — Phase 1
      POST   /api/imports/<id>/confirm/              — Phase 2
      GET    /api/imports/                           — List history
      GET    /api/imports/<id>/                      — Detail
      DELETE /api/imports/<id>/                      — Soft-delete
    """
    queryset = ImportJob.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def get_serializer_class(self):
        if self.action == "list":
            return ImportJobListSerializer
        return ImportJobDetailSerializer

    def get_queryset(self):
        qs = ImportJob.objects.filter(
            tenant_id=self.request.user.tenant_id,
            deleted_at__isnull=True,
        )
        # Optional filtering
        params = self.request.query_params
        if entity_type := params.get("entity_type"):
            qs = qs.filter(entity_type=entity_type)
        if status_val := params.get("status"):
            qs = qs.filter(status=status_val)
        if created_by := params.get("created_by_id"):
            qs = qs.filter(created_by_id=created_by)
        # Filtering by date range
        if created_after := params.get("created_after"):
            qs = qs.filter(created_at__gte=created_after)
        if created_before := params.get("created_before"):
            qs = qs.filter(created_at__lte=created_before)
        return qs

    # ── Phase 1: Preview ─────────────────────────────────────────────────────

    @action(detail=False, methods=["post"],
            url_path=r"(?P<entity_type_raw>\w+)/preview")
    def preview(self, request, entity_type_raw=None):
        """Upload a CSV, detect columns, and return a dry-run preview."""
        # Normalize plural URL form → singular entity type
        PLURAL_MAP = {"contacts": "contact", "deals": "deal", "accounts": "account"}
        entity_type = PLURAL_MAP.get(entity_type_raw, entity_type_raw)

        if entity_type not in IMPORT_FUNCTIONS:
            return Response(
                {"error": f"Unsupported entity_type '{entity_type}'. "
                          f"Use one of: {', '.join(IMPORT_FUNCTIONS.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PreviewPayloadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data["file"]

        # File size check
        if uploaded_file.size > MAX_FILE_SIZE:
            return Response(
                {"error": "File exceeds maximum size of 10 MB"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # Read and decode file
        try:
            content = uploaded_file.read().decode("utf-8-sig")
        except Exception:
            return Response(
                {"error": "Failed to read file as UTF-8 text"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse CSV
        headers, rows = _parse_csv(content)

        if not headers:
            return Response(
                {"error": "CSV file has no headers "
                          "(first row must be column names)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(rows) > MAX_ROWS:
            return Response(
                {"error": f"CSV exceeds maximum of {MAX_ROWS:,} rows. "
                          f"Please split the file.",
                 "total_rows": len(rows)},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # Resolve column mapping
        user_mapping = serializer.validated_data.get("column_mapping")
        if user_mapping:
            column_mapping = user_mapping
        else:
            column_mapping = auto_detect_mapping(headers, entity_type)

        # Determine unmatched columns
        model_fields = ENTITY_FIELD_SETS.get(entity_type, set())
        unmatched = [
            h for h in headers
            if column_mapping.get(h, h) not in model_fields
        ]

        # Resolve strategy and dedup
        conflict_strategy = serializer.validated_data.get(
            "conflict_strategy", ImportJob.ConflictStrategy.SKIP
        )
        dedup_key = serializer.validated_data.get("dedup_key", None)
        if dedup_key is None:
            dedup_key = DEFAULT_DEDUP_KEYS.get(entity_type, "name")

        # Create the ImportJob in draft status
        import_job = ImportJob.objects.create(
            tenant_id=request.user.tenant_id,
            created_by_id=request.user.id or request.user.pk,
            entity_type=entity_type,
            status=ImportJob.Status.DRAFT,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            file_content=content,
            detected_columns=headers,
            column_mapping=column_mapping,
            dedup_key=dedup_key,
            conflict_strategy=conflict_strategy,
        )

        # Run dry-run preview
        import_func = IMPORT_FUNCTIONS[entity_type]
        try:
            preview_data = _format_preview(
                import_func,
                tenant_id=str(request.user.tenant_id),
                file_content=content,
                column_mapping=column_mapping,
                dedup_key=dedup_key,
                conflict_strategy=conflict_strategy,
            )
        except Exception as exc:
            import_job.status = ImportJob.Status.FAILED
            import_job.error_message = str(exc)
            import_job.save(update_fields=["status", "error_message", "updated_at"])
            return Response(
                {"error": "Preview failed", "detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save preview and advance status
        import_job.preview = preview_data
        import_job.status = ImportJob.Status.PREVIEWED
        import_job.save(update_fields=["preview", "status", "updated_at"])

        # Check for existing draft/previewed import jobs (warn, but allow)
        existing_drafts = ImportJob.objects.filter(
            tenant_id=request.user.tenant_id,
            entity_type=entity_type,
            deleted_at__isnull=True,
        ).exclude(
            id=import_job.id,
        ).filter(
            status__in=[ImportJob.Status.DRAFT, ImportJob.Status.PREVIEWED],
        )[:1]

        if existing_drafts.exists():
            warnings = list(preview_data.get("warnings", []))
            warnings.append(
                f"An existing draft import for {entity_type} is already in progress. "
                f"Consider completing or deleting it to avoid confusion."
            )
            preview_data["warnings"] = warnings

        resp_data = ImportPreviewResponseSerializer({
            "import_job_id": import_job.id,
            "status": import_job.status,
            "entity_type": import_job.entity_type,
            "original_filename": import_job.original_filename,
            "detected_columns": headers,
            "unmatched_columns": unmatched,
            "preview": preview_data,
            "dedup_key": import_job.dedup_key,
            "conflict_strategy": import_job.conflict_strategy,
        }).data

        return Response(resp_data)

    # ── Phase 2: Confirm ──────────────────────────────────────────────────────

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Execute the import for a previously previewed job."""
        import_job = self.get_object()

        if import_job.status in (
            ImportJob.Status.COMPLETED,
            ImportJob.Status.CONFIRMED,
        ):
            return Response(
                {"error": "Import job has already been confirmed",
                 "summary": import_job.summary},
                status=status.HTTP_409_CONFLICT,
            )

        if import_job.status == ImportJob.Status.FAILED:
            return Response(
                {"error": "Import job is in failed state "
                          "and cannot be confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if import_job.status not in (
            ImportJob.Status.PREVIEWED, ImportJob.Status.DRAFT,
        ):
            return Response(
                {"error": f"Import job is in '{import_job.status}' state "
                          f"and cannot be confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Allow optional overrides at confirm time
        confirm_ser = ImportConfirmSerializer(data=request.data)
        confirm_ser.is_valid(raise_exception=True)

        column_mapping = (
            confirm_ser.validated_data.get("column_mapping")
            or import_job.column_mapping
        )
        conflict_strategy = confirm_ser.validated_data.get(
            "conflict_strategy", import_job.conflict_strategy
        )

        # Mark as confirmed before running (ensures idempotent boundary)
        import_job.status = ImportJob.Status.CONFIRMED
        import_job.started_at = timezone.now()
        import_job.conflict_strategy = conflict_strategy
        if column_mapping:
            import_job.column_mapping = column_mapping
        import_job.save(
            update_fields=[
                "status", "started_at", "conflict_strategy",
                "column_mapping", "updated_at",
            ]
        )

        # Execute the import (non-dry-run)
        import_func = IMPORT_FUNCTIONS[import_job.entity_type]
        file_content = import_job.file_content

        if not file_content:
            # This should not happen since preview stores it, but guard anyway
            return Response(
                {"error": "Import file content is missing. "
                          "Please re-upload via preview."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                result = import_func(
                    tenant_id=str(request.user.tenant_id),
                    file_content=file_content,
                    column_mapping=column_mapping,
                    dedup_key=import_job.dedup_key,
                    conflict_strategy=conflict_strategy,
                    dry_run=False,
                    skip_errors=True,
                )
        except Exception as exc:
            import_job.status = ImportJob.Status.FAILED
            import_job.error_message = str(exc)
            import_job.completed_at = timezone.now()
            import_job.save(
                update_fields=[
                    "status", "error_message", "completed_at", "updated_at",
                ]
            )
            return Response(
                {"error": "Import failed", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Build summary
        d = result.to_dict()
        summary = {
            "total_rows": d["total_rows"],
            "created_count": d["created_count"],
            "updated_count": d["updated_count"],
            "skipped_count": d["skipped_count"],
            "error_count": d["error_count"],
            "errors": d["errors"][:50],  # cap error list
        }

        import_job.summary = summary
        import_job.status = ImportJob.Status.COMPLETED
        import_job.completed_at = timezone.now()
        import_job.save(
            update_fields=["summary", "status", "completed_at", "updated_at"]
        )

        return Response({
            "import_job_id": str(import_job.id),
            "status": import_job.status,
            "entity_type": import_job.entity_type,
            "summary": summary,
        })

    # ── List / Detail / Destroy ───────────────────────────────────────────────

    def list(self, request):
        """List import jobs for the current tenant."""
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ImportJobListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ImportJobListSerializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get full detail for a single import job."""
        import_job = self.get_object()
        serializer = ImportJobDetailSerializer(import_job)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        """Soft-delete an import job."""
        import_job = self.get_object()
        import_job.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)