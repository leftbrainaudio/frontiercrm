"""
CSV import utilities for contacts, deals, and accounts.

Each import function:
  1. Parses a CSV file (passed as a string).
  2. Maps columns based on a user-provided mapping dict.
  3. Handles conflict detection (preview mode) and conflict resolution (import mode).

Columns → Model field mapping for contacts:
  first_name, last_name, email, phone, mobile, job_title, department,
  street, city, state, postal_code, country, source, tags, account_name

Columns → Model field mapping for deals:
  name, value, currency, status, description, tags,
  contact_email, account_name, stage_name, pipeline_name,
  expected_close_date, close_reason

Columns → Model field mapping for accounts:
  name, domain, industry, description, website, phone,
  address_line1, address_line2, city, state, postcode, country,
  employees, annual_revenue, logo_url
"""

from __future__ import annotations

import csv
import io
from decimal import Decimal
from typing import Any

# NOTE: model imports are Lazy (inside functions) so this module can be
# imported at Django startup without circular / premature app registry issues.

# -- Field sets (exported for use by views) ------------------------------------

CONTACT_FIELDS = {
    "first_name", "last_name", "email", "phone", "mobile",
    "job_title", "department", "street", "city", "state",
    "postal_code", "country", "source", "tags",
}

DEAL_FIELDS = {
    "name", "value", "currency", "status", "description",
    "tags", "expected_close_date", "close_reason",
}

ACCOUNT_FIELDS = {
    "name", "domain", "industry", "description", "website",
    "phone", "address_line1", "address_line2", "city",
    "state", "postal_code", "country", "employees_count",
    "annual_revenue", "logo_url",
}

DEFAULT_DEDUP_KEYS = {
    "contact": "email",
    "deal": "name",
    "account": "name",
}

MAX_ROWS_DEFAULT = 10_000

# -- Auto-detect column mapping ------------------------------------------------

CONTACT_ALIASES = {
    "first name": "first_name",
    "firstname": "first_name",
    "given name": "first_name",
    "givenname": "first_name",
    "last name": "last_name",
    "lastname": "last_name",
    "surname": "last_name",
    "last_name": "last_name",
    "family name": "last_name",
    "email address": "email",
    "e-mail": "email",
    "emailaddress": "email",
    "mobile phone": "mobile",
    "cell": "mobile",
    "work phone": "phone",
    "telephone": "phone",
    "job title": "job_title",
    "jobtitle": "job_title",
    "title": "job_title",
    "position": "job_title",
    "company": "account_name",
    "organization": "account_name",
    "organisation": "account_name",
    "account name": "account_name",
    "account_name": "account_name",
    "zip code": "postal_code",
    "zipcode": "postal_code",
    "zip": "postal_code",
    "post code": "postal_code",
    "postcode": "postal_code",
    "street address": "street",
    "address": "street",
    "country code": "country",
}

DEAL_ALIASES = {
    "deal name": "name",
    "dealname": "name",
    "deal_value": "value",
    "deal value": "value",
    "amount": "value",
    "deal stage": "stage_name",
    "stage": "stage_name",
    "deal stage name": "stage_name",
    "pipeline": "pipeline_name",
    "pipeline name": "pipeline_name",
    "pipeline_name": "pipeline_name",
    "contact email": "contact_email",
    "contact_email": "contact_email",
    "contact e-mail": "contact_email",
    "account": "account_name",
    "organization": "account_name",
    "company": "account_name",
    "expected close": "expected_close_date",
    "expected close date": "expected_close_date",
    "close date": "expected_close_date",
    "close_date": "expected_close_date",
    "close reason": "close_reason",
    "close_reason": "close_reason",
    **{k: v for k, v in CONTACT_ALIASES.items()
       if v not in ("first_name", "last_name", "email", "mobile",
                    "phone", "job_title", "department", "city",
                    "state", "postal_code", "country", "account_name")},
}

ACCOUNT_ALIASES = {
    "account name": "name",
    "account_name": "name",
    "organization": "name",
    "company": "name",
    "website": "domain",  # many CSV call the domain field "website"
    "domain name": "domain",
    "domainname": "domain",
    "industry": "industry",
    "description": "description",
    "phone": "phone",
    "address": "address_line1",
    "address line 1": "address_line1",
    "address_line1": "address_line1",
    "address line 2": "address_line2",
    "address_line2": "address_line2",
    "city": "city",
    "state": "state",
    "state/province": "state",
    "zip code": "postal_code",
    "zipcode": "postal_code",
    "zip": "postal_code",
    "post code": "postal_code",
    "postcode": "postal_code",
    "country": "country",
    "employees": "employees_count",
    "employee count": "employees_count",
    "employees_count": "employees_count",
    "number of employees": "employees_count",
    "annual revenue": "annual_revenue",
    "annual_revenue": "annual_revenue",
    "revenue": "annual_revenue",
    "logo url": "logo_url",
    "logo_url": "logo_url",
    "logo": "logo_url",
}

ENTITY_ALIASES = {
    "contact": CONTACT_ALIASES,
    "deal": DEAL_ALIASES,
    "account": ACCOUNT_ALIASES,
}


def auto_detect_mapping(
    headers: list[str], entity_type: str
) -> dict[str, str]:
    """
    Try to match CSV column names to model fields.

    Uses direct match, case-insensitive match, and fuzzy match
    via a known alias dictionary for the given entity_type.

    Returns a dict {csv_header: model_field}.
    """
    aliases = ENTITY_ALIASES.get(entity_type, {})
    mapping: dict[str, str] = {}

    for header in headers:
        stripped = header.strip()
        # Direct (exact) match — header is already a model field name
        if entity_type == "contact" and stripped in CONTACT_FIELDS:
            mapping[header] = stripped
            continue
        if entity_type == "deal" and stripped in DEAL_FIELDS:
            mapping[header] = stripped
            continue
        if entity_type == "account" and stripped in ACCOUNT_FIELDS:
            mapping[header] = stripped
            continue

        # Alias lookup (lowercased)
        lower = stripped.lower()
        if lower in aliases:
            mapping[header] = aliases[lower]
            continue

        # Direct pass-through: use header as-is (user probably named
        # the column exactly after a model field with different casing)
        mapping[header] = stripped

    return mapping


# -- Helpers -------------------------------------------------------------------


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


def _validate_entity_type(entity_type: str) -> None:
    """Raise ValueError if entity_type is unsupported."""
    valid = {"contact", "deal", "account"}
    if entity_type not in valid:
        raise ValueError(
            f"Unsupported entity_type '{entity_type}'. "
            f"Must be one of: {', '.join(sorted(valid))}"
        )


# -- Generic import runner (single implementation) -----------------------------

# The three result classes share the same structure; we keep them for
# backward compatibility but share a single implementation internally.


class ImportResultBase:
    """Shared result container for all entity types."""

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


class ContactImportResult(ImportResultBase):
    """Result of a contact CSV import operation."""
    pass


class DealImportResult(ImportResultBase):
    """Result of a deal CSV import operation."""
    pass


class AccountImportResult(ImportResultBase):
    """Result of an account CSV import operation."""
    pass


_RESULT_CLASSES = {
    "contact": ContactImportResult,
    "deal": DealImportResult,
    "account": AccountImportResult,
}


def _build_field_map(
    headers: list[str],
    column_mapping: dict[str, str] | None,
) -> dict[str, str]:
    """Build a {csv_column: model_field} map."""
    if column_mapping:
        return dict(column_mapping)
    return {h: h for h in headers}


def _get_dedup_value(
    row: dict[str, str], dedup_key: str
) -> str:
    """Return the dedup value from a row, or empty string."""
    return row.get(dedup_key, "").strip()


