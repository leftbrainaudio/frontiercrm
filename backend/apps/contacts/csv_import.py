"""
CSV import utilities for contacts and deals.

Each import function:
  1. Parses a CSV file (uploaded as InMemoryUploadedFile).
  2. Maps columns based on a user-provided mapping dict.
  3. Handles conflict detection (preview mode) and conflict resolution (import mode).

Columns → Model field mapping for contacts:
  first_name, last_name, email, phone, mobile, job_title, department,
  street, city, state, postal_code, country, source, tags, account_name

Columns → Model field mapping for deals:
  name, value, currency, status, description, tags,
  contact_email, account_name, stage_name, pipeline_name,
  expected_close_date, close_reason
"""

from __future__ import annotations

import csv
import io
from decimal import Decimal
from typing import Any

# NOTE: model imports are Lazy (inside functions) so this module can be
# imported at Django startup without circular / premature app registry issues.

# -- Helpers -------------------------------------------------------------------

CONTACT_FIELDS = {
    "first_name", "last_name", "email", "phone", "mobile",
    "job_title", "department", "street", "city", "state",
    "postal_code", "country", "source", "tags",
}

DEAL_FIELDS = {
    "name", "value", "currency", "status", "description",
    "tags", "expected_close_date", "close_reason",
}


def _parse_csv(file_content: str) -> tuple[list[str], list[dict[str, str]]]:
    """Parse CSV content into headers and row dicts."""
    reader = csv.DictReader(io.StringIO(file_content))
    headers: list[str] = list(reader.fieldnames or [])
    rows: list[dict[str, str]] = list(reader)
    return headers, rows


def _resolve_tags(tag_str: str) -> list[str]:
    """Parse comma/semicolon-separated tags into a list."""
    if not tag_str:
        return []
    import re
    return [t.strip() for t in re.split(r"[;,|]", tag_str) if t.strip()]


# -- Contact Import ------------------------------------------------------------


class ContactImportResult:
    """Result of a contact CSV import operation."""

    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []
        self.updated: list[dict[str, Any]] = []
        self.skipped: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.total_rows = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
            "total_rows": self.total_rows,
            "created_count": len(self.created),
            "updated_count": len(self.updated),
            "skipped_count": len(self.skipped),
            "error_count": len(self.errors),
        }


def import_contacts_csv(
    tenant_id: str,
    file_content: str,
    column_mapping: dict[str, str] | None = None,
    *,
    dry_run: bool = False,
    update_existing: bool = False,
    skip_errors: bool = True,
) -> ContactImportResult:
    """
    Import contacts from a CSV string.

    column_mapping maps CSV column names -> model field names.
    If None, uses the CSV headers directly as field names.

    Conflict detection is by email (case-insensitive).
    """
    # Lazy imports
    from apps.contacts.models import Account, Contact

    headers, rows = _parse_csv(file_content)
    result = ContactImportResult()
    result.total_rows = len(rows)

    # Build field mapping
    if column_mapping:
        field_map = column_mapping
    else:
        field_map = {h: h for h in headers}

    # Pre-fetch existing accounts
    existing_accounts = {
        a.name.lower(): a
        for a in Account.objects.filter(tenant_id=tenant_id).only("id", "name")
    }

    created: list[dict[str, Any]] = []
    updated: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for idx, row in enumerate(rows, start=2):
        entry: dict[str, Any] = {"row": idx, "data": dict(row)}

        try:
            # Map row data to model fields
            model_data: dict[str, Any] = {}
            for csv_col, val in row.items():
                field_name = field_map.get(csv_col, csv_col)
                if field_name in CONTACT_FIELDS or field_name == "account_name":
                    model_data[field_name] = val.strip() if val else ""

            # Validate required
            email = model_data.get("email", "")
            first_name = model_data.get("first_name", "")
            last_name = model_data.get("last_name", "")

            if not email and not (first_name and last_name):
                entry["reason"] = "Missing required: email or first_name+last_name"
                errors.append(entry)
                if not skip_errors:
                    break
                continue

            # Resolve account
            account_name = model_data.pop("account_name", "")
            account = None
            if account_name:
                key = account_name.strip().lower()
                if key in existing_accounts:
                    account = existing_accounts[key]
                else:
                    account = Account.objects.create(
                        tenant_id=tenant_id,
                        name=account_name.strip(),
                    )
                    existing_accounts[key] = account

            # Handle tags
            if "tags" in model_data and isinstance(model_data["tags"], str):
                model_data["tags"] = _resolve_tags(model_data["tags"])

            # Trim to model fields
            contact_kwargs: dict[str, Any] = {
                k: v for k, v in model_data.items()
                if k in CONTACT_FIELDS
            }
            contact_kwargs["tenant_id"] = tenant_id
            if account:
                contact_kwargs["account"] = account

            # Conflict detection by email
            if email:
                existing = Contact.objects.filter(
                    tenant_id=tenant_id,
                    email__iexact=email,
                ).first()
            else:
                existing = Contact.objects.filter(
                    tenant_id=tenant_id,
                    first_name__iexact=first_name,
                    last_name__iexact=last_name,
                ).first()

            if existing:
                if update_existing:
                    if not dry_run:
                        for k, v in contact_kwargs.items():
                            if v:
                                setattr(existing, k, v)
                        existing.save()
                    updated.append(entry)
                else:
                    entry["reason"] = "Existing contact found"
                    skipped.append(entry)
            else:
                if not dry_run:
                    Contact.objects.create(**contact_kwargs)
                created.append(entry)

        except Exception as exc:
            entry["reason"] = str(exc)
            errors.append(entry)
            if not skip_errors:
                break

    result.created = created
    result.updated = updated
    result.skipped = skipped
    result.errors = errors
    return result


