"""Main URL configuration for FrontierCRM."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.saml_views import (
    SamlProviderDetailView,
    SamlProviderListCreateView,
    saml_acs,
    saml_domain_check,
    saml_logout,
    saml_metadata,
    saml_sp_login,
)
from apps.accounts.two_factor_views import (
    two_factor_admin_reset,
    two_factor_confirm,
    two_factor_disable,
    two_factor_regenerate_codes,
    two_factor_setup,
    two_factor_status,
    two_factor_verify,
)
from apps.accounts.views import (
    SignupView,
    google_oauth_callback,
    google_oauth_init,
    login_view,
    magic_link_confirm,
    magic_link_request,
    social_auth_callback,
    social_auth_init,
)

api_patterns = [
    # Auth
    path("auth/signup/", SignupView.as_view(), name="auth-signup"),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/magic-link/request/", magic_link_request, name="auth-magic-link-request"),
    path("auth/magic-link/confirm/", magic_link_confirm, name="auth-magic-link-confirm"),
    path("auth/google/init/", google_oauth_init, name="auth-google-init"),
    path("auth/google/callback/", google_oauth_callback, name="auth-google-callback"),
    path("auth/social/", social_auth_callback, name="auth-social-callback"),
    path("auth/social/<str:provider>/init/", social_auth_init, name="auth-social-init"),
    # ── 2FA Routes ─────────────────────────────────────────────────
    path("auth/2fa/setup/", two_factor_setup, name="auth-2fa-setup"),
    path("auth/2fa/confirm/", two_factor_confirm, name="auth-2fa-confirm"),
    path("auth/2fa/verify/", two_factor_verify, name="auth-2fa-verify"),
    path("auth/2fa/disable/", two_factor_disable, name="auth-2fa-disable"),
    path("auth/2fa/status/", two_factor_status, name="auth-2fa-status"),
    path("auth/2fa/recovery-codes/regenerate/", two_factor_regenerate_codes, name="auth-2fa-regenerate"),
    path("auth/2fa/admin/reset/<uuid:user_id>/", two_factor_admin_reset, name="auth-2fa-admin-reset"),
    # ── SAML Routes ────────────────────────────────────────────────
    path("auth/saml/login/", saml_sp_login, name="auth-saml-login"),
    path("auth/saml/<uuid:tenant_id>/acs/", saml_acs, name="auth-saml-acs"),
    path("auth/saml/<uuid:tenant_id>/metadata/", saml_metadata, name="auth-saml-metadata"),
    path("auth/saml/domain-check/", saml_domain_check, name="auth-saml-domain-check"),
    path("auth/saml/logout/", saml_logout, name="auth-saml-logout"),
    path("auth/saml/providers/", SamlProviderListCreateView.as_view(), name="auth-saml-providers"),
    path("auth/saml/providers/<uuid:id>/", SamlProviderDetailView.as_view(), name="auth-saml-provider-detail"),
    # App endpoints
    path("accounts/", include("apps.accounts.urls")),
    path("contacts/", include("apps.contacts.urls")),
    path("deals/", include("apps.pipelines.urls")),
    path("activities/", include("apps.activities.urls")),
    path("emails/", include("apps.email.urls")),
    path("notes/", include("apps.notes.urls")),
    path("tasks/", include("apps.tasks.urls")),
    path("teams/", include("apps.teams.urls")),
    path("webhooks/", include("apps.webhooks.urls")),
    path("api-keys/", include("apps.apikeys.urls")),
    path("files/", include("apps.files.urls")),
    path("slack/", include("apps.slack.urls")),
    path("search/", include("apps.search.urls")),
    path("sync/", include("apps.sync.urls")),
    path("imports/", include("apps.imports.urls")),
    # Reports
    path("reports/", include("apps.reports.urls")),
    # Export
    path("export/", include("apps.export.urls")),
    # Health
    path("health/", include("apps.core.health_urls")),
    # Custom fields
    path("custom-fields/", include("apps.core.urls_api")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
    path("api/docs/", include("rest_framework.urls", namespace="rest_framework")),
    # OpenAPI / Swagger / ReDoc
    path("api/docs/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

# ── SPA catch-all: serve frontend for non-API routes ─────────────────────
from apps.core.views import spa_serve

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# SPA catch-all — must be last, after all API routes
urlpatterns += [
    path("assets/<path:path>", spa_serve, name="spa-assets"),
    path("favicon.svg", spa_serve, name="spa-favicon"),
    path("icons.svg", spa_serve, name="spa-icons"),
    re_path(r"^(?!api/|admin/|static/|media/).*$", spa_serve, name="spa-catch-all"),
]
