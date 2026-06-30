"""Views for SAML 2.0 SSO — login, ACS, metadata, domain check, CRUD, logout."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from apps.core.permissions import RolePermission, TenantAwarePermission

from .models import SamlProvider
from .serializers import (
    SamlDomainCheckSerializer,
    SamlLoginSerializer,
    SamlProviderSerializer,
    UserSerializer,
)

UserModel = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def saml_sp_login(request: Request) -> Response:
    """POST /api/auth/saml/login/ — Start SP-initiated SAML login.

    Request: {email: "user@company.com"}
    Response: {redirect_url: "https://idp/...", relay_state: "/dashboard"}
    """
    from urllib.parse import urlencode

    serializer = SamlLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    domain = email.split("@")[1].lower()

    provider = _resolve_saml_provider(domain)
    if not provider:
        return Response(
            {"error": "No SAML provider configured for this domain."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Generate SAML AuthnRequest
    auth = _build_saml_auth(provider)
    # For SP-initiated, we need a request ID to validate the response
    import uuid
    request_id = str(uuid.uuid4())

    # Use the onelogin saml2 library
    try:
        # onelogin's prepare_for_redirect returns (url, request_id)
        # We need an empty RelayState — we use the client-side redirect
        saml_request = auth.login(custom_id=request_id)
        redirect_params = urlencode({"SAMLRequest": saml_request, "RelayState": "/dashboard"})
        redirect_url = f"{provider.idp_sso_url}?{redirect_params}"
    except Exception as e:
        return Response(
            {"error": f"Failed to generate SAML request: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({"redirect_url": redirect_url, "relay_state": "/dashboard"})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def saml_acs(request: Request, tenant_id: str) -> Response:
    """POST /api/auth/saml/{tenant_id}/acs/ — Assertion Consumer Service.

    Accepts form-encoded SAMLResponse from the IdP (HTTP-POST binding).
    Returns redirect URL with JWT tokens in hash fragment.
    """
    provider = get_object_or_404(SamlProvider, tenant_id=tenant_id, is_active=True)

    saml_response = request.data.get("SAMLResponse") or request.POST.get("SAMLResponse")
    if not saml_response:
        return Response(
            {"error": "SAMLResponse is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        auth = _build_saml_auth(provider)
        auth.process_response(request_id=None)

        if auth.get_errors():
            return Response(
                {"error": f"SAML response errors: {', '.join(auth.get_errors())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not auth.is_authenticated():
            return Response(
                {"error": "SAML authentication failed."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Extract attributes using the provider's attribute mapping
        saml_attrs = auth.get_attributes()
        attributes = _map_saml_attributes(saml_attrs, provider.attribute_mapping)
        attributes["email"] = attributes.get("email") or auth.get_nameid()
        if not attributes.get("email"):
            return Response(
                {"error": "SAML response must include an email attribute."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        return Response(
            {"error": f"SAML processing error: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # JIT provision or find user
    try:
        user, created = provision_user_from_saml(provider, attributes)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

    # Update last used
    provider.last_used_at = timezone.now()
    provider.save(update_fields=["last_used_at"])

    # Issue JWT tokens
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    if user.tenant_id:
        refresh.access_token["tenant_id"] = str(user.tenant_id)

    tokens = {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }

    # For IdP-initiated flows, return tokens in a redirect
    # For API-based flows, return directly
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    import urllib.parse
    fragment = urllib.parse.urlencode(tokens)
    redirect_url = f"{frontend_url}/auth/saml/callback#{fragment}"

    return Response({"redirect_url": redirect_url})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def saml_metadata(request: Request, tenant_id: str) -> Response:
    """GET /api/auth/saml/{tenant_id}/metadata/ — SP Metadata XML."""
    provider = get_object_or_404(SamlProvider, tenant_id=tenant_id, is_active=True)

    try:
        auth = _build_saml_auth(provider)
        metadata_xml = auth.get_settings().get_sp_metadata()
        errors = auth.get_settings().validate_metadata(metadata_xml)
        if errors:
            return Response(
                {"error": f"Invalid metadata: {', '.join(errors)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    except Exception as e:
        return Response(
            {"error": f"Failed to generate metadata: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(metadata_xml, content_type="application/xml")


@api_view(["GET"])
@permission_classes([AllowAny])
def saml_domain_check(request: Request) -> Response:
    """GET /api/auth/saml/domain-check/?email=user@company.com — Check SAML config."""
    serializer = SamlDomainCheckSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    domain = email.split("@")[1].lower()

    provider = _resolve_saml_provider(domain)

    if not provider:
        return Response({"has_saml": False})

    return Response(
        {
            "has_saml": True,
            "provider_name": provider.idp_entity_id,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def saml_logout(request: Request) -> Response:
    """POST /api/auth/saml/logout/ — SAML Single Logout.

    Request: {tenant_id: "uuid"}
    """
    tenant_id = request.data.get("tenant_id", "")
    if not tenant_id:
        tenant_id = getattr(request.user, "tenant_id", "")

    provider = SamlProvider.objects.filter(
        tenant_id=tenant_id, is_active=True
    ).first()

    if not provider or not provider.idp_slo_url:
        # No SLO configured — local logout only
        return Response({"redirect_url": None, "detail": "Logged out locally."})

    try:
        auth = _build_saml_auth(provider)
        logout_request = auth.logout(custom_id=str(request.user.id))
        return Response({"redirect_url": logout_request, "relay_state": "/login"})
    except Exception:
        return Response({"redirect_url": None, "detail": "SLO unavailable, logged out locally."})


# ── JIT Provisioning ──────────────────────────────────────────────────────────


def provision_user_from_saml(
    provider: SamlProvider,
    attributes: dict[str, str],
) -> tuple[Any, bool]:
    """Find or create a user from SAML attributes.

    Returns (user, created: bool).
    Raises ValueError for missing email, PermissionError for disabled auto-provisioning.
    """
    email = attributes.get("email", "")
    if not email:
        raise ValueError("SAML response must include an email attribute")

    # Look up by email
    try:
        user = UserModel.objects.get(email=email)
        return user, False
    except UserModel.DoesNotExist:
        pass

    # Create new user (JIT provisioning)
    if not provider.auto_create_users:
        raise PermissionError("No account found. Contact your administrator.")

    username = email.split("@")[0]
    base_username = username
    suffix = 1
    while UserModel.objects.filter(username=username).exists():
        username = f"{base_username}{suffix}"
        suffix += 1

    user = UserModel.objects.create(
        tenant_id=provider.tenant_id,
        email=email,
        username=username,
        first_name=attributes.get("first_name", ""),
        last_name=attributes.get("last_name", ""),
        avatar_url=attributes.get("avatar_url", ""),
        email_verified=True,
    )

    # Assign default role
    if provider.default_role_id:
        from apps.teams.models import Membership, Team

        default_team = Team.objects.filter(
            tenant_id=provider.tenant_id, name="Everyone"
        ).first()

        Membership.objects.create(
            user=user,
            tenant_id=provider.tenant_id,
            role_id=provider.default_role_id,
            team=default_team,
            is_active=True,
        )

    return user, True


# ── Helpers ───────────────────────────────────────────────────────────────────


def _resolve_saml_provider(domain: str) -> SamlProvider | None:
    """Find an active SamlProvider for the given email domain."""
    # Prefer exact domain match
    provider = SamlProvider.objects.filter(
        is_active=True,
        allowed_domains__contains=[domain],
    ).first()
    if provider:
        return provider
    # Fall back to providers with empty allowed_domains (allow any)
    return SamlProvider.objects.filter(
        is_active=True,
        allowed_domains=[],
    ).first()


def _build_saml_auth(provider: SamlProvider) -> Any:
    """Build a OneLogin_Saml2_Auth instance from a SamlProvider."""
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings

    sp_settings = provider.get_sp_settings()

    class _Request:
        """Minimal request object for OneLogin_Saml2_Auth."""
        def __init__(self, sp_settings: dict) -> None:
            self.settings = sp_settings

        def get_data(self, key: str) -> Any:
            return None

        def get_server_name(self) -> str:
            from urllib.parse import urlparse
            parsed = urlparse(settings.SAML_BASE_URL)
            return parsed.hostname or "localhost"

        def get_server_port(self) -> int:
            from urllib.parse import urlparse
            parsed = urlparse(settings.SAML_BASE_URL)
            port = parsed.port
            if port:
                return port
            return 443 if parsed.scheme == "https" else 80

        def get_request_uri(self) -> str:
            return settings.SAML_BASE_URL

    req_data = _Request(sp_settings)
    return OneLogin_Saml2_Auth(req_data, old_settings=sp_settings)


def _map_saml_attributes(
    saml_attrs: dict[str, list[str]],
    mapping: dict[str, str],
) -> dict[str, str]:
    """Map SAML attributes (list-valued) to user fields using the provider's mapping."""
    result: dict[str, str] = {}
    for user_field, saml_attr_name in mapping.items():
        values = saml_attrs.get(saml_attr_name, [])
        if values:
            result[user_field] = values[0]
    return result


# ── Management endpoints (CRUD) ───────────────────────────────────────────────


class SamlProviderListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/auth/saml/providers/ — List/create SAML providers for current tenant."""

    serializer_class = SamlProviderSerializer
    permission_classes = [IsAuthenticated, TenantAwarePermission, RolePermission]

    def get_queryset(self):
        return SamlProvider.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

    def get_serializer_class(self):
        # Dynamically set model for serializer
        from rest_framework import serializers as drf_serializers

        class _SamlProviderSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = SamlProvider
                fields = (
                    "id", "idp_entity_id", "idp_sso_url", "idp_slo_url",
                    "idp_x509_cert", "attribute_mapping", "default_role_id",
                    "auto_create_users", "allowed_domains", "is_active",
                    "sp_entity_id", "acs_url", "last_used_at", "tenant_id",
                )
                read_only_fields = ("id", "sp_entity_id", "acs_url", "last_used_at", "tenant_id")

        return _SamlProviderSerializer

    def get_required_permission(self) -> str | None:
        if self.request.method == "POST":
            return "team.manage_team"
        return None


class SamlProviderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/auth/saml/providers/{id}/ — SAML provider CRUD."""

    permission_classes = [IsAuthenticated, TenantAwarePermission, RolePermission]
    lookup_field = "id"

    def get_queryset(self):
        return SamlProvider.objects.filter(tenant_id=self.request.user.tenant_id)

    def get_serializer_class(self):
        from rest_framework import serializers as drf_serializers

        class _SamlProviderSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = SamlProvider
                fields = (
                    "id", "idp_entity_id", "idp_sso_url", "idp_slo_url",
                    "idp_x509_cert", "attribute_mapping", "default_role_id",
                    "auto_create_users", "allowed_domains", "is_active",
                    "sp_entity_id", "acs_url", "last_used_at", "tenant_id",
                )
                read_only_fields = ("id", "sp_entity_id", "acs_url", "last_used_at", "tenant_id")

        return _SamlProviderSerializer

    def get_required_permission(self) -> str | None:
        method = self.request.method
        if method in ("POST", "PATCH", "DELETE"):
            return "team.manage_team"
        return None
