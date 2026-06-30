"""Serializers + Viewsets for contacts app."""

from __future__ import annotations

from django_filters.rest_framework import FilterSet
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import RolePermission, TenantAwarePermission

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
    permission_classes = [TenantAwarePermission, RolePermission]

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.action == "list":
            return AccountListSerializer
        return AccountSerializer

    def get_required_permission(self) -> str | None:
        return {
            "list": "contacts.view",
            "retrieve": "contacts.view",
            "create": "contacts.create",
            "update": "contacts.edit",
            "partial_update": "contacts.edit",
            "destroy": "contacts.delete",
        }.get(self.action)

    def get_queryset(self):
        return Account.objects.filter(tenant_id=self.request.user.tenant_id, deleted_at__isnull=True)

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        serializer.save(tenant_id=self.request.user.tenant_id)

    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        """Streaming CSV export of accounts.
        GET /api/contacts/accounts/export_csv/
        """
        from django.http import StreamingHttpResponse

        qs = self.get_queryset().only(
            "name", "domain", "industry", "description", "website",
            "phone", "address_line1", "address_line2", "city", "state",
            "postal_code", "country", "employees_count", "annual_revenue",
            "logo_url", "owner_id", "tags", "custom_fields",
            "created_at", "updated_at",
        )

        # Filters
        search = request.query_params.get("search", "").strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(domain__icontains=search)
                | Q(industry__icontains=search)
                | Q(city__icontains=search)
            )
        industry = request.query_params.get("industry", "").strip()
        if industry:
            qs = qs.filter(industry__iexact=industry)
        owner_id = request.query_params.get("owner_id", "").strip()
        if owner_id:
            qs = qs.filter(owner_id=owner_id)

        headers = [
            "Name", "Domain", "Industry", "Description", "Website",
            "Phone", "Address Line 1", "Address Line 2", "City", "State",
            "Postal Code", "Country", "Employees Count", "Annual Revenue",
            "Logo URL", "Owner ID", "Owner Name", "Tags",
            "Created At", "Updated At",
        ]

        def stream():
            import csv, io
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(headers)
            yield buf.getvalue()

            user_cache: dict[str, str] = {}

            for obj in qs.iterator(chunk_size=500):
                owner_name = ""
                if obj.owner_id:
                    oid = str(obj.owner_id)
                    if oid not in user_cache:
                        from apps.accounts.models import User
                        user = User.objects.filter(id=oid).values("first_name", "last_name").first()
                        user_cache[oid] = f"{user['first_name']} {user['last_name']}".strip() if user else ""
                    owner_name = user_cache[oid]

                tags_str = ", ".join(obj.tags) if obj.tags else ""
                annual_revenue = float(obj.annual_revenue) if obj.annual_revenue else ""

                buf.seek(0)
                buf.truncate()
                writer.writerow([
                    obj.name, obj.domain, obj.industry, obj.description,
                    obj.website, obj.phone, obj.address_line1, obj.address_line2,
                    obj.city, obj.state, obj.postal_code, obj.country,
                    obj.employees_count or "", annual_revenue,
                    obj.logo_url, str(obj.owner_id or ""), owner_name, tags_str,
                    obj.created_at.isoformat() if obj.created_at else "",
                    obj.updated_at.isoformat() if obj.updated_at else "",
                ])
                yield buf.getvalue()

        response = StreamingHttpResponse(stream(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="accounts.csv"'
        return response


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
    permission_classes = [TenantAwarePermission, RolePermission]

    def get_serializer_class(self):
        if self.action == "list":
            return ContactListSerializer
        return ContactSerializer

    def get_required_permission(self) -> str | None:
        return {
            "list": "contacts.view",
            "retrieve": "contacts.view",
            "create": "contacts.create",
            "update": "contacts.edit",
            "partial_update": "contacts.edit",
            "destroy": "contacts.delete",
        }.get(self.action)

    def get_queryset(self):
        return Contact.objects.filter(tenant_id=self.request.user.tenant_id, deleted_at__isnull=True)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        """Streaming CSV export of contacts.
        GET /api/contacts/contacts/export_csv/
        """
        from django.http import StreamingHttpResponse

        qs = self.get_queryset().select_related("account").only(
            "first_name", "last_name", "email", "phone", "mobile",
            "job_title", "department", "avatar_url", "linkedin_url",
            "twitter_handle", "street", "city", "state", "postal_code",
            "country", "owner_id", "source", "tags", "custom_fields",
            "created_at", "updated_at", "account",
        )

        # Apply filters
        search = request.query_params.get("search", "").strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
                | Q(job_title__icontains=search)
            )
        tags = request.query_params.get("tags", "").strip()
        if tags:
            qs = qs.filter(tags__overlap=[t.strip() for t in tags.split(",") if t.strip()])
        owner_id = request.query_params.get("owner_id", "").strip()
        if owner_id:
            qs = qs.filter(owner_id=owner_id)
        source = request.query_params.get("source", "").strip()
        if source:
            qs = qs.filter(source__iexact=source)

        headers = [
            "First Name", "Last Name", "Email", "Phone", "Mobile",
            "Job Title", "Department", "Avatar URL", "LinkedIn URL",
            "Twitter Handle", "Street", "City", "State", "Postal Code",
            "Country", "Owner ID", "Owner Name", "Source", "Tags",
            "Account Name", "Created At", "Updated At",
        ]

        def stream():
            import csv, io
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(headers)
            yield buf.getvalue()

            # Batch-resolve owner names
            user_cache: dict[str, str] = {}

            for obj in qs.iterator(chunk_size=500):
                owner_name = ""
                if obj.owner_id:
                    oid = str(obj.owner_id)
                    if oid not in user_cache:
                        from apps.accounts.models import User
                        user = User.objects.filter(id=oid).values("first_name", "last_name").first()
                        user_cache[oid] = f"{user['first_name']} {user['last_name']}".strip() if user else ""
                    owner_name = user_cache[oid]

                tags_str = ", ".join(obj.tags) if obj.tags else ""
                account_name = obj.account.name if obj.account else ""

                buf.seek(0)
                buf.truncate()
                writer.writerow([
                    obj.first_name, obj.last_name, obj.email, obj.phone,
                    obj.mobile, obj.job_title, obj.department, obj.avatar_url,
                    obj.linkedin_url, obj.twitter_handle, obj.street, obj.city,
                    obj.state, obj.postal_code, obj.country,
                    str(obj.owner_id or ""), owner_name, obj.source, tags_str,
                    account_name,
                    obj.created_at.isoformat() if obj.created_at else "",
                    obj.updated_at.isoformat() if obj.updated_at else "",
                ])
                yield buf.getvalue()

        response = StreamingHttpResponse(stream(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="contacts.csv"'
        return response

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