def _apply_update(instance: Any, kwargs: dict[str, Any],
                  strategy: str) -> Any:
    """
    Apply fields to an existing instance based on conflict strategy.

    'skip': do nothing (instance left unchanged)
    'update': only set non-empty fields (safe merge)
    'overwrite': set all fields including empty/None
    """
    if strategy == "skip":
        return instance

    changed = False
    for k, v in kwargs.items():
        if k in ("tenant_id",):
            continue
        if strategy == "overwrite":
            setattr(instance, k, v)
            changed = True
        elif strategy == "update" and v not in (None, "", [], {}):
            setattr(instance, k, v)
            changed = True

    if changed:
        instance.save()
    return instance


def import_entities_csv(
    entity_type: str,
    tenant_id: str,
    file_content: str,
    column_mapping: dict[str, str] | None = None,
    *,
    dry_run: bool = False,
    dedup_key: str | None = None,
    conflict_strategy: str = "skip",
    skip_errors: bool = True,
    max_rows: int = MAX_ROWS_DEFAULT,
) -> ImportResultBase:
    """
    Generic CSV import for any entity type (contact, deal, account).

    Parameters
    ----------
    entity_type : str
        One of 'contact', 'deal', 'account'.
    tenant_id : str
        UUID of the tenant.
    file_content : str
        Raw CSV file content as a string.
    column_mapping : dict[str, str] | None
        Maps CSV column names → model field names.
        If None, uses CSV headers directly.
    dry_run : bool
        If True, no database writes are performed.
    dedup_key : str | None
        Field to use for duplicate detection. Falls back to
        entity-specific default (email for contact, name for deal/account).
    conflict_strategy : str
        'skip' (default) — leave existing records unchanged.
        'update' — update existing records, only non-empty fields.
        'overwrite' — overwrite existing records, all fields.
    skip_errors : bool
        If True, skip rows that cause errors and continue.
        If False, stop on the first error.
    max_rows : int
        Maximum number of rows to process (default: 10_000).
    """
    _validate_entity_type(entity_type)
    result_cls = _RESULT_CLASSES[entity_type]
    result = result_cls()

    headers, rows = _parse_csv(file_content)
    result.total_rows = min(len(rows), max_rows)
    rows = rows[:max_rows]

    field_map = _build_field_map(headers, column_mapping)

    resolved_dedup_key = dedup_key or DEFAULT_DEDUP_KEYS.get(entity_type, "name")
    created: list[dict[str, Any]] = []
    updated: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    # ── Resolve entity-specific kwargs ────────────────────────────────────

    if entity_type == "contact":
        created, updated, skipped, errors = _import_contacts(
            rows, field_map, tenant_id, resolved_dedup_key,
            conflict_strategy, dry_run, skip_errors,
        )
    elif entity_type == "deal":
        created, updated, skipped, errors = _import_deals(
            rows, field_map, tenant_id, resolved_dedup_key,
            conflict_strategy, dry_run, skip_errors,
        )
    elif entity_type == "account":
        created, updated, skipped, errors = _import_accounts(
            rows, field_map, tenant_id, resolved_dedup_key,
            conflict_strategy, dry_run, skip_errors,
        )

    result.created = created
    result.updated = updated
    result.skipped = skipped
    result.errors = errors
    return result


# ── Contact import ────────────────────────────────────────────────────────────


def _import_contacts(rows, field_map, tenant_id, dedup_key,
                     conflict_strategy, dry_run, skip_errors):
    """Internal contact import logic shared by preview and confirm."""
    from apps.contacts.models import Account, Contact

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

            # Build contact kwargs
            contact_kwargs: dict[str, Any] = {
                k: v for k, v in model_data.items()
                if k in CONTACT_FIELDS
            }
            contact_kwargs["tenant_id"] = tenant_id
            if account:
                contact_kwargs["account"] = account

            # Conflict detection
            dedup_value = _get_dedup_value(row, dedup_key)
            existing = None
            if dedup_value:
                filter_kwargs = {
                    "tenant_id": tenant_id,
                    f"{dedup_key}__iexact": dedup_value,
                }
                existing = Contact.objects.filter(**filter_kwargs).first()
            elif email and dedup_key != "email":
                # Fallback to email if dedup_value was empty
                existing = Contact.objects.filter(
                    tenant_id=tenant_id, email__iexact=email,
                ).first()
            elif first_name and last_name:
                existing = Contact.objects.filter(
                    tenant_id=tenant_id,
                    first_name__iexact=first_name,
                    last_name__iexact=last_name,
                ).first()

            if existing:
                if conflict_strategy == "skip":
                    entry["reason"] = "Existing contact found"
                    skipped.append(entry)
                else:
                    if not dry_run:
                        _apply_update(existing, contact_kwargs, conflict_strategy)
                    updated.append(entry)
            else:
                if not dry_run:
                    Contact.objects.create(**contact_kwargs)
                created.append(entry)

        except Exception as exc:
            entry["reason"] = str(exc)
            errors.append(entry)
            if not skip_errors:
                break

    return created, updated, skipped, errors


# ── Deal import ───────────────────────────────────────────────────────────────


def _import_deals(rows, field_map, tenant_id, dedup_key,
                  conflict_strategy, dry_run, skip_errors):
    """Internal deal import logic shared by preview and confirm."""
    from apps.pipelines.models import Deal, Pipeline, Stage
    from apps.contacts.models import Account, Contact

    # Pre-fetch pipelines
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

            # Conflict detection by dedup_key within pipeline
            dedup_value = _get_dedup_value(row, dedup_key)
            existing = None
            if dedup_value:
                filter_kwargs = {
                    "tenant_id": tenant_id,
                    "pipeline": pipeline,
                    f"{dedup_key}__iexact": dedup_value,
                }
                existing = Deal.objects.filter(**filter_kwargs).first()

            if existing:
                if conflict_strategy == "skip":
                    entry["reason"] = f"Existing deal in pipeline '{pipeline.name}'"
                    skipped.append(entry)
                else:
                    if not dry_run:
                        _apply_update(existing, deal_kwargs, conflict_strategy)
                    updated.append(entry)
            else:
                if not dry_run:
                    Deal.objects.create(**deal_kwargs)
                created.append(entry)

        except Exception as exc:
            entry["reason"] = str(exc)
            errors.append(entry)
            if not skip_errors:
                break

    return created, updated, skipped, errors


# ── Account import ────────────────────────────────────────────────────────────


def _import_accounts(rows, field_map, tenant_id, dedup_key,
                     conflict_strategy, dry_run, skip_errors):
    """Internal account import logic shared by preview and confirm."""
    from apps.contacts.models import Account

    created: list[dict[str, Any]] = []
    updated: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for idx, row in enumerate(rows, start=2):
        entry: dict[str, Any] = {"row": idx, "data": dict(row)}

        try:
            model_data: dict[str, Any] = {}
            for csv_col, val in row.items():
                field_name = field_map.get(csv_col, csv_col)
                if field_name in ACCOUNT_FIELDS:
                    model_data[field_name] = val.strip() if val else ""

            name = model_data.get("name", "").strip()
            if not name:
                entry["reason"] = "Missing required: name"
                errors.append(entry)
                if not skip_errors:
                    break
                continue

            # Build account kwargs
            account_kwargs: dict[str, Any] = {
                k: v for k, v in model_data.items()
                if k in ACCOUNT_FIELDS
            }
            account_kwargs["tenant_id"] = tenant_id

            # Handle numeric fields
            if "employees_count" in account_kwargs:
                try:
                    v = account_kwargs["employees_count"]
                    account_kwargs["employees_count"] = int(v) if v else None
                except (ValueError, TypeError):
                    account_kwargs["employees_count"] = None

            if "annual_revenue" in account_kwargs:
                try:
                    v = account_kwargs["annual_revenue"]
                    account_kwargs["annual_revenue"] = Decimal(str(v)) if v else None
                except Exception:
                    account_kwargs["annual_revenue"] = None

            # Conflict detection by dedup_key
            dedup_value = _get_dedup_value(row, dedup_key)
            existing = None
            if dedup_value:
                filter_kwargs = {
                    "tenant_id": tenant_id,
                    f"{dedup_key}__iexact": dedup_value,
                }
                existing = Account.objects.filter(**filter_kwargs).first()

            if existing:
                if conflict_strategy == "skip":
                    entry["reason"] = "Existing account found"
                    skipped.append(entry)
                else:
                    if not dry_run:
                        _apply_update(existing, account_kwargs, conflict_strategy)
                    updated.append(entry)
            else:
                if not dry_run:
                    Account.objects.create(**account_kwargs)
                created.append(entry)

        except Exception as exc:
            entry["reason"] = str(exc)
            errors.append(entry)
            if not skip_errors:
                break

    return created, updated, skipped, errors


