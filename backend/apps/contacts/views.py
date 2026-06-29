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

        DEPRECATED: Use POST /api/imports/contacts/preview/ instead.
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
            entity_type=ImportJob.EntityType.CONTACT,
            status=ImportJob.Status.DRAFT,
            original_filename=file.name,
            file_size=file.size,
            file_content=content,
            column_mapping=column_mapping or {},
            conflict_strategy=conflict_strategy,
        )

        if dry_run:
            preview_data = _format_preview(
                import_contacts_csv,
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
            result = import_contacts_csv(
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
        response["X-Deprecation"] = "use /api/imports/contacts/preview/ instead"
        return response
