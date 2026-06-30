"""Authentication backends for email/password, magic link, and Google OAuth."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

UserModel = get_user_model()


class TwoFactorToken(AccessToken):
    """Short-lived JWT for the 2FA challenge step."""
    token_type = "2fa"
    lifetime = timezone.timedelta(minutes=5)

    @classmethod
    def for_user(cls, user) -> "TwoFactorToken":
        token = super().for_user(user)
        token["purpose"] = "2fa_challenge"
        token["user_id"] = str(user.id)
        if user.tenant_id:
            token["tenant_id"] = str(user.tenant_id)
        return token


class EmailPasswordBackend(BaseBackend):
    """Authenticate via email + password."""

    def authenticate(
        self,
        request: Any,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> UserModel | None:
        if email is None:
            return None
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password):
                user.last_activity_at = timezone.now()
                user.save(update_fields=["last_activity_at"])
                return user
        except UserModel.DoesNotExist:
            return None
        return None

    def get_user(self, user_id: str) -> UserModel | None:
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None


class MagicLinkBackend(BaseBackend):
    """Authenticate via magic link token."""

    def authenticate(
        self,
        request: Any,
        magic_link_token: str | None = None,
        **kwargs: Any,
    ) -> UserModel | None:
        if not magic_link_token:
            return None
        # Token is valid for 15 minutes
        cutoff = timezone.now() - timezone.timedelta(minutes=15)
        try:
            user = UserModel.objects.get(
                magic_link_token=magic_link_token,
                magic_link_created_at__gte=cutoff,
            )
            # Clear token after use
            user.magic_link_token = ""
            user.magic_link_created_at = None
            user.last_activity_at = timezone.now()
            user.save(update_fields=["magic_link_token", "magic_link_created_at", "last_activity_at"])
            return user
        except UserModel.DoesNotExist:
            return None

    def get_user(self, user_id: str) -> UserModel | None:
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
