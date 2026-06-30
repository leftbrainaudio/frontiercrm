"""Views for authentication — signup, login, magic link, Google OAuth."""

from __future__ import annotations

import secrets
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.permissions import RolePermission, TenantAwarePermission
from apps.teams.models import Membership, Role

from .serializers import (
    LoginSerializer,
    MagicLinkConfirmSerializer,
    MagicLinkRequestSerializer,
    SignupSerializer,
    UserSerializer,
)

UserModel = get_user_model()


class SignupView(generics.CreateAPIView):
    """Create a new user account."""

    queryset = UserModel.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request: Request) -> Response:
    """Authenticate with email + password, return JWT tokens.

    If user has 2FA enabled, returns a short-lived 2fa_token instead.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]

    # ── 2FA check ────────────────────────────────────────────────────────
    if user.totp_enabled:
        from .auth import TwoFactorToken
        twofa_token = TwoFactorToken.for_user(user)
        return Response(
            {
                "2fa_required": True,
                "2fa_token": str(twofa_token),
                "user": {"id": str(user.id), "email": user.email},
            }
        )

    refresh = RefreshToken.for_user(user)
    # Attach tenant_id to token
    if user.tenant_id:
        refresh.access_token["tenant_id"] = str(user.tenant_id)
    return Response(
        {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def magic_link_request(request: Request) -> Response:
    """Generate and send a magic link token via email."""
    serializer = MagicLinkRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    user = UserModel.objects.get(email=email)
    user.magic_link_token = secrets.token_urlsafe(48)
    user.magic_link_created_at = timezone.now()
    user.save(update_fields=["magic_link_token", "magic_link_created_at"])

    link = f"{request.build_absolute_uri('/api/auth/magic-link/confirm/')}?token={user.magic_link_token}"
    send_mail(
        subject="Your FrontierCRM magic sign-in link",
        message=f"Click to sign in: {link}\n\nThis link expires in 15 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=True,
    )
    return Response({"detail": "Magic link sent to email."})


@api_view(["POST"])
@permission_classes([AllowAny])
def magic_link_confirm(request: Request) -> Response:
    """Confirm magic link and return JWT tokens."""
    serializer = MagicLinkConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    refresh = RefreshToken.for_user(user)
    if user.tenant_id:
        refresh.access_token["tenant_id"] = str(user.tenant_id)
    return Response(
        {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def google_oauth_init(request: Request) -> Response:
    """Redirect user to Google OAuth consent screen."""
    from urllib.parse import urlencode

    params = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile https://www.googleapis.com/auth/gmail.modify",
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    return Response(
        {
            "authorization_url": f"https://accounts.google.com/o/oauth2/auth?{params}",
        }
    )


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def google_oauth_callback(request: Request) -> Response:
    """Handle Google OAuth callback — exchange code for tokens."""
    import requests as http_requests

    code = request.data.get("code") if request.method == "POST" else request.GET.get("code")
    if not code:
        return Response({"error": "Authorization code required."}, status=status.HTTP_400_BAD_REQUEST)

    # Exchange code for tokens
    token_resp = http_requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    token_data = token_resp.json()
    if "access_token" not in token_data:
        return Response({"error": "Failed to exchange authorization code."}, status=status.HTTP_400_BAD_REQUEST)

    # Get user info from Google
    user_info_resp = http_requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
        timeout=10,
    )
    user_info = user_info_resp.json()
    google_id = user_info.get("id")
    email = user_info.get("email")

    if not google_id or not email:
        return Response({"error": "Failed to get user info from Google."}, status=status.HTTP_400_BAD_REQUEST)

    # Find or create user
    user, created = UserModel.objects.get_or_create(
        google_id=google_id,
        defaults={
            "email": email,
            "username": email.split("@")[0],
            "first_name": user_info.get("given_name", ""),
            "last_name": user_info.get("family_name", ""),
            "avatar_url": user_info.get("picture", ""),
            "email_verified": True,
            "google_access_token": token_data.get("access_token", ""),
            "google_refresh_token": token_data.get("refresh_token", ""),
        },
    )
    if not created:
        user.google_access_token = token_data.get("access_token", user.google_access_token)
        if "refresh_token" in token_data:
            user.google_refresh_token = token_data["refresh_token"]
        user.save(update_fields=["google_access_token", "google_refresh_token"])

    refresh = RefreshToken.for_user(user)
    if user.tenant_id:
        refresh.access_token["tenant_id"] = str(user.tenant_id)
    return Response(
        {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me_view(request: Request) -> Response:
    """Get or update the current user's profile."""
    if request.method == "GET":
        return Response(UserSerializer(request.user).data)
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


