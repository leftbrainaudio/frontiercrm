"""Serializers + Viewsets for contacts app."""

from __future__ import annotations

from django_filters.rest_framework import FilterSet
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .csv_import import import_contacts_csv
from .models import Account, Contact

# -- Account -----------------------------------------------------------------


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


# -- Contact -----------------------------------------------------------------


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
    parser_classes = [FormParser, MultiPartParser]

    def get_serializer_class(self):
        if self.action == "list":
            return ContactListSerializer
        return ContactSerializer

    def get_queryset(self):
        return Contact.objects.filter(tenant_id=self.request.user.tenant_id, deleted_at__isnull=True)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

    @action(detail=False, methods=["post"], parser_classes=[FormParser, MultiPartParser])
    def import_csv(self, request):
        """Upload a CSV file and import contacts.

        Accepts multipart form data with:
          - file: the CSV file
          - column_mapping: optional JSON dict mapping CSV columns to model fields
          - dry_run: if 'true', preview only (no writes)
          - update_existing: if 'true', update matching contacts by email
        """
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

        result = import_contacts_csv(
            tenant_id=str(request.user.tenant_id),
            file_content=content,
            column_mapping=column_mapping,
            dry_run=dry_run,
            update_existing=update_existing,
        )

        return Response(result.to_dict())
