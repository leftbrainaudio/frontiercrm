"""Middleware for FrontierCRM — health check bypass + tenant injection."""

from __future__ import annotations

import json
import re

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken

from apps.teams.models import Tenant

# Patterns that skip tenant resolution
PUBLIC_PATHS = re.compile(r"^/(admin|api/auth|api/health|api/schema|api/docs|static|media)/")
# Health check paths — bypassed before host validation
HEALTH_PATHS = re.compile(r"^/api/health/")


class HealthCheckMiddleware(MiddlewareMixin):
    """Respond 200 to health checks before Django's SecurityMiddleware runs.

    Fly.io Consul health checks use internal IPs (e.g. 172.19.x.x) as the Host
    header, which Django's ALLOWED_HOSTS validation rejects. This middleware
    intercepts health check requests before SecurityMiddleware processes them,
    returning a lightweight 200 response without any database access.
    """

    def process_request(self, request: HttpRequest) -> HttpResponse | None:
        if HEALTH_PATHS.match(request.path_info):
            return HttpResponse(
                json.dumps({"status": "ok", "service": "frontiercrm-api"}).encode(),
                content_type="application/json",
                status=200,
            )
        return None


class TenantMiddleware(MiddlewareMixin):
    """Extract tenant context from JWT claims or subdomain and attach to request."""

    def process_request(self, request: HttpRequest) -> HttpResponse | None:
        """Attach tenant_id and tenant to the request if authenticated."""
        request.tenant_id = None  # type: ignore[attr-defined]
        request.tenant = None  # type: ignore[attr-defined]

        if PUBLIC_PATHS.match(request.path_info):
            return None

        # Extract from JWT token if present
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            try:
                token = AccessToken(auth_header.removeprefix("Bearer "))
                request.tenant_id = token.get("tenant_id")  # type: ignore[attr-defined]
            except Exception:
                pass

        # If no tenant from JWT, try subdomain (multi-tenant via domain)
        if not request.tenant_id:  # type: ignore[attr-defined]
            host = request.get_host().split(":")[0]
            if host and host != "localhost" and "." in host:
                # Map subdomain to tenant — only if user is authenticated
                if request.user.is_authenticated:
                    try:
                        tenant = Tenant.objects.filter(subdomain=host.split(".")[0]).first()
                        if tenant:
                            request.tenant_id = tenant.id  # type: ignore[attr-defined]
                            request.tenant = tenant  # type: ignore[attr-defined]
                    except Exception:
                        pass

        return None
