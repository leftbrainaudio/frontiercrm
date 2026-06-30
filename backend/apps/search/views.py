"""Search API — full-text search via Meilisearch and ORM fallback."""

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
    """Full-text search across indexed models via Meilisearch."""
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
        results = service.search(
            model_name=model,
            query=query,
            filters=tenant_filter,
            page=page,
            hits_per_page=hits_per_page,
        )
        return Response(results)
    else:
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def simple_search_view(request: Request) -> Response:
    """ORM-based global search — no Meilisearch dependency.

    Queries deals (name), contacts (name, email), accounts (name),
    notes (title, content), and email subjects.
    Returns grouped results with type indicators.
    """
    query = request.GET.get("q", "").strip()
    limit = min(int(request.GET.get("limit", 10)), 50)

    if not query:
        return Response({
            "results": [],
            "query": "",
            "total": 0,
        })

    from django.db.models import Q, Value
    from django.db.models.functions import Concat

    from apps.contacts.models import Account, Contact
    from apps.pipelines.models import Deal
    from apps.notes.models import Note
    from apps.email.models import EmailMessage

    tenant_id = request.user.tenant_id

    results: list[dict] = []

    # ── Contacts ──
    contacts = Contact.objects.filter(
        tenant_id=tenant_id,
        deleted_at__isnull=True,
    ).filter(
        Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
        | Q(email__icontains=query)
    ).annotate(
        _display=Concat("first_name", Value(" "), "last_name"),
    ).values("id", "_display", "email", "job_title")[:limit]

    for c in contacts:
        results.append({
            "id": str(c["id"]),
            "type": "contact",
            "title": c["_display"],
            "subtitle": c.get("email") or c.get("job_title") or "",
            "url": f"/contacts/{c['id']}",
        })

    # ── Deals ──
    deals = Deal.objects.filter(
        tenant_id=tenant_id,
        deleted_at__isnull=True,
    ).filter(
        Q(name__icontains=query)
        | Q(description__icontains=query)
    ).select_related("stage").values(
        "id", "name", "value", "stage__name"
    )[:limit]

    for d in deals:
        results.append({
            "id": str(d["id"]),
            "type": "deal",
            "title": d["name"],
            "subtitle": f"${float(d['value']):,.0f}" if d["value"] else "",
            "url": f"/pipeline",
        })

    # ── Accounts ──
    accounts = Account.objects.filter(
        tenant_id=tenant_id,
        deleted_at__isnull=True,
    ).filter(
        Q(name__icontains=query)
        | Q(domain__icontains=query)
    ).values("id", "name", "domain", "industry")[:limit]

    for a in accounts:
        results.append({
            "id": str(a["id"]),
            "type": "account",
            "title": a["name"],
            "subtitle": a.get("industry") or a.get("domain") or "",
            "url": f"/contacts",
        })

    # ── Notes ──
    notes = Note.objects.filter(
        tenant_id=tenant_id,
        deleted_at__isnull=True,
    ).filter(
        Q(title__icontains=query)
        | Q(content__icontains=query)
    ).values("id", "title", "entity_type")[:limit]

    for n in notes:
        results.append({
            "id": str(n["id"]),
            "type": "note",
            "title": n["title"][:80] or "Untitled note",
            "subtitle": n.get("entity_type", ""),
            "url": "",
        })

    # ── Emails (subjects) ──
    emails = EmailMessage.objects.filter(
        tenant_id=tenant_id,
    ).filter(
        Q(subject__icontains=query)
    ).values("id", "subject", "from_email", "snippet")[:limit]

    for e in emails:
        results.append({
            "id": str(e["id"]),
            "type": "email",
            "title": e["subject"][:80] or "(no subject)",
            "subtitle": e.get("from_email", ""),
            "url": "/email",
        })

    return Response({
        "results": results,
        "query": query,
        "total": len(results),
    })
