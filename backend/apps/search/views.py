"""Search API — full-text search via Meilisearch."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .service import SearchService


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def search_view(request: Request) -> Response:
    """Full-text search across indexed models."""
    query = request.data.get("q") if request.method == "POST" else request.GET.get("q", "")
    if not query:
        return Response({"error": "Search query 'q' is required"}, status=status.HTTP_400_BAD_REQUEST)

    model = request.data.get("model") if request.method == "POST" else request.GET.get("model", "")
    page = int(request.data.get("page", 1) if request.method == "POST" else request.GET.get("page", 1))
    hits_per_page = int(
        request.data.get("hits_per_page", 25) if request.method == "POST" else request.GET.get("hits_per_page", 25)
    )

    service = SearchService()
    tenant_filter = f"tenant_id = {request.user.tenant_id}"

    if model:
        # Single-model search
        results = service.search(
            model_name=model,
            query=query,
            filters=tenant_filter,
            page=page,
            hits_per_page=hits_per_page,
        )
        return Response(results)
    else:
        # Multi-model search
        models = ["contact", "deal", "account", "note"]
        results = service.multi_search(
            models=models,
            query=query,
            filters=tenant_filter,
            limit=hits_per_page,
        )
        return Response(results)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_health(request: Request) -> Response:
    """Check Meilisearch connectivity."""
    service = SearchService()
    healthy = service.health()
    return Response({"status": "ok" if healthy else "unavailable", "service": "meilisearch"})
