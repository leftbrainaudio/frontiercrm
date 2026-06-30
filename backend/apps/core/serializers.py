"""Serializers for core models."""

from __future__ import annotations

from rest_framework import serializers

from .models import CustomFieldDef


class CustomFieldDefSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFieldDef
        exclude = ("deleted_at",)
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")
