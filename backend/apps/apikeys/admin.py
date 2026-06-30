"""Django admin registration for API Key model."""

from __future__ import annotations

from django.contrib import admin

from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "key_prefix",
        "user",
        "tenant_id",
        "is_active",
        "is_expired",
        "is_revoked",
        "last_used_at",
        "created_at",
    ]
    list_filter = ["is_active", "tenant_id", "revoked_at"]
    search_fields = ["name", "key_prefix"]
    readonly_fields = [
        "tenant_id",
        "key_prefix",
        "key_hash",
        "user",
        "last_used_at",
        "last_ip_address",
        "created_at",
        "updated_at",
        "revoked_at",
    ]
