from django.urls import path

from . import views
from .onboarding_views import (
    onboarding_progress,
    onboarding_reset,
    onboarding_status,
)
from .two_factor_views import (
    two_factor_admin_reset,
    two_factor_confirm,
    two_factor_disable,
    two_factor_regenerate_codes,
    two_factor_setup,
    two_factor_status,
    two_factor_verify,
)

urlpatterns = [
    path("me/", views.me_view, name="account-me"),
    path(
        "onboarding/status/",
        onboarding_status,
        name="onboarding-status",
    ),
    path(
        "onboarding/progress/",
        onboarding_progress,
        name="onboarding-progress",
    ),
    path(
        "onboarding/reset/",
        onboarding_reset,
        name="onboarding-reset",
    ),
    # ── RBAC ───────────────────────────────────────────────────
    path("roles/", views.RoleListCreateView.as_view(), name="account-roles-list"),
    path(
        "users/<uuid:user_id>/role/",
        views.UserRoleUpdateView.as_view(),
        name="account-user-role-update",
    ),
    # ── 2FA ─────────────────────────────────────────────────────
    path("2fa/setup/", two_factor_setup, name="2fa-setup"),
    path("2fa/confirm/", two_factor_confirm, name="2fa-confirm"),
    path("2fa/verify/", two_factor_verify, name="2fa-verify"),
    path("2fa/disable/", two_factor_disable, name="2fa-disable"),
    path("2fa/status/", two_factor_status, name="2fa-status"),
    path(
        "2fa/recovery-codes/regenerate/",
        two_factor_regenerate_codes,
        name="2fa-regenerate",
    ),
    path(
        "2fa/admin/reset/<uuid:user_id>/",
        two_factor_admin_reset,
        name="2fa-admin-reset",
    ),
]