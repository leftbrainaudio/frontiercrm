"""Service-layer functions for pipeline operations — template creation, etc."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .models import Pipeline, Stage

# ── Pipeline Templates ────────────────────────────────────────────────────────

PIPELINE_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "sales": [
        {"name": "Lead", "display_order": 0, "probability": Decimal("0.10")},
        {"name": "Qualified", "display_order": 1, "probability": Decimal("0.25")},
        {"name": "Proposal", "display_order": 2, "probability": Decimal("0.50")},
        {"name": "Negotiation", "display_order": 3, "probability": Decimal("0.75")},
        {"name": "Closed Won", "display_order": 4, "probability": Decimal("1.00")},
    ],
    "saas": [
        {"name": "Trial", "display_order": 0, "probability": Decimal("0.10")},
        {"name": "Demo", "display_order": 1, "probability": Decimal("0.30")},
        {"name": "Negotiation", "display_order": 2, "probability": Decimal("0.60")},
        {"name": "Closed", "display_order": 3, "probability": Decimal("1.00")},
    ],
    "recruiting": [
        {"name": "Sourced", "display_order": 0, "probability": Decimal("0.05")},
        {"name": "Screening", "display_order": 1, "probability": Decimal("0.20")},
        {"name": "Interview", "display_order": 2, "probability": Decimal("0.50")},
        {"name": "Offer", "display_order": 3, "probability": Decimal("0.80")},
        {"name": "Hired", "display_order": 4, "probability": Decimal("1.00")},
    ],
    "custom": [
        {"name": "Lead", "display_order": 0, "probability": Decimal("0.10")},
        {"name": "Qualified", "display_order": 1, "probability": Decimal("0.50")},
        {"name": "Closed", "display_order": 2, "probability": Decimal("1.00")},
    ],
}


def create_pipeline_from_template(
    *,
    tenant_id: str,
    template_name: str,
) -> Pipeline | None:
    """Create a default pipeline from a named template.

    Idempotent — if the tenant already has a default pipeline it returns ``None``.
    Returns the created ``Pipeline`` instance (with stages) on success.
    """
    # Idempotency: skip if a default pipeline already exists
    if Pipeline.objects.filter(tenant_id=tenant_id, is_default=True).exists():
        return None

    stages_data = PIPELINE_TEMPLATES.get(template_name)
    if not stages_data:
        raise ValueError(f"Unknown pipeline template: {template_name!r}")

    template_labels = {
        "sales": "Sales",
        "saas": "SaaS Sales",
        "recruiting": "Recruitment",
        "custom": "Custom",
    }
    pipeline_name = f"{template_labels.get(template_name, template_name.title())} Pipeline"

    pipeline = Pipeline.objects.create(
        tenant_id=tenant_id,
        name=pipeline_name,
        description=f"Auto-created from {template_name} template",
        is_default=True,
    )

    for stage_data in stages_data:
        Stage.objects.create(
            tenant_id=tenant_id,
            pipeline=pipeline,
            **stage_data,
        )

    return pipeline