# ── Public API (backward-compatible wrappers) ────────────────────────────────


def import_contacts_csv(
    tenant_id: str,
    file_content: str,
    column_mapping: dict[str, str] | None = None,
    *,
    dry_run: bool = False,
    update_existing: bool = False,
    skip_errors: bool = True,
    dedup_key: str | None = None,
    conflict_strategy: str | None = None,
    max_rows: int = MAX_ROWS_DEFAULT,
) -> ContactImportResult:
    """
    Import contacts from a CSV string.

    Backward-compatible: accepts the old ``update_existing`` boolean.
    When both ``update_existing`` and ``conflict_strategy`` are provided,
    ``conflict_strategy`` wins.
    """
    if conflict_strategy is None:
        conflict_strategy = "update" if update_existing else "skip"
    return import_entities_csv(
        "contact", tenant_id, file_content,
        column_mapping=column_mapping,
        dry_run=dry_run,
        dedup_key=dedup_key,
        conflict_strategy=conflict_strategy,
        skip_errors=skip_errors,
        max_rows=max_rows,
    )


def import_deals_csv(
    tenant_id: str,
    file_content: str,
    column_mapping: dict[str, str] | None = None,
    *,
    dry_run: bool = False,
    update_existing: bool = False,
    skip_errors: bool = True,
    dedup_key: str | None = None,
    conflict_strategy: str | None = None,
    max_rows: int = MAX_ROWS_DEFAULT,
) -> DealImportResult:
    """
    Import deals from a CSV string.

    Backward-compatible: accepts the old ``update_existing`` boolean.
    When both ``update_existing`` and ``conflict_strategy`` are provided,
    ``conflict_strategy`` wins.
    """
    if conflict_strategy is None:
        conflict_strategy = "update" if update_existing else "skip"
    return import_entities_csv(
        "deal", tenant_id, file_content,
        column_mapping=column_mapping,
        dry_run=dry_run,
        dedup_key=dedup_key,
        conflict_strategy=conflict_strategy,
        skip_errors=skip_errors,
        max_rows=max_rows,
    )


def import_accounts_csv(
    tenant_id: str,
    file_content: str,
    column_mapping: dict[str, str] | None = None,
    *,
    dry_run: bool = False,
    update_existing: bool = False,
    skip_errors: bool = True,
    dedup_key: str | None = None,
    conflict_strategy: str | None = None,
    max_rows: int = MAX_ROWS_DEFAULT,
) -> AccountImportResult:
    """
    Import accounts from a CSV string.

    Mirrors the contact import pattern but for the Account model.
    Default dedup key is ``name``.
    """
    if conflict_strategy is None:
        conflict_strategy = "update" if update_existing else "skip"
    return import_entities_csv(
        "account", tenant_id, file_content,
        column_mapping=column_mapping,
        dry_run=dry_run,
        dedup_key=dedup_key,
        conflict_strategy=conflict_strategy,
        skip_errors=skip_errors,
        max_rows=max_rows,
    )