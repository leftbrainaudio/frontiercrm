"""Views for authentication — signup, login, magic link, Google OAuth."""

from __future__ import annotations

import secrets
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

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
    """Authenticate with email + password, return JWT tokens."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
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
