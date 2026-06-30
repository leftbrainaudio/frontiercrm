"""Serializers for the AuditLog model."""

from __future__ import annotations

from rest_framework import serializers

from apps.core.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Compact serializer for audit log list view."""

    actor_name = serializers.SerializerMethodField()
    actor_email = serializers.SerializerMethodField()
    action_label = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "actor_name",
            "actor_email",
            "action",
            "action_label",
            "entity_type",
            "entity_id",
            "entity_name",
            "details",
            "created_at",
        ]

    def get_actor_name(self, obj: AuditLog) -> str:
        if obj.actor:
            full = f"{obj.actor.first_name} {obj.actor.last_name}".strip()
            return full or obj.actor.email
        return "System"

    def get_actor_email(self, obj: AuditLog) -> str:
        return obj.actor.email if obj.actor else ""

    def get_action_label(self, obj: AuditLog) -> str:
        return obj.get_action_display()
