"""Views and viewsets for email messages and email templates."""
from __future__ import annotations

from django.utils import timezone
from django_filters.rest_framework import FilterSet, filters
from rest_framework import serializers as drf_serializers, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import RolePermission, TenantAwarePermission

from .models import EmailMessage, EmailTemplate
from .serializers import (
    EmailTemplateListSerializer,
    EmailTemplateSerializer,
    TemplatePreviewRequestSerializer,
)
from .services import VariableResolver
from .tasks import send_gmail_message


# ── Email CRUD (existing) ─────────────────────────────────────────────────────


class EmailSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = EmailMessage
        exclude = ()
        read_only_fields = (
            "id", "tenant_id", "created_at", "updated_at",
            "message_id", "thread_id", "external_id",
            "sent_at", "is_read", "is_starred", "labels",
            "provider_labels", "gmail_history_id", "smtp_id",
            "size_estimate", "received_at",
        )


class EmailSendStatusSerializer(drf_serializers.Serializer):
    status = drf_serializers.CharField()
    error_message = drf_serializers.CharField(required=False, allow_blank=True)
    message_id = drf_serializers.CharField(required=False, allow_blank=True)


class EmailFilter(FilterSet):
    class Meta:
        model = EmailMessage
        fields = {
            "direction": ["exact"],
            "from_email": ["exact", "icontains"],
            "thread_id": ["exact"],
            "entity_type": ["exact"],
            "entity_id": ["exact"],
            "contact": ["exact"],
            "deal": ["exact"],
            "is_read": ["exact"],
            "is_starred": ["exact"],
        }


class EmailViewSet(viewsets.ModelViewSet):
    queryset = EmailMessage.objects.all()
    serializer_class = EmailSerializer
    filterset_class = EmailFilter
    search_fields = ["subject", "body_text", "from_email"]
    ordering_fields = ["-sent_at"]
    permission_classes = [TenantAwarePermission, RolePermission]

    def get_required_permission(self) -> str | None:
        return {
            "list": "email.view",
            "retrieve": "email.view",
            "create": "email.send",
            "update": None,
            "partial_update": None,
            "destroy": "email.delete",
        }.get(self.action)

    def get_queryset(self):
        return EmailMessage.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        user = self.request.user

        # Fail fast if Gmail is not connected
        if not user.google_refresh_token:
            raise drf_serializers.ValidationError(
                "No Gmail connection configured. Connect Gmail from the email page first."
            )

        email = serializer.save(
            tenant_id=user.tenant_id,
            from_email=user.email,
            status=EmailMessage.EmailStatus.SENDING,
            direction=EmailMessage.EmailDirection.OUTBOUND,
            sent_at=timezone.now(),
        )
        # Enqueue async Gmail send
        send_gmail_message.delay(str(user.id), str(email.id))

    @action(detail=True, methods=["get"])
    def send_status(self, request, pk=None) -> Response:
        email = self.get_object()
        data: dict[str, str] = {"status": email.status}
        if email.error_message:
            data["error_message"] = email.error_message
        if email.external_id:
            data["message_id"] = email.external_id
        serializer = EmailSendStatusSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def toggle_star(self, request, pk=None) -> Response:
        email = self.get_object()
        email.is_starred = not email.is_starred
        email.save()
        return Response(self.get_serializer(email).data)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None) -> Response:
        email = self.get_object()
        email.is_read = True
        email.save()
        return Response(self.get_serializer(email).data)


# ── Email Templates ───────────────────────────────────────────────────────────


class EmailTemplateFilter(FilterSet):
    search = filters.CharFilter(method="filter_search")
    category = filters.CharFilter(field_name="category", lookup_expr="exact")
    is_shared = filters.BooleanFilter(field_name="is_shared")
    created_by = filters.UUIDFilter(field_name="created_by")

    class Meta:
        model = EmailTemplate
        fields = ["category", "is_shared", "created_by"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            drf_serializers.Q(name__icontains=value) | drf_serializers.Q(description__icontains=value)
        )


class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    permission_classes = [TenantAwarePermission, RolePermission]
    filterset_class = EmailTemplateFilter
    ordering_fields = ["name", "-updated_at", "category"]
    ordering = ["-updated_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return EmailTemplateListSerializer
        return EmailTemplateSerializer

    def get_required_permission(self) -> str | None:
        permission_map = {
            "list": "template.view",
            "retrieve": "template.view",
            "create": "template.edit",
            "update": "template.edit",
            "partial_update": "template.edit",
            "destroy": "template.edit",
            "preview": "template.view",
        }
        return permission_map.get(self.action)

    def get_queryset(self):
        qs = EmailTemplate.objects.filter(
            tenant_id=self.request.user.tenant_id,
            deleted_at__isnull=True,
        )
        # If user doesn't have template.edit, only show shared + own templates
        if not self.request.user.has_permission("template.edit"):
            qs = qs.filter(
                drf_serializers.Q(is_shared=True) | drf_serializers.Q(created_by=self.request.user)
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(
            tenant_id=self.request.user.tenant_id,
            created_by=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def preview(self, request, pk=None) -> Response:
        """Resolve {{variable}} placeholders with CRM context."""
        template = self.get_object()
        serializer = TemplatePreviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        context = serializer.validated_data.get("context", {})

        # Build resolver
        resolver = VariableResolver(request.user, request.user.tenant)

        # Extract entity IDs from context dict (keys are passed as strings)
        entity_mapping = self._extract_entity_ids(context)
        resolver.set_contact(entity_mapping.get("contact_id"))
        resolver.set_deal(entity_mapping.get("deal_id"))
        resolver.set_account(entity_mapping.get("account_id"))

        # Set explicit custom variables (everything that isn't a known entity key)
        custom_vars = {k: v for k, v in context.items() if k not in entity_mapping}
        resolver.set_explicit_context(custom_vars)

        # Resolve
        rendered_subject, unresolved_subject = resolver.resolve(template.subject_template)
        rendered_body_html, unresolved_body = resolver.resolve(template.body_html)
        rendered_body_text, unresolved_text = resolver.resolve(template.body_text)

        # Merge unresolved
        all_unresolved = list(set(unresolved_subject + unresolved_body + unresolved_text))

        return Response({
            "rendered_subject": rendered_subject,
            "rendered_body_html": rendered_body_html,
            "rendered_body_text": rendered_body_text,
            "unresolved_variables": all_unresolved,
        })

    @staticmethod
    def _extract_entity_ids(context: dict) -> dict[str, str | None]:
        """Extract known entity ID keys from context dict."""
        return {
            "contact_id": context.pop("contact_id", None) or context.pop("contact", None),
            "deal_id": context.pop("deal_id", None) or context.pop("deal", None),
            "account_id": context.pop("account_id", None) or context.pop("account", None),
        }

    def destroy(self, request, *args, **kwargs):
        """Soft-delete — set deleted_at instead of hard-deleting."""
        instance = self.get_object()
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])
        return Response(status=204)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def template_variables(request):
    """Return the full catalog of available variables."""
    catalog = VariableResolver.get_variable_catalog()
    return Response({"variables": catalog})