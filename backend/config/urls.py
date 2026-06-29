"""Main URL configuration for FrontierCRM."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework.schemas import get_schema_view
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    SignupView,
    google_oauth_callback,
    google_oauth_init,
    login_view,
    magic_link_confirm,
    magic_link_request,
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
    path("files/", include("apps.files.urls")),
    path("search/", include("apps.search.urls")),
    # Health
    path("health/", include("apps.core.health_urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
    path(
        "api/schema/",
        get_schema_view(
            title="FrontierCRM API",
            description="API for FrontierCRM — the modern CRM platform",
            version="1.0.0",
        ),
        name="openapi-schema",
    ),
    path("api/docs/", include("rest_framework.urls", namespace="rest_framework")),
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
