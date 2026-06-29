"""Health check views for readiness and liveness probes."""

from __future__ import annotations

from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request: Request) -> Response:
    """Basic liveness check."""
    return Response({"status": "ok", "service": "frontiercrm-api"})


@api_view(["GET"])
@permission_classes([AllowAny])
def ready(request: Request) -> Response:
    """Readiness check — verifies DB connectivity."""
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    return Response(
        {
            "status": "ok" if db_ok else "degraded",
            "database": "connected" if db_ok else "unreachable",
        }
    )


urlpatterns = [
    path("", health, name="health"),
    path("ready/", ready, name="ready"),
]
