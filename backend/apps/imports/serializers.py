"""Serializers for the imports app."""

from __future__ import annotations

from rest_framework import serializers

from .models import ImportJob


class ImportJobListSerializer(serializers.ModelSerializer):
    """Compact serializer for listing import jobs."""

    class Meta:
        model = ImportJob
        fields = (
            "id",
            "entity_type",
            "status",
            "original_filename",
            "dedup_key",
            "conflict_strategy",
            "summary",
            "created_at",
            "completed_at",
        )
        read_only_fields = fields


class ImportJobDetailSerializer(serializers.ModelSerializer):
    """Full detail for a single import job."""

    class Meta:
        model = ImportJob
        fields = (
            "id",
            "entity_type",
            "status",
            "original_filename",
            "file_size",
            "detected_columns",
            "column_mapping",
            "dedup_key",
            "conflict_strategy",
            "preview",
            "summary",
            "error_message",
            "created_at",
            "updated_at",
            "started_at",
            "completed_at",
        )
        read_only_fields = fields


class ImportPreviewResponseSerializer(serializers.Serializer):
    """Response shape for the preview endpoint."""

    import_job_id = serializers.UUIDField()
    status = serializers.CharField()
    entity_type = serializers.CharField()
    original_filename = serializers.CharField()
    detected_columns = serializers.ListField(child=serializers.CharField())
    unmatched_columns = serializers.ListField(child=serializers.CharField())
    preview = serializers.JSONField()
    dedup_key = serializers.CharField(allow_null=True)
    conflict_strategy = serializers.CharField()


class ImportConfirmSerializer(serializers.Serializer):
    """Optional overrides at confirm time."""

    column_mapping = serializers.JSONField(required=False)
    conflict_strategy = serializers.ChoiceField(
        choices=ImportJob.ConflictStrategy.choices, required=False
    )


# ── Preview payload serializer ────────────────────────────────────────────────


class PreviewPayloadSerializer(serializers.Serializer):
    """Validates multipart form-data for the preview endpoint."""

    file = serializers.FileField()
    column_mapping = serializers.JSONField(required=False)
    dedup_key = serializers.CharField(required=False, allow_null=True)
    conflict_strategy = serializers.ChoiceField(
        choices=ImportJob.ConflictStrategy.choices, required=False
    )