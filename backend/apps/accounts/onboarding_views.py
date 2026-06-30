"""Views for onboarding flow — status, progress, and reset."""

from __future__ import annotations

from typing import Any

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.pipelines.services import create_pipeline_from_template
from apps.teams.models import Tenant


def _build_status_response(user: Any, tenant: Tenant) -> dict[str, Any]:
    """Return the standard onboarding status payload."""
    settings = tenant.settings or {}
    onboarding = settings.get("onboarding", {})
    return {
        "is_onboarded": user.is_onboarded,
        "company_done": onboarding.get("company_done", False),
        "invite_done": onboarding.get("invite_done", False),
        "import_done": onboarding.get("import_done", False),
        "email_done": onboarding.get("email_done", False),
        "pipeline_done": onboarding.get("pipeline_done", False),
        "skipped_steps": onboarding.get("skipped_steps", []),
        "tenant": {
            "name": tenant.name,
            "logo_url": tenant.logo_url,
            "industry": tenant.industry,
        },
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def onboarding_status(request: Request) -> Response:
    """Return current onboarding progress for the user's tenant."""
    tenant = Tenant.objects.get(id=request.user.tenant_id)
    return Response(_build_status_response(request.user, tenant))


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def onboarding_progress(request: Request) -> Response:
    """Update onboarding progress for one or more steps."""
    tenant = Tenant.objects.get(id=request.user.tenant_id)
    settings = dict(tenant.settings or {})
    onboarding = dict(settings.get("onboarding", {}))

    data: dict[str, Any] = request.data

    # Handle company setup
    if "company" in data:
        company = data["company"]
        changed = []
        if "name" in company:
            tenant.name = company["name"]
            changed.append("name")
        if "logo_url" in company:
            tenant.logo_url = company["logo_url"]
            changed.append("logo_url")
        if "industry" in company:
            tenant.industry = company["industry"]
            changed.append("industry")
        if changed:
            tenant.save(update_fields=changed)

    # Handle pipeline template (idempotent — skips if already has default pipeline)
    # MUST run BEFORE the step-booleans loop so `pipeline_done` doesn't short-circuit it.
    if "pipeline_template" in data and not onboarding.get("pipeline_done"):
        try:
            create_pipeline_from_template(
                tenant_id=tenant.id,
                template_name=data["pipeline_template"],
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        onboarding["pipeline_done"] = True

    # Handle step completion booleans
    for step_key in ["company_done", "invite_done", "import_done", "email_done", "pipeline_done"]:
        if step_key in data:
            onboarding[step_key] = data[step_key]

    # Handle skip
    if "skip_step" in data:
        step_key = f"{data['skip_step']}_done"
        onboarding[step_key] = True
        skipped = onboarding.get("skipped_steps", [])
        if data["skip_step"] not in skipped:
            onboarding.setdefault("skipped_steps", []).append(data["skip_step"])

    # Persist onboarding settings
    settings["onboarding"] = onboarding
    tenant.settings = settings
    tenant.save(update_fields=["settings"])

    # Handle mark_complete (after persistence so incomplete steps get auto-skipped)
    if data.get("mark_complete"):
        request.user.is_onboarded = True
        request.user.onboarded_at = timezone.now()
        request.user.save(update_fields=["is_onboarded", "onboarded_at"])
        # Auto-skip any incomplete steps
        for step_key in ["company_done", "invite_done", "import_done", "email_done", "pipeline_done"]:
            if not onboarding.get(step_key):
                onboarding[step_key] = True
        settings["onboarding"] = onboarding
        tenant.settings = settings
        tenant.save(update_fields=["settings"])

    return Response(_build_status_response(request.user, tenant))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def onboarding_reset(request: Request) -> Response:
    """Reset onboarding so the wizard can be re-run."""
    tenant = Tenant.objects.get(id=request.user.tenant_id)
    settings = tenant.settings or {}
    settings.pop("onboarding", None)
    tenant.settings = settings
    tenant.save(update_fields=["settings"])

    request.user.is_onboarded = False
    request.user.onboarded_at = None
    request.user.save(update_fields=["is_onboarded", "onboarded_at"])

    return Response({"status": "reset"})