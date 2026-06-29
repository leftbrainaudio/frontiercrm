"""Serializers + Viewsets for contacts app."""

from __future__ import annotations

from django_filters.rest_framework import FilterSet
from rest_framework import serializers, viewsets

from .models import Account, Contact

# ── Account ──────────────────────────────────────────────────────────────────


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        exclude = ("deleted_at",)
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


class AccountListSerializer(AccountSerializer):
    """Compact version for list views."""

    class Meta(AccountSerializer.Meta):
        exclude = None
        fields = ("id", "name", "domain", "industry", "city", "country", "logo_url", "created_at")


class AccountFilter(FilterSet):
    class Meta:
        model = Account
        fields = {
            "name": ["exact", "icontains"],
            "domain": ["exact", "icontains"],
            "industry": ["exact", "icontains"],
            "city": ["exact", "icontains"],
            "country": ["exact"],
            "owner_id": ["exact"],
        }


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filterset_class = AccountFilter
    search_fields = ["name", "domain", "industry", "city", "description"]
    ordering_fields = ["name", "created_at", "industry"]

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.action == "list":
            return AccountListSerializer
        return AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(tenant_id=self.request.user.tenant_id, deleted_at__isnull=True)

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        serializer.save(tenant_id=self.request.user.tenant_id)


# ── Contact ──────────────────────────────────────────────────────────────────


class ContactSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    account_name = serializers.ReadOnlyField(source="account.name", default="")

    class Meta:
        model = Contact
        exclude = ("deleted_at",)
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


class ContactListSerializer(ContactSerializer):
    class Meta(ContactSerializer.Meta):
        exclude = None
        fields = (
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "job_title",
            "account_name",
            "avatar_url",
            "city",
            "created_at",
        )


class ContactFilter(FilterSet):
    class Meta:
        model = Contact
        fields = {
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


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilter
    search_fields = ["first_name", "last_name", "email", "phone", "job_title"]
    ordering_fields = ["created_at", "last_name", "first_name", "email"]

    def get_serializer_class(self):
        if self.action == "list":
            return ContactListSerializer
        return ContactSerializer

    def get_queryset(self):
        return Contact.objects.filter(tenant_id=self.request.user.tenant_id, deleted_at__isnull=True)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)