# ── Social Auth (Login via Google / Microsoft) ────────────────────────────────

SOCIAL_PROVIDERS: dict[str, dict[str, Any]] = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile",
        "id_field": "google_id",
        "access_token_field": "google_access_token",
        "refresh_token_field": "google_refresh_token",
        "client_id": lambda s: s.GOOGLE_CLIENT_ID,
        "client_secret": lambda s: s.GOOGLE_CLIENT_SECRET,
        "redirect_uri": lambda s: s.GOOGLE_OAUTH_REDIRECT_URI,
    },
    "microsoft": {
        "auth_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid email profile User.Read",
        "id_field": "microsoft_id",
        "access_token_field": "microsoft_access_token",
        "refresh_token_field": "microsoft_refresh_token",
        "client_id": lambda s: s.MICROSOFT_CLIENT_ID,
        "client_secret": lambda s: s.MICROSOFT_CLIENT_SECRET,
        "redirect_uri": lambda s: s.MICROSOFT_OAUTH_REDIRECT_URI,
    },
}


@api_view(["GET"])
@permission_classes([AllowAny])
def social_auth_init(request: Request, provider: str) -> Response:
    """GET /api/auth/social/{provider}/init/ — return authorization URL."""
    from urllib.parse import urlencode

    cfg = SOCIAL_PROVIDERS.get(provider)
    if not cfg:
        return Response({"error": f"Unsupported provider '{provider}'."}, status=status.HTTP_400_BAD_REQUEST)

    redirect_uri = request.query_params.get("redirect_uri", "") or cfg["redirect_uri"](settings)
    auth_url = cfg["auth_url"]
    if "{tenant}" in auth_url:
        tenant = settings.MICROSOFT_TENANT if provider == "microsoft" else "common"
        auth_url = auth_url.replace("{tenant}", tenant)

    params = urlencode({
        "client_id": cfg["client_id"](settings),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": cfg["scope"],
        "access_type": "online",
    })

    return Response({"authorization_url": f"{auth_url}?{params}"})


@api_view(["POST"])
@permission_classes([AllowAny])
def social_auth_callback(request: Request) -> Response:
    """POST /api/auth/social/ — exchange auth code for JWT tokens.

    Request body: {provider: str, code: str, redirect_uri?: str}
    """
    import requests as http_requests

    provider = request.data.get("provider", "")
    code = request.data.get("code", "")
    redirect_uri = request.data.get("redirect_uri", "")

    if not provider or not code:
        return Response({"error": "provider and code are required."}, status=status.HTTP_400_BAD_REQUEST)

    cfg = SOCIAL_PROVIDERS.get(provider)
    if not cfg:
        return Response({"error": f"Unsupported provider '{provider}'."}, status=status.HTTP_400_BAD_REQUEST)

    token_url = cfg["token_url"]
    if "{tenant}" in token_url:
        tenant = settings.MICROSOFT_TENANT if provider == "microsoft" else "common"
        token_url = token_url.replace("{tenant}", tenant)

    effective_redirect = redirect_uri or cfg["redirect_uri"](settings)

    # Exchange code for tokens
    token_resp = http_requests.post(
        token_url,
        data={
            "code": code,
            "client_id": cfg["client_id"](settings),
            "client_secret": cfg["client_secret"](settings),
            "redirect_uri": effective_redirect,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    token_data = token_resp.json()
    if "access_token" not in token_data:
        return Response(
            {"error": "Failed to exchange authorization code.", "details": token_data.get("error_description", "")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get user info from the provider
    userinfo_url = cfg["userinfo_url"]
    if "{tenant}" in userinfo_url:
        tenant = settings.MICROSOFT_TENANT if provider == "microsoft" else "common"
        userinfo_url = userinfo_url.replace("{tenant}", tenant)

    user_info_resp = http_requests.get(
        userinfo_url,
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
        timeout=10,
    )
    user_info = user_info_resp.json()

    if provider == "google":
        provider_user_id = user_info.get("id", "")
        email = user_info.get("email", "")
        first_name = user_info.get("given_name", "")
        last_name = user_info.get("family_name", "")
        avatar = user_info.get("picture", "")
    elif provider == "microsoft":
        provider_user_id = user_info.get("id", "")
        email = user_info.get("mail", "") or user_info.get("userPrincipalName", "")
        first_name = user_info.get("givenName", "")
        last_name = user_info.get("surname", "")
        avatar = ""
    else:
        return Response({"error": f"Unsupported provider '{provider}'."}, status=status.HTTP_400_BAD_REQUEST)

    if not provider_user_id or not email:
        return Response({"error": "Failed to get user info from provider."}, status=status.HTTP_400_BAD_REQUEST)

    id_field = cfg["id_field"]
    access_token_field = cfg["access_token_field"]
    refresh_token_field = cfg["refresh_token_field"]

    # Find or create user
    lookup = {id_field: provider_user_id}
    defaults = {
        "email": email,
        "username": email.split("@")[0],
        "first_name": first_name,
        "last_name": last_name,
        "avatar_url": avatar,
        "email_verified": True,
        access_token_field: token_data.get("access_token", ""),
        refresh_token_field: token_data.get("refresh_token", ""),
    }

    user, created = UserModel.objects.get_or_create(
        defaults=defaults,
        **lookup,  # type: ignore[arg-type]
    )

    if not created:
        # Update tokens on the existing user
        setattr(user, access_token_field, token_data.get("access_token", getattr(user, access_token_field, "")))
        if "refresh_token" in token_data:
            setattr(user, refresh_token_field, token_data["refresh_token"])
        user.save(
            update_fields=[access_token_field, refresh_token_field]
            if "refresh_token" in token_data
            else [access_token_field]
        )

    refresh = RefreshToken.for_user(user)
    if user.tenant_id:
        refresh.access_token["tenant_id"] = str(user.tenant_id)
    return Response(
        {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    )


# ── RBAC Endpoints under /api/accounts/ ──────────────────────────────────


class RoleListCreateView(generics.ListCreateAPIView):
    """GET /api/accounts/roles/ — list roles for current tenant.
    POST /api/accounts/roles/ — create a new role (requires manage_roles).
    """

    queryset = Role.objects.all()
    permission_classes = [IsAuthenticated, TenantAwarePermission, RolePermission]

    def get_queryset(self):
        return Role.objects.filter(tenant_id=self.request.user.tenant_id)

    def get_serializer_class(self):
        from apps.teams.views import RoleSerializer
        return RoleSerializer

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.user.tenant_id)

    def get_required_permission(self) -> str | None:
        if self.request.method == "POST":
            return "team.manage_roles"
        return None  # GET requires auth only


class UserRoleUpdateView(generics.UpdateAPIView):
    """PATCH /api/accounts/users/{id}/role/ — change a user's role.

    Finds the user's membership in the current tenant and updates the role.
    Requires team.manage_roles permission.
    """

    queryset = Membership.objects.all()
    permission_classes = [IsAuthenticated, TenantAwarePermission, RolePermission]
    lookup_url_kwarg = "user_id"

    def get_required_permission(self) -> str | None:
        return "team.manage_roles"

    def get_object(self):
        user_id = self.kwargs.get(self.lookup_url_kwarg)
        return get_object_or_404(
            Membership,
            user_id=user_id,
            tenant_id=self.request.user.tenant_id,
            is_active=True,
        )

    def get_serializer_class(self):
        from apps.teams.views import MembershipSerializer
        return MembershipSerializer

    def perform_update(self, serializer):
        role_id = self.request.data.get("role_id") or self.request.data.get("role")
        if role_id:
            role = get_object_or_404(
                Role,
                id=role_id,
                tenant_id=self.request.user.tenant_id,
            )
            serializer.save(role=role)
        else:
            serializer.save()
