"""Serializers for EmailTemplate model."""
from __future__ import annotations

from rest_framework import serializers

from .models import EmailTemplate


class EmailTemplateListSerializer(serializers.ModelSerializer):
    """Compact serializer for list view — omits body content."""

    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EmailTemplate
        fields = [
            "id",
            "name",
            "description",
            "category",
            "is_shared",
            "created_by",
            "created_by_name",
            "variables_used",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "variables_used", "created_by_name"]

    def get_created_by_name(self, obj) -> str | None:
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Full serializer for detail view — includes body content."""

    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EmailTemplate
        fields = [
            "id",
            "tenant_id",
            "name",
            "description",
            "subject_template",
            "body_html",
            "body_text",
            "category",
            "is_shared",
            "created_by",
            "created_by_name",
            "variables_used",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "variables_used", "created_by", "created_by_name",
        ]

    def get_created_by_name(self, obj) -> str | None:
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None


class TemplatePreviewRequestSerializer(serializers.Serializer):
    """Request body for the preview endpoint."""

    context = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        default=dict,
    )


class TemplatePreviewResponseSerializer(serializers.Serializer):
    """Response shape for the preview endpoint."""

    rendered_subject = serializers.CharField()
    rendered_body_html = serializers.CharField()
    rendered_body_text = serializers.CharField()
    unresolved_variables = serializers.ListField(child=serializers.CharField())
    entity_preview = serializers.DictField(child=serializers.CharField(), required=False)