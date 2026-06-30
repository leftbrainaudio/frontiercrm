"""Views for Two-Factor Authentication — setup, verify, disable, status, recovery."""

from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Any

import pyotp
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from apps.accounts.auth import TwoFactorToken
from apps.core.permissions import TenantAwarePermission

from .serializers import (
    TwoFactorConfirmSerializer,
    TwoFactorDisableSerializer,
    TwoFactorRegenerateSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
    UserSerializer,
)

UserModel = get_user_model()

# ── Helpers ───────────────────────────────────────────────────────────────────


def generate_recovery_codes(n: int = 10) -> tuple[list[str], list[str]]:
    """Generate n recovery codes. Returns (raw_codes, bcrypt_hashes_as_str)."""
    import bcrypt

    raw_codes: list[str] = []
    hashed_codes: list[str] = []
    for _ in range(n):
        code = f"{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
        raw_codes.append(code)
        hashed = bcrypt.hashpw(code.encode(), bcrypt.gensalt())
        hashed_codes.append(hashed.decode() if isinstance(hashed, bytes) else hashed)
    return raw_codes, hashed_codes


def verify_recovery_code(code: str, hashed_codes: list[str]) -> int | None:
    """Verify a recovery code. Returns its index or None."""
    import bcrypt

    for i, hashed in enumerate(hashed_codes):
        try:
            if bcrypt.checkpw(code.encode(), hashed.encode() if isinstance(hashed, str) else hashed):
                return i
        except Exception:
            continue
    return None


# ── Rate limiters ─────────────────────────────────────────────────────────────


class TwoFactorSetupThrottle(UserRateThrottle):
    rate = "3/hour"


class TwoFactorVerifyThrottle(AnonRateThrottle):
    rate = "5/minute"


class TwoFactorDisableThrottle(UserRateThrottle):
    rate = "3/hour"


class TwoFactorRegenerateThrottle(UserRateThrottle):
    rate = "3/day"


class SamlLoginThrottle(AnonRateThrottle):
    rate = "10/minute"


# ── Endpoints ─────────────────────────────────────────────────────────────────


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([TwoFactorSetupThrottle])
def two_factor_setup(request: Request) -> Response:
    """POST /api/auth/2fa/setup/ — Initialize 2FA setup.

    Generates a new TOTP secret and returns the provisioning URI.
    Does NOT enable 2FA yet — user must confirm with a valid code first.
    """
    user = request.user

    if user.totp_enabled:
        return Response(
            {"detail": "Two-factor authentication is already enabled."},
            status=status.HTTP_409_CONFLICT,
        )

    secret = pyotp.random_base32()
    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="FrontierCRM",
    )

    # Store the secret but don't enable yet
    user.totp_secret = secret
    user.save(update_fields=["totp_secret"])

    return Response(
        {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def two_factor_confirm(request: Request) -> Response:
    """POST /api/auth/2fa/confirm/ — Confirm and enable 2FA."""
    user = request.user
    serializer = TwoFactorConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if user.totp_enabled:
        return Response(
            {"detail": "Two-factor authentication is already enabled."},
            status=status.HTTP_409_CONFLICT,
        )

    if not user.totp_secret:
        return Response(
            {"detail": "No TOTP secret found. Call /api/auth/2fa/setup/ first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    code = serializer.validated_data["code"]
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code, valid_window=1):
        return Response(
            {"code": ["Invalid code. Please try again."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Generate recovery codes
    raw_codes, hashed_codes = generate_recovery_codes(10)

    # Enable 2FA
    user.totp_enabled = True
    user.totp_created_at = timezone.now()
    user.recovery_codes = hashed_codes
    user.save(update_fields=["totp_enabled", "totp_created_at", "recovery_codes"])

    return Response(
        {
            "detail": "Two-factor authentication enabled.",
            "recovery_codes": raw_codes,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([TwoFactorVerifyThrottle])
def two_factor_verify(request: Request) -> Response:
    """POST /api/auth/2fa/verify/ — Verify 2FA code during login.

    Accepts a 2fa_token + TOTP code (or recovery code).
    On success returns access + refresh JWT tokens.
    """
    serializer = TwoFactorVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    twofa_token_str = serializer.validated_data["two_factor_token"]
    code = serializer.validated_data["code"]
    is_recovery = serializer.validated_data.get("is_recovery", False)

    # Validate the 2fa_token
    try:
        from rest_framework_simplejwt.exceptions import TokenError
        from rest_framework_simplejwt.tokens import UntypedToken

        token = UntypedToken(twofa_token_str)
        if token.payload.get("purpose") != "2fa_challenge":
            return Response(
                {"detail": "Invalid token purpose."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_id = token.payload.get("user_id")
    except TokenError:
        return Response(
            {"detail": "Invalid or expired 2FA token."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = UserModel.objects.get(pk=user_id, is_active=True)
    except UserModel.DoesNotExist:
        return Response(
            {"detail": "User not found or inactive."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.totp_enabled:
        return Response(
            {"detail": "2FA is not enabled for this user."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    attempts_cache_key = f"2fa_attempts_{user_id}"
    attempts = getattr(request, "_django_cached_attempts", None)
    if attempts is None:
        from django.core.cache import cache
        attempts = cache.get(attempts_cache_key, 0)
    else:
        attempts = 0

    if attempts >= 5:
        return Response(
            {"detail": "Too many failed attempts. Please log in again."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    verified = False

    if is_recovery:
        idx = verify_recovery_code(code, user.recovery_codes)
        if idx is not None:
            verified = True
            # Remove used recovery code
            codes = list(user.recovery_codes)
            codes.pop(idx)
            user.recovery_codes = codes
            user.save(update_fields=["recovery_codes"])
    else:
        totp = pyotp.TOTP(user.totp_secret)
        verified = totp.verify(code, valid_window=1)

    if not verified:
        attempts += 1
        from django.core.cache import cache
        cache.set(attempts_cache_key, attempts, timedelta(minutes=5))
        remaining = max(0, 5 - attempts)
        resp_data: dict[str, Any] = {
            "code": ["Invalid code."],
            "attempts_remaining": remaining,
        }
        if remaining == 0:
            resp_data["detail"] = "Too many failed attempts. Please log in again."
        return Response(resp_data, status=status.HTTP_400_BAD_REQUEST)

    # Success — clear attempt counter
    from django.core.cache import cache
    cache.delete(attempts_cache_key)

    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    if user.tenant_id:
        refresh.access_token["tenant_id"] = str(user.tenant_id)

    resp = {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }

    if is_recovery:
        resp["remaining_codes"] = len(user.recovery_codes)

    return Response(resp)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([TwoFactorDisableThrottle])
def two_factor_disable(request: Request) -> Response:
    """POST /api/auth/2fa/disable/ — Disable 2FA with password + TOTP."""
    user = request.user
    serializer = TwoFactorDisableSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if not user.totp_enabled:
        return Response(
            {"detail": "Two-factor authentication is not enabled."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    password = serializer.validated_data["password"]
    if not user.check_password(password):
        return Response(
            {"password": ["Incorrect password."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    code = serializer.validated_data["code"]
    totp = pyotp.TOTP(user.totp_secret)
    code_valid = totp.verify(code, valid_window=1)

    if not code_valid:
        # Try as recovery code
        idx = verify_recovery_code(code, user.recovery_codes)
        code_valid = idx is not None

    if not code_valid:
        return Response(
            {"code": ["Invalid TOTP or recovery code."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Disable 2FA
    user.totp_enabled = False
    user.totp_secret = ""
    user.recovery_codes = []
    user.totp_created_at = None
    user.save(update_fields=["totp_enabled", "totp_secret", "recovery_codes", "totp_created_at"])

    return Response({"detail": "Two-factor authentication disabled."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def two_factor_status(request: Request) -> Response:
    """GET /api/auth/2fa/status/ — Check if 2FA is enabled/required."""
    user = request.user
    tenant_requires_2fa = False
    if user.tenant_id:
        from apps.teams.models import Tenant
        try:
            tenant = Tenant.objects.get(pk=user.tenant_id)
            tenant_requires_2fa = tenant.settings.get("require_2fa", False)
        except Tenant.DoesNotExist:
            pass

    return Response(
        {
            "totp_enabled": user.totp_enabled,
            "tenant_requires_2fa": tenant_requires_2fa,
            "has_recovery_codes": len(user.recovery_codes) > 0 if user.totp_enabled else False,
            "remaining_recovery_codes": len(user.recovery_codes) if user.totp_enabled else 0,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([TwoFactorRegenerateThrottle])
def two_factor_regenerate_codes(request: Request) -> Response:
    """POST /api/auth/2fa/recovery-codes/regenerate/ — New recovery codes."""
    user = request.user
    serializer = TwoFactorRegenerateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if not user.totp_enabled:
        return Response(
            {"detail": "Two-factor authentication is not enabled."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    code = serializer.validated_data["code"]
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code, valid_window=1):
        return Response(
            {"code": ["Invalid TOTP code."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    raw_codes, hashed_codes = generate_recovery_codes(10)
    user.recovery_codes = hashed_codes
    user.save(update_fields=["recovery_codes"])

    return Response({"recovery_codes": raw_codes})


# ── Admin endpoints ───────────────────────────────────────────────────────────


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def two_factor_admin_reset(request: Request, user_id: str) -> Response:
    """POST /api/auth/2fa/admin/reset/{user_id}/ — Admin reset another user's 2FA.

    Requires superuser or manage_team permission.
    """
    admin_user = request.user
    if not admin_user.is_superuser and not admin_user.has_permission("team.manage_team"):
        return Response(
            {"detail": "You do not have permission to reset 2FA."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        target_user = UserModel.objects.get(pk=user_id)
    except UserModel.DoesNotExist:
        return Response(
            {"detail": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    target_user.totp_enabled = False
    target_user.totp_secret = ""
    target_user.recovery_codes = []
    target_user.totp_created_at = None
    target_user.save(update_fields=["totp_enabled", "totp_secret", "recovery_codes", "totp_created_at"])

    # Log activity
    from apps.activities.models import Activity
    Activity.objects.create(
        tenant_id=target_user.tenant_id or admin_user.tenant_id,
        activity_type="system",
        title=f"2FA reset for {target_user.email} by {admin_user.email}",
        actor_id=admin_user.id,
    )

    return Response({"detail": f"Two-factor authentication reset for {target_user.email}."})