# -- Deal Import ---------------------------------------------------------------


class DealImportResult:
    """Result of a deal CSV import operation."""

    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []
        self.updated: list[dict[str, Any]] = []
        self.skipped: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.total_rows = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
            "total_rows": self.total_rows,
            "created_count": len(self.created),
            "updated_count": len(self.updated),
            "skipped_count": len(self.skipped),
            "error_count": len(self.errors),
        }


def import_deals_csv(
    tenant_id: str,
    file_content: str,
    column_mapping: dict[str, str] | None = None,
    *,
    dry_run: bool = False,
    update_existing: bool = False,
    skip_errors: bool = True,
) -> DealImportResult:
    """
    Import deals from a CSV string.

    column_mapping maps CSV column names -> model field names.
    If None, uses the CSV headers directly as field names.

    Conflicts are detected by deal name (case-insensitive) within the same pipeline.
    """
    from apps.pipelines.models import Deal, Pipeline, Stage
    from apps.contacts.models import Account, Contact

    headers, rows = _parse_csv(file_content)
    result = DealImportResult()
    result.total_rows = len(rows)

    # Build field mapping
    if column_mapping:
        field_map = column_mapping
    else:
        field_map = {h: h for h in headers}

    # Pre-fetch pipelines and stages
    pipelines = {
        p.name.lower(): p
        for p in Pipeline.objects.filter(tenant_id=tenant_id, deleted_at__isnull=True)
        .prefetch_related("stages")
    }

    created: list[dict[str, Any]] = []
    updated: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for idx, row in enumerate(rows, start=2):
        entry: dict[str, Any] = {"row": idx, "data": dict(row)}

        try:
            # Map row data to model fields
            model_data: dict[str, Any] = {}
            for csv_col, val in row.items():
                field_name = field_map.get(csv_col, csv_col)
                model_data[field_name] = val.strip() if val else ""

            deal_name = model_data.get("name", "").strip()
            if not deal_name:
                entry["reason"] = "Missing required: name"
                errors.append(entry)
                if not skip_errors:
                    break
                continue

            # Resolve pipeline
            pipeline_name = model_data.pop("pipeline_name", "")
            stage_name = model_data.pop("stage_name", "")
            contact_email = model_data.pop("contact_email", "")
            account_name = model_data.pop("account_name", "")

            pipeline_lower = pipeline_name.strip().lower()
            pipeline = pipelines.get(pipeline_lower)
            if not pipeline:
                entry["reason"] = f"Pipeline '{pipeline_name}' not found"
                errors.append(entry)
                if not skip_errors:
                    break
                continue

            # Resolve stage
            stage = None
            if stage_name:
                stage = pipeline.stages.filter(
                    name__iexact=stage_name.strip()
                ).first()
            if not stage:
                stage = pipeline.stages.order_by("display_order").first()
            if not stage:
                entry["reason"] = f"No stages found in pipeline '{pipeline_name}'"
                errors.append(entry)
                if not skip_errors:
                    break
                continue

            # Resolve account
            account = None
            if account_name:
                account = Account.objects.filter(
                    tenant_id=tenant_id,
                    name__iexact=account_name.strip(),
                ).first()

            # Resolve contact
            contact = None
            if contact_email:
                contact = Contact.objects.filter(
                    tenant_id=tenant_id,
                    email__iexact=contact_email.strip(),
                ).first()

            # Build deal kwargs
            deal_kwargs: dict[str, Any] = {
                "tenant_id": tenant_id,
                "pipeline": pipeline,
                "stage": stage,
            }

            if account:
                deal_kwargs["account"] = account
            if contact:
                deal_kwargs["contact"] = contact

            for field in DEAL_FIELDS:
                val = model_data.get(field, "")
                if val:
                    if field == "value":
                        try:
                            deal_kwargs["value"] = Decimal(str(val))
                        except Exception:
                            deal_kwargs["value"] = Decimal("0.00")
                    elif field == "tags":
                        deal_kwargs["tags"] = _resolve_tags(val)
                    else:
                        deal_kwargs[field] = val

            # Conflict detection by name within pipeline
            existing = Deal.objects.filter(
                tenant_id=tenant_id,
                pipeline=pipeline,
                name__iexact=deal_name,
            ).first()

            if existing:
                if update_existing:
                    if not dry_run:
                        for k, v in deal_kwargs.items():
                            if v not in (None, "", 0) and k not in ("tenant_id",):
                                setattr(existing, k, v)
                        existing.save()
                    updated.append(entry)
                else:
                    entry["reason"] = f"Existing deal in pipeline '{pipeline.name}'"
                    skipped.append(entry)
            else:
                if not dry_run:
                    Deal.objects.create(**deal_kwargs)
                created.append(entry)

        except Exception as exc:
            entry["reason"] = str(exc)
            errors.append(entry)
            if not skip_errors:
                break

    result.created = created
    result.updated = updated
    result.skipped = skipped
    result.errors = errors
    return result
