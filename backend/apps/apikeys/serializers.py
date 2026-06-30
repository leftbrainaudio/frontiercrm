"""Serializers for the API Key model."""

from __future__ import annotations

from rest_framework import serializers

from .models import APIKey


class APIKeySerializer(serializers.ModelSerializer):
    key = serializers.CharField(read_only=True)  # populated on create only

    class Meta:
        model = APIKey
        fields = (
            "id", "name", "key", "key_prefix", "permissions",
            "expires_at", "last_used_at", "last_ip_address",
            "is_active", "revoked_at", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "key", "key_prefix", "last_used_at",
            "last_ip_address", "is_active", "revoked_at",
            "created_at", "updated_at",
        )

    def create(self, validated_data):
        user = self.context["request"].user
        raw_key = APIKey.generate_key()
        instance = APIKey.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            name=validated_data["name"],
            key_prefix=APIKey.get_key_prefix(raw_key),
            key_hash=APIKey.hash_key(raw_key),
            permissions=validated_data.get("permissions", {}),
            expires_at=validated_data.get("expires_at"),
        )
        # Attach the plaintext key so the serializer can include it
        instance._plaintext_key = raw_key
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Inject plaintext key on create response only
        if hasattr(instance, "_plaintext_key"):
            data["key"] = instance._plaintext_key
        else:
            data.pop("key", None)  # never show on read/list
        return data
