# Phase 5 — Email Templates Specification

**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)
**Status:** Draft
**Priority:** P2

---

## Table of Contents

1. [ADR-031: Email Templates — Simple String Interpolation](#1-adr-031-email-templates--simple-string-interpolation)
2. [Data Model: EmailTemplate](#2-data-model-emailtemplate)
3. [Variable System](#3-variable-system)
4. [API Contracts](#4-api-contracts)
5. [Frontend: Template Editor Page](#5-frontend-template-editor-page)
6. [Frontend: Template Picker in Compose Modal](#6-frontend-template-picker-in-compose-modal)
7. [Integration with Email Send Flow](#7-integration-with-email-send-flow)
8. [Implementation Order](#8-implementation-order)
9. [Acceptance Criteria](#9-acceptance-criteria)

---

## 1. ADR-031: Email Templates — Simple String Interpolation

**Status:** Proposed
**Date:** 2026-06-30

### Context

The compose modal (`email-page.tsx`) currently lets users write raw subject and body text. There is no mechanism for reusable email templates with variable substitution. Users need to:

1. Save common email patterns (introductions, follow-ups, meeting confirmations) as reusable templates
2. Pre-fill templates with CRM data — contact name, deal name, company name, current date
3. Preview the rendered email before sending

The existing email send flow (`EmailViewSet.perform_create` → `send_gmail_message` task) constructs the MIME message from the `EmailMessage` record's `subject`, `body_text`, and `body_html` fields. A template system must integrate at the compose stage (frontend applies the template, then POSTs the rendered email) rather than at send time, so the user can edit the rendered result before sending.

### Decision

Use **simple `{{double_curly}}` placeholder syntax with Python `re.sub()`-based substitution**. Store the template (subject + body with placeholders) in a new `EmailTemplate` model. Resolution happens on the backend via a preview endpoint and on the frontend for live preview in the editor.

**Flow:**

```
Template stored:  body_html = "Hi {{contact_name}},\n\n..."
User selects template + enters context (e.g. contact, deal)
  ↓
POST /api/email-templates/{id}/preview/
  ↓
Backend resolves variables from CRM context, returns rendered subject + body
  ↓
Frontend shows preview; user can edit or send as-is
```

**Variable resolution:** The backend preview endpoint accepts a `context` dict (variable name → value) and returns the rendered subject + body. For convenience, when the user links a template to a specific entity (contact/deal), the backend auto-resolves known variables from the CRM database.

### Rejected Alternatives

1. **Jinja2/Django Templates** — rejected as overkill. We only need simple variable substitution (`{{name}}` → value), no conditionals, loops, filters, or template inheritance. A Python `re.sub()` with a dict lookup handles all cases. Jinja2 adds a dependency with no benefit for this use case.

2. **Client-side only resolution** — rejected. Template resolution needs access to CRM data (contact names, deal values, pipeline stages) that only the backend has. The preview endpoint is the source of truth.

3. **Server-side send-time resolution** — rejected. The user must see the rendered email before sending so they can review and edit. Resolution at compose time (via preview) is the correct UX.

4. **Markdown-based templates** — rejected. Email templates are predominantly HTML (rich formatting, signatures). Support both HTML and plain text variants; let the editor handle conversion if desired.

5. **Versioned templates** — rejected for P2. A single `updated_at` field with overwrite semantics is sufficient. Template versioning can be added in a later phase if audit trails are needed.

6. **Category tree / folder hierarchy** — rejected for P2. A flat `category` CharField with filtering and search is sufficient for 10-50 templates per tenant.

### Data Model Changes

**New model:** `EmailTemplate` in `apps/email/models.py`. 1 new migration.

**No changes** to `EmailMessage`, `Activity`, or any other existing model.

### Schema Change Summary

| Action | Details |
|--------|---------|
| New table | `email_templates` (via `EmailTemplate` model) |

---

## 2. Data Model: EmailTemplate

### Model Definition

```python
class EmailTemplate(TenantScopedModel):
    """Reusable email template with variable placeholders."""

    class Category(models.TextChoices):
        GENERAL = "general", "General"
        INTRODUCTION = "introduction", "Introduction"
        FOLLOW_UP = "follow_up", "Follow-up"
        MEETING = "meeting", "Meeting Confirmation"
        PROPOSAL = "proposal", "Proposal"
        THANK_YOU = "thank_you", "Thank You"
        REMINDER = "reminder", "Reminder"
        CUSTOM = "custom", "Custom"

    # Identity
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    # Template content (with {{variable}} placeholders)
    subject_template = models.CharField(max_length=1000)
    body_html = models.TextField(blank=True, default="")
    body_text = models.TextField(blank=True, default="",
        help_text="Plain text fallback. Auto-generated from HTML if empty.")

    # Categorization
    category = models.CharField(
        max_length=50, choices=Category.choices,
        default=Category.GENERAL, db_index=True,
    )

    # Scope
    is_shared = models.BooleanField(default=True,
        help_text="Shared with entire team vs. personal only")
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="email_templates",
    )

    # Introspection — populated on save by parsing the templates
    variables_used = models.JSONField(default=list, blank=True,
        help_text="List of variable names found in subject_template / body_html / body_text")

    class Meta:
        db_table = "email_templates"
        indexes = [
            models.Index(fields=["tenant_id", "category"]),
            models.Index(fields=["tenant_id", "created_by"]),
            models.Index(fields=["tenant_id", "-updated_at"]),
        ]
        ordering = ["-updated_at"]
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        """Auto-populate variables_used by scanning template fields."""
        self.variables_used = self._extract_variables()
        super().save(*args, **kwargs)

    def _extract_variables(self) -> list[str]:
        """Scan template content for {{variable}} patterns."""
        import re
        pattern = r"\{\{(\w+)\}\}"
        found: set[str] = set()
        for field in [self.subject_template, self.body_html, self.body_text]:
            found.update(re.findall(pattern, field))
        return sorted(found)
```

### Column Reference

| Column | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID (PK) | auto | auto | Primary key |
| `tenant_id` | UUID | auto (from request) | — | Multi-tenant scope |
| `name` | varchar(255) | yes | — | Human-readable template name |
| `description` | text | no | `""` | Optional description / usage notes |
| `subject_template` | varchar(1000) | yes | — | Email subject with `{{variable}}` placeholders |
| `body_html` | text | no | `""` | HTML body with `{{variable}}` placeholders |
| `body_text` | text | no | `""` | Plain text fallback with `{{variable}}` placeholders |
| `category` | varchar(50) | yes | `"general"` | One of the Category choices |
| `is_shared` | boolean | yes | `True` | Team-wide or personal |
| `created_by` | FK → User | no | null | Template author |
| `variables_used` | JSON | auto | `[]` | Parsed variable names (read-only via API) |
| `created_at` | datetime | auto | now | Creation timestamp |
| `updated_at` | datetime | auto | now | Last modification timestamp |
| `deleted_at` | datetime | no | null | Soft-delete support (from TimeStampedModel) |

### Variables Introspection

The `variables_used` field is auto-populated on every `save()` by running the regex `\{\{(\w+)\}\}` over all three template content fields. This list is exposed via the API so the frontend can:

- Show which variables a template expects
- Pre-populate a variable-values form when previewing
- Warn the user about unresolved variables before sending

---

## 3. Variable System

### Syntax

```
{{variable_name}}
```

Where `variable_name` is alphanumeric with underscores. No nesting, no filters, no default values.

### Predefined CRM Variables

These are auto-resolved by the preview endpoint when a `context_entity_type` and `context_entity_id` are provided.

#### Contact Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{{contact_name}}` | Contact.first_name + last_name | "Jane Smith" |
| `{{contact_first_name}}` | Contact.first_name | "Jane" |
| `{{contact_last_name}}` | Contact.last_name | "Smith" |
| `{{contact_email}}` | Contact.email | "jane@acme.com" |
| `{{contact_phone}}` | Contact.phone | "+1 555-0123" |
| `{{contact_job_title}}` | Contact.job_title | "VP of Sales" |
| `{{contact_company}}` | Contact.account.name | "Acme Corp" |

#### Deal Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{{deal_name}}` | Deal.name | "Acme Corp - Q3 Deal" |
| `{{deal_value}}` | Deal.value (formatted) | "$50,000" |
| `{{deal_currency}}` | Deal.currency | "USD" |
| `{{deal_stage}}` | Deal.stage.name | "Proposal" |
| `{{deal_pipeline}}` | Deal.pipeline.name | "Sales Pipeline" |
| `{{deal_owner}}` | Deal.owner.name | "Alice Johnson" |
| `{{deal_expected_close}}` | Deal.expected_close_date (formatted) | "Sep 30, 2026" |
| `{{deal_probability}}` | Deal.stage.probability × 100 | "60%" |

#### Account (Company) Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{{account_name}}` | Account.name | "Acme Corp" |
| `{{account_domain}}` | Account.domain | "acme.com" |
| `{{account_industry}}` | Account.industry | "Technology" |

#### User (Sender) Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{{user_name}}` | User.get_full_name() | "Alice Johnson" |
| `{{user_email}}` | User.email | "alice@frontiercrm.com" |
| `{{user_first_name}}` | User.first_name | "Alice" |
| `{{user_signature}}` | User.email_signature (new field) | "Alice Johnson\nVP of Sales\nFrontierCRM" |

> **Note:** `User.email_signature` does not exist yet. See [Open Questions / Spike Items](#10-open-questions--spike-items) below.

#### Date & Time Variables

| Variable | Value |
|----------|-------|
| `{{today}}` | Today's date formatted as "MMMM D, YYYY" |
| `{{tomorrow}}` | Tomorrow's date formatted as "MMMM D, YYYY" |
| `{{next_week}}` | 7 days from today, "MMMM D, YYYY" |
| `{{next_month}}` | 1 month from today, "MMMM D, YYYY" |
| `{{current_time}}` | Current time, "h:MM AM/PM" |

#### Tenant Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{{company_name}}` | Tenant.settings.company_name | "Acme Corp" |
| `{{company_phone}}` | Tenant.settings.company_phone | "+1 555-0000" |

### Custom Variables

In addition to the predefined variables above, users can pass arbitrary key-value pairs in the preview `context` dict. This enables templates that use custom fields or ad-hoc values not mapped to a CRM entity. For example, a proposal template might use `{{proposal_url}}` that the user provides at compose time via a custom field form.

### Resolution Priority (Preview Endpoint)

When resolving `{{variable_name}}`, the preview endpoint uses this order:

1. **Explicit context** — values in the `context` dict from the request body
2. **Entity-derived** — auto-resolved from the linked contact/deal/account
3. **Sender-derived** — from the requesting user
4. **Tenant-derived** — from the tenant's settings
5. **Date-derived** — dynamic date variables
6. **Unresolved** — left as `{{variable_name}}` verbatim (so the user sees what's missing)

---

## 4. API Contracts

### 4.1 Template CRUD

All endpoints live at `/api/email-templates/`. Tenant-scoped: all queries filter by `request.user.tenant_id`.

#### List Templates

```
GET /api/email-templates/
```

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `search` | string | No | — | Search name, description |
| `category` | string | No | — | Filter by category slug |
| `is_shared` | boolean | No | — | Filter by sharing scope |
| `created_by` | UUID | No | — | Filter by author |
| `ordering` | string | No | `-updated_at` | `name`, `-updated_at`, `category` |

**Response (paginated):**

```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "Introduction - New Contact",
      "description": "Friendly intro for newly assigned contacts.",
      "category": "introduction",
      "is_shared": true,
      "created_by": {
        "id": "uuid",
        "name": "Alice Johnson"
      },
      "variables_used": [
        "contact_first_name",
        "user_name",
        "company_name"
      ],
      "created_at": "2026-06-30T10:00:00Z",
      "updated_at": "2026-06-30T10:00:00Z"
    }
  ]
}
```

> **Note:** The list response omits `subject_template`, `body_html`, `body_text` for efficiency. Include them only in the detail response.

#### Create Template

```
POST /api/email-templates/
```

**Request Body:**

```json
{
  "name": "Follow-up after meeting",
  "description": "Sent 24h after a meeting to summarize action items.",
  "subject_template": "Following up: {{deal_name}}",
  "body_html": "<p>Hi {{contact_first_name}},</p><p>Thanks for the great discussion about {{deal_name}}.</p><p>Best regards,<br/>{{user_name}}</p>",
  "body_text": "Hi {{contact_first_name}},\n\nThanks for the great discussion about {{deal_name}}.\n\nBest regards,\n{{user_name}}",
  "category": "follow_up",
  "is_shared": true
}
```

**Response (201):** Full template object (same as detail response below).

#### Get Template

```
GET /api/email-templates/{id}/
```

**Response (200):**

```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "name": "Follow-up after meeting",
  "description": "Sent 24h after a meeting to summarize action items.",
  "subject_template": "Following up: {{deal_name}}",
  "body_html": "<p>Hi {{contact_first_name}}, ...</p>",
  "body_text": "Hi {{contact_first_name}},\n\n...",
  "category": "follow_up",
  "is_shared": true,
  "created_by": {
    "id": "uuid",
    "name": "Alice Johnson"
  },
  "variables_used": ["contact_first_name", "deal_name", "user_name"],
  "created_at": "2026-06-30T10:00:00Z",
  "updated_at": "2026-06-30T10:00:00Z"
}
```

**Permissions:** `template.view` for read, `template.edit` for write (for shared templates). Users can always edit their own templates regardless of permission.

#### Update Template

```
PUT /api/email-templates/{id}/
PATCH /api/email-templates/{id}/
```

Same request/response shape as Create. `variables_used` is regenerated on save and is read-only on input.

#### Delete Template

```
DELETE /api/email-templates/{id}/
```

**Response (204):** No content. Soft-delete (sets `deleted_at`).

### 4.2 Preview Endpoint

```
POST /api/email-templates/{id}/preview/
```

Resolves `{{variable}}` placeholders using the provided context and CRM data.

**Request Body:**

```json
{
  "context": {
    "contact_id": "uuid",
    "deal_id": "uuid",
    "account_id": "uuid",
    "custom_variables": {
      "proposal_url": "https://..."
    }
  }
}
```

All fields are optional. The endpoint:

1. Loads the template by `id`
2. If `contact_id` is provided, fetches the Contact and resolves all `{{contact_*}}` variables
3. If `deal_id` is provided, fetches the Deal and resolves all `{{deal_*}}` variables
4. If `account_id` is provided, fetches the Account and resolves all `{{account_*}}` variables
5. Resolves `{{user_*}}` from the requesting user
6. Resolves `{{company_*}}` from the tenant settings
7. Resolves date variables dynamically
8. Applies any `custom_variables` (highest priority — overrides entity-derived values)
9. Replaces all `{{variable}}` placeholders with resolved values
10. Returns the rendered subject + body

**Response (200):**

```json
{
  "rendered_subject": "Following up: Acme Corp - Q3 Deal",
  "rendered_body_html": "<p>Hi Jane,</p><p>Thanks for the great discussion about Acme Corp - Q3 Deal.</p><p>Best regards,<br/>Alice Johnson</p>",
  "rendered_body_text": "Hi Jane,\n\nThanks for the great discussion about Acme Corp - Q3 Deal.\n\nBest regards,\nAlice Johnson",
  "unresolved_variables": [],
  "entity_preview": {
    "contact": {
      "id": "uuid",
      "name": "Jane Smith",
      "email": "jane@acme.com"
    },
    "deal": {
      "id": "uuid",
      "name": "Acme Corp - Q3 Deal",
      "value": "$50,000"
    }
  }
}
```

**When variables cannot be resolved**, they are left as `{{variable_name}}` in the rendered output and listed in `unresolved_variables`:

```json
{
  "rendered_subject": "Following up: {{deal_name}}",
  "rendered_body_html": "<p>Hi Jane, ...</p>",
  "unresolved_variables": ["deal_name"]
}
```

**Error responses:**

| Status | When |
|--------|------|
| 404 | Template not found or deleted |
| 422 | `context.contact_id` provided but Contact not found or not in same tenant |
| 422 | `context.deal_id` provided but Deal not found or not in same tenant |

**Rate limiting:** No hard limit, but the endpoint makes 0-3 DB lookups per request (contact, deal, account by id). At current scale (<50 req/min), this is negligible.

### 4.3 Variables Catalog Endpoint

```
GET /api/email-templates/variables/
```

Returns the full catalog of available variables, grouped by category, for the template editor UI.

**Response (200):**

```json
{
  "variables": {
    "contact": [
      {"name": "contact_name", "label": "Contact Full Name", "source": "contact.first_name + last_name"},
      {"name": "contact_first_name", "label": "Contact First Name", "source": "contact.first_name"},
      {"name": "contact_last_name", "label": "Contact Last Name", "source": "contact.last_name"},
      {"name": "contact_email", "label": "Contact Email", "source": "contact.email"},
      {"name": "contact_phone", "label": "Contact Phone", "source": "contact.phone"},
      {"name": "contact_job_title", "label": "Contact Job Title", "source": "contact.job_title"},
      {"name": "contact_company", "label": "Contact's Company", "source": "contact.account.name"}
    ],
    "deal": [
      {"name": "deal_name", "label": "Deal Name", "source": "deal.name"},
      {"name": "deal_value", "label": "Deal Value", "source": "deal.value (formatted)"},
      {"name": "deal_currency", "label": "Deal Currency", "source": "deal.currency"},
      {"name": "deal_stage", "label": "Deal Stage", "source": "deal.stage.name"},
      {"name": "deal_pipeline", "label": "Pipeline Name", "source": "deal.pipeline.name"},
      {"name": "deal_owner", "label": "Deal Owner", "source": "deal.owner.name"},
      {"name": "deal_expected_close", "label": "Expected Close Date", "source": "deal.expected_close_date (formatted)"},
      {"name": "deal_probability", "label": "Deal Probability", "source": "deal.stage.probability"}
    ],
    "account": [
      {"name": "account_name", "label": "Company Name", "source": "account.name"},
      {"name": "account_domain", "label": "Company Domain", "source": "account.domain"},
      {"name": "account_industry", "label": "Industry", "source": "account.industry"}
    ],
    "user": [
      {"name": "user_name", "label": "Your Full Name", "source": "user.get_full_name()"},
      {"name": "user_email", "label": "Your Email", "source": "user.email"},
      {"name": "user_first_name", "label": "Your First Name", "source": "user.first_name"},
      {"name": "user_signature", "label": "Your Email Signature", "source": "user.email_signature (new field)"}
    ],
    "date": [
      {"name": "today", "label": "Today's Date", "source": "current date (MMMM D, YYYY)"},
      {"name": "tomorrow", "label": "Tomorrow's Date", "source": "MMMM D, YYYY"},
      {"name": "next_week", "label": "Next Week (7 days)", "source": "MMMM D, YYYY"},
      {"name": "next_month", "label": "Next Month (30 days)", "source": "MMMM D, YYYY"},
      {"name": "current_time", "label": "Current Time", "source": "h:MM AM/PM"}
    ],
    "tenant": [
      {"name": "company_name", "label": "Company Name", "source": "tenant.settings.company_name"},
      {"name": "company_phone", "label": "Company Phone", "source": "tenant.settings.company_phone"}
    ]
  }
}
```

**Caching:** This response is static per tenant — variables don't change between deploys. Cache at the application or CDN layer.

### 4.4 URL Registration

In `apps/email/urls.py`, add a second router for templates:

```python
from .views import EmailTemplateViewSet, TemplateVariablesView

# Inside urlpatterns, after the existing email router:
template_router = routers.DefaultRouter()
template_router.register("email-templates", EmailTemplateViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("email-templates/variables/", TemplateVariablesView.as_view(), name="template-variables"),
    path("", include(template_router.urls)),
]
```

Resulting URL table:

| Method | URL | Action |
|--------|-----|--------|
| GET | `/api/email-templates/` | List templates |
| POST | `/api/email-templates/` | Create template |
| GET | `/api/email-templates/{id}/` | Get template |
| PUT | `/api/email-templates/{id}/` | Update template |
| PATCH | `/api/email-templates/{id}/` | Partial update |
| DELETE | `/api/email-templates/{id}/` | Delete (soft) |
| POST | `/api/email-templates/{id}/preview/` | Preview with variable substitution |
| GET | `/api/email-templates/variables/` | List available variables |

### 4.5 Permission Mapping

```python
def get_required_permission(self) -> str | None:
    return {
        "list": "template.view",
        "retrieve": "template.view",
        "create": "template.edit",
        "update": "template.edit",
        "partial_update": "template.edit",
        "destroy": "template.edit",
        "preview": "template.view",
    }.get(self.action)
```

For personal templates (created by the requesting user), the permission check is bypassed — users always have full CRUD on their own templates. This follows the same pattern as the existing `RolePermission` class.

### 4.6 Preview Utility (Backend)

Create a `VariableResolver` helper class in `apps/email/services.py`:

```python
import re
from typing import Any

VARIABLE_PATTERN = re.compile(r"\{\{(\w+)\}\}")

class VariableResolver:
    """Resolves {{variable}} placeholders from CRM context."""

    def __init__(self, user, tenant):
        self.user = user
        self.tenant = tenant
        self._contact: Contact | None = None
        self._deal: Deal | None = None
        self._account: Account | None = None

    def resolve(self, text: str) -> tuple[str, list[str]]:
        """Replace all {{vars}} with resolved values. Returns (rendered_text, unresolved)."""
        unresolved: list[str] = []

        def _replace(match) -> str:
            varname = match.group(1)
            value = self._get_value(varname)
            if value is None:
                unresolved.append(varname)
                return match.group(0)  # leave as-is
            return value

        rendered = VARIABLE_PATTERN.sub(_replace, text)
        return rendered, unresolved

    def _get_value(self, name: str) -> str | None:
        # Resolution priority: explicit context → entity → user → tenant → date
        ...
```

The resolver is the core logic reused by the preview endpoint and, in future, by the send flow if auto-resolution during send becomes necessary.

---

## 5. Frontend: Template Editor Page

### 5.1 New Page: `TemplateEditor` at `/email-templates`

A full-page template editor where users create and manage email templates.

**Route:** `/email-templates` (linked from a "Templates" tab on the Email page, or from Settings)

### 5.2 Component Tree

```
EmailTemplatesPage
├── TemplateList                    (left panel)
│   ├── TemplateSearchBar           (search by name)
│   ├── CategoryFilter              (dropdown: All / General / Introduction / ...)
│   └── TemplateCard[]              (name, category badge, preview of variables)
│       └── ContextMenu             (Edit, Duplicate, Delete)
├── TemplateEditor                  (right panel, shown when editing)
│   ├── TemplateForm
│   │   ├── NameInput               (text input)
│   │   ├── DescriptionTextarea     (optional description)
│   │   ├── CategorySelect          (dropdown)
│   │   ├── SubjectInput            (with variable inserter toolbar)
│   │   ├── HtmlEditor             (rich text editor — TipTap/Quill)
│   │   │   └── VariableInserter   (dropdown to insert {{variable}} at cursor)
│   │   ├── PlainTextTab            (toggled view of body_text)
│   │   ├── SharingToggle           (switch: Shared with team / Personal)
│   │   ├── VariablesUsedBadge      ("Uses: contact_first_name, deal_name, user_name")
│   │   └── SaveButton
│   └── PreviewPane                 (live preview with mock context)
│       ├── ContextSelector         (select contact/deal for preview data)
│       └── RenderedPreview         (read-only iframe for HTML, pre for text)
└── DeleteConfirmModal
```

### 5.3 API Hook

```typescript
// src/api/email-templates.ts

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "./client";
import type { EmailTemplate, PaginatedResponse, TemplatePreview } from "../types";

export function useEmailTemplates(params?: Record<string, string>) {
  return useQuery({
    queryKey: ["email-templates", params],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<EmailTemplate>>("/email-templates/", { params })
        .then((r) => r.data),
  });
}

export function useEmailTemplate(id: string | undefined) {
  return useQuery({
    queryKey: ["email-templates", id],
    queryFn: () =>
      apiClient.get<EmailTemplate>(`/email-templates/${id}/`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useSaveTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<EmailTemplate> & { id?: string }) => {
      if (data.id) {
        return apiClient.patch(`/email-templates/${data.id}/`, data).then((r) => r.data);
      }
      return apiClient.post("/email-templates/", data).then((r) => r.data);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-templates"] }),
  });
}

export function useDeleteTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/email-templates/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-templates"] }),
  });
}

export function usePreviewTemplate() {
  return useMutation({
    mutationFn: ({
      id,
      context,
    }: {
      id: string;
      context: {
        contact_id?: string;
        deal_id?: string;
        account_id?: string;
        custom_variables?: Record<string, string>;
      };
    }) => apiClient.post<TemplatePreview>(`/email-templates/${id}/preview/`, { context }).then((r) => r.data),
  });
}

export function useTemplateVariables() {
  return useQuery({
    queryKey: ["email-template-variables"],
    queryFn: () =>
      apiClient.get<{ variables: Record<string, Array<{ name: string; label: string; source: string }>> }>(
        "/email-templates/variables/"
      ).then((r) => r.data),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}
```

### 5.4 TypeScript Types

Add to `frontend/src/types/index.ts`:

```typescript
export interface EmailTemplate {
  id: string;
  tenant_id: string;
  name: string;
  description: string;
  subject_template: string;
  body_html: string;
  body_text: string;
  category: string;
  is_shared: boolean;
  created_by: { id: string; name: string } | null;
  variables_used: string[];
  created_at: string;
  updated_at: string;
}

export interface TemplatePreview {
  rendered_subject: string;
  rendered_body_html: string;
  rendered_body_text: string;
  unresolved_variables: string[];
  entity_preview?: {
    contact?: { id: string; name: string; email: string };
    deal?: { id: string; name: string; value: string };
  };
}
```

### 5.5 HTML Editor Choice

Use **TipTap** (Tiptap Editor — `@tiptap/react`). It's already feasible to add to the project (no existing rich-text dependency). If TipTap is too heavy, fall back to a `<textarea>` with Markdown-to-HTML preview.

**Minimal TipTap setup for templates:**
- Bold, italic, underline
- Bullet list, ordered list
- Link insertion
- Heading (H2, H3 — not H1, which is reserved for the subject/preheader)
- Horizontal rule

**Variable inserter:** A dropdown button in the editor toolbar that opens the variable catalog and inserts `{{variable_name}}` at cursor position in the TipTap document (as raw text, not HTML).

---

## 6. Frontend: Template Picker in Compose Modal

### 6.1 Integration Point

The existing compose modal in `email-page.tsx` currently shows To / Subject / Message fields. Add a **Template Picker** that:

1. Shows a dropdown or compact list of templates (filterable by name/category)
2. On selection, calls the preview endpoint with the current context (if a contact/deal is selected in the sidebar)
3. Fills the Subject and Message fields with the rendered result
4. Still lets the user edit before sending

### 6.2 Compose Modal Changes

**New component:** `TemplatePicker` — an inline bar at the top of the compose modal:

```
┌─────────────────────────────────┐
│ Template: [Dropdown ▼]          │
│ [Introduction — New Contact]    │
│ [Follow-up after meeting]       │
│ [Meeting Confirmation]          │
│ [Create New Template...]        │
│                                  │
│ --- Selected: Follow-up ---     │
│ Variables needed: contact_name  │
│                                  │
│ [Apply Template]                │
├─────────────────────────────────┤
│ To: [________________]          │
│ Subject: [Following up: ...]    │
│ Message: [________________]     │
│ [__________________________]    │
└─────────────────────────────────┘
```

**Interaction flow:**

1. User clicks "Compose" → modal opens (current behaviour)
2. User optionally selects a contact or deal from the sidebar (links compose context)
3. User clicks template dropdown → list of templates appears (cached from `useEmailTemplates`)
4. User selects a template → template details shown with "Variables needed" badge
5. User clicks "Apply Template" → calls `POST /api/email-templates/{id}/preview/` with contact_id/deal_id
6. Subject and Message fields are filled with rendered values
7. User can edit freely before sending
8. If user changes the template, re-applying replaces the content (with confirmation if edited)

### 6.3 Component Details

```typescript
interface TemplatePickerProps {
  onApplyTemplate: (rendered: {
    subject: string;
    bodyHtml: string;
    bodyText: string;
    templateId: string;
    templateName: string;
  }) => void;
  contextContactId?: string;
  contextDealId?: string;
  disabled?: boolean;
}

function TemplatePicker(props: TemplatePickerProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [preview, setPreview] = useState<TemplatePreview | null>(null);
  const [isApplying, setIsApplying] = useState(false);

  const { data: templates } = useEmailTemplates({ is_shared: "true" });
  const previewMutation = usePreviewTemplate();

  const selectedTemplate = templates?.results.find(t => t.id === selectedId);

  const handleApply = async () => {
    if (!selectedId) return;
    setIsApplying(true);
    try {
      const result = await previewMutation.mutateAsync({
        id: selectedId,
        context: {
          contact_id: props.contextContactId,
          deal_id: props.contextDealId,
        },
      });
      props.onApplyTemplate({
        subject: result.rendered_subject,
        bodyHtml: result.rendered_body_html,
        bodyText: result.rendered_body_text,
        templateId: selectedId,
        templateName: selectedTemplate?.name ?? "",
      });
    } finally {
      setIsApplying(false);
    }
  };

  // Render: dropdown + "Apply Template" button
  // When selected: show template details + unresolved variables warning
}
```

### 6.4 Integration into Compose State

The existing compose state variables get set when a template is applied:

```typescript
const handleApplyTemplate = (rendered: {
  subject: string;
  bodyHtml: string;
  bodyText: string;
  templateId: string;
  templateName: string;
}) => {
  // Set subject and body from rendered template
  setComposeSubject(rendered.subject);
  setComposeBody(rendered.bodyText);  // or rendered.bodyHtml for rich editor

  // Track which template was used (for UI display, not sent)
  setAppliedTemplateId(rendered.templateId);
  setAppliedTemplateName(rendered.templateName);
};
```

### 6.5 "Create New Template" from Compose

The template picker dropdown includes a "Create New Template..." option that:
1. Opens the compose state's current subject + body
2. Navigates to `/email-templates/new` with pre-filled values (via query params or session state)
3. User can add `{{variables}}` manually or via the variable inserter on the editor page

### 6.6 Empty State

When no templates exist yet, the template picker shows:
- A badge: "No templates yet" with a "Create Template" button
- The button links to `/email-templates/new`

---

## 7. Integration with Email Send Flow

### 7.1 What Changes in the Send Flow

The email send flow (`EmailViewSet.perform_create` → `send_gmail_message` task) does **not** change. Templates are resolved at compose time in the frontend, and the resolved subject + body are POSTed as normal email fields.

```
Compose → Pick Template → Preview → Edit → POST /api/emails/ (resolved subject + body)
```

The `EmailMessage` model stores the final rendered text, not the template reference. This means:
- Sent emails are immutable snapshots (no risk of template changes retroactively altering sent emails)
- The template system is a compose-time helper, not a send-time transformation

### 7.2 Optional: Template Reference on Sent Email

For analytics (e.g. "which templates are most used"), optionally add an optional FK on `EmailMessage`:

```python
# Future addition — not required for P2
applied_template = models.ForeignKey(
    "email.EmailTemplate", on_delete=models.SET_NULL,
    null=True, blank=True, related_name="sent_emails",
)
```

This is **not** part of the P2 scope. It's noted here as a future enhancement.

### 7.3 Preview in Compose Context

When the compose modal is opened with a selected contact or deal (common flow — user opens a contact page, clicks "Send Email"), the context is passed to the template preview endpoint:

```
Context: contact_id = "uuid-123" (from the contact page or sidebar)
Template uses: {{contact_first_name}}, {{contact_company}}
```

The preview endpoint resolves these from the CRM database, so the rendered preview is accurate.

---

## 8. Implementation Order

### Phase A: Data Model & Backend Core (P2 — 4 steps)

| Step | File(s) | Description |
|------|---------|-------------|
| A1 | `backend/apps/email/models.py` | Create `EmailTemplate` model + migration |
| A2 | `backend/apps/email/services.py` | Create `VariableResolver` class with all variable resolution logic |
| A3 | `backend/apps/email/views.py` | Create `EmailTemplateViewSet`, `TemplateVariablesView`, and `preview` action |
| A4 | `backend/apps/email/urls.py` | Register template routes + variables endpoint |
| A5 | `backend/apps/email/serializers.py` | Create `EmailTemplateSerializer` with `variables_used` as read-only, auto-populate on save |

### Phase B: Frontend Editor Page (P2 — 4 steps)

| Step | File(s) | Description |
|------|---------|-------------|
| B1 | `frontend/src/types/index.ts` | Add `EmailTemplate`, `TemplatePreview` TypeScript types |
| B2 | `frontend/src/api/email-templates.ts` | Create API hooks: `useEmailTemplates`, `useEmailTemplate`, `useSaveTemplate`, `useDeleteTemplate`, `usePreviewTemplate`, `useTemplateVariables` |
| B3 | `frontend/src/pages/email/templates/` | Create `EmailTemplatesPage`, `TemplateList`, `TemplateEditor`, `PreviewPane` components |
| B4 | `frontend/src/router/index.ts` | Add route `/email-templates` linking to `EmailTemplatesPage` |

### Phase C: Template Picker in Compose (P2 — 3 steps)

| Step | File(s) | Description |
|------|---------|-------------|
| C1 | `frontend/src/pages/email/email-page.tsx` | Add `TemplatePicker` component above compose form fields |
| C2 | `frontend/src/pages/email/email-page.tsx` | Wire "Apply Template" to set subject + body, pass contact/deal context |
| C3 | `frontend/src/pages/email/email-page.tsx` | Add "Create New Template..." flow from picker dropdown |

### Phase D: Variable Resolution Enhancements (Post-P2)

| Step | Description |
|------|-------------|
| D1 | Add `User.email_signature` field for `{{user_signature}}` resolution (requires schema migration) |
| D2 | Add template usage analytics: optional `applied_template` FK on `EmailMessage` |
| D3 | Add "Duplicate Template" action in frontend (convenience, no backend change) |
| D4 | Add template CSV import/export (bulk create from spreadsheet) |

---

## 9. Acceptance Criteria

### Backend

- [ ] `EmailTemplate` model is created with all fields including auto-populated `variables_used`
- [ ] `GET /api/email-templates/` returns paginated, tenant-scoped template list
- [ ] `POST /api/email-templates/` creates template with `variables_used` auto-populated
- [ ] `GET /api/email-templates/{id}/` returns full template including body content
- [ ] `PUT/PATCH /api/email-templates/{id}/` updates template and regenerates `variables_used`
- [ ] `DELETE /api/email-templates/{id}/` soft-deletes (sets `deleted_at`)
- [ ] `POST /api/email-templates/{id}/preview/` resolves all CRM variables correctly
- [ ] `POST /api/email-templates/{id}/preview/` leaves unresolved variables as `{{var}}` in output
- [ ] `POST /api/email-templates/{id}/preview/` returns 422 for non-existent contact_id/deal_id
- [ ] `GET /api/email-templates/variables/` returns full variable catalog grouped by category
- [ ] List endpoint supports `search`, `category`, `is_shared`, `created_by`, `ordering` params
- [ ] Permission checks enforce `template.view` for read, `template.edit` for write
- [ ] Users can always CRUD their own templates regardless of permission
- [ ] Template routes are properly prefixed and don't conflict with existing email endpoints

### Frontend

- [ ] `EmailTemplatesPage` renders with list panel + editor panel
- [ ] Template list supports search and category filtering
- [ ] Template editor shows all form fields (name, description, category, subject, body HTML/Text)
- [ ] Variable inserter dropdown shows categorized list of variables and inserts at cursor
- [ ] Save creates/updates template and shows success notification
- [ ] Delete shows confirmation modal before soft-deleting
- [ ] Preview pane renders resolved content with mock data
- [ ] Compose modal shows TemplatePicker dropdown
- [ ] Selecting a template and clicking "Apply Template" fills subject and body
- [ ] Unresolved variables are shown as a warning badge
- [ ] "Create New Template..." navigates to template editor with pre-filled compose values
- [ ] Empty state shown when no templates exist
- [ ] Loading, error, and empty states for all API calls
- [ ] All CRUD operations invalidate query cache correctly

### Integration

- [ ] Using a template + sending an email results in correct rendered content in Gmail
- [ ] Template picker context (contact_id) passed from contact page sidebar works
- [ ] Editing rendered template before sending doesn't affect the saved template
- [ ] Multiple templates can be created and applied in the same session

---

## 10. Open Questions / Spike Items

| # | Question | Impact | Resolution |
|---|----------|--------|------------|
| 1 | Should `User.email_signature` be added for `{{user_signature}}`? | Affects whether the {{user_signature}} variable resolves or stays unresolved. | Recommend yes — add as a new TextField on User model (or as a per-tenant setting). If not, remove {{user_signature}} from the catalog. |
| 2 | HTML editor: TipTap vs Quill vs plain `<textarea>` with Markdown preview? | Affects frontend bundle size and editor richness. | TipTap recommended for WYSIWYG HTML editing. Spike: check current bundle size and evaluate @tiptap/react bundle weight. |
| 3 | Should template categories be admin-configurable (database-backed) or hard-coded choices? | Affects extensibility. | Hard-coded for P2 (matching Data Model section). If users request custom categories, migrate to a `TemplateCategory` model in a future phase. |
| 4 | Should we expose a "duplicate template" action or rely on create-with-pre-fill? | UX tradeoff. | Rely on "Copy" button in the context menu that reads the template data and opens the editor pre-filled. No backend endpoint needed — the frontend reads, the user saves as new. |

---

## Appendix A: Existing Code Reuse

| Artifact | How it's used |
|----------|--------------|
| `TenantScopedModel` | Base class for `EmailTemplate` — provides `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at` |
| `EmailViewSet.perform_create` | Unchanged — templates resolve at compose time, not send time |
| `send_gmail_message` task | Unchanged — receives resolved subject + body, sends via Gmail API |
| `RolePermission` / `TenantAwarePermission` | Reused for template endpoint permissions |
| `EmailPage` compose modal | Extended with `TemplatePicker` component |
| `useEmails` hook | Unchanged — template resolution is orthogonal |
| `PaginatedResponse<T>` type | Reused for template list pagination |

## Appendix B: Project-Wide Impact Summary

### Backend Changes

| App | New/Changed Files | Description |
|-----|------------------|-------------|
| `apps/email/` | `models.py` (+`EmailTemplate` model) | New model + migration |
| `apps/email/` | `services.py` (new) | `VariableResolver` class |
| `apps/email/` | `serializers.py` (new) | `EmailTemplateSerializer` |
| `apps/email/` | `views.py` (+`EmailTemplateViewSet` + `TemplateVariablesView`) | CRUD + preview + variables catalog |
| `apps/email/` | `urls.py` (+template routes) | Register template router |

### Frontend Changes

| File/Directory | Change |
|----------------|--------|
| `frontend/src/types/index.ts` | Add `EmailTemplate`, `TemplatePreview` types |
| `frontend/src/api/email-templates.ts` | New file with 6 API hooks |
| `frontend/src/pages/email/templates/` | New directory: `EmailTemplatesPage`, `TemplateList`, `TemplateEditor`, `PreviewPane` |
| `frontend/src/pages/email/email-page.tsx` | Add `TemplatePicker` to compose modal |
| `frontend/src/router/index.ts` | Add `/email-templates` route |

### Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| TipTap adds >200KB to bundle | Medium | Medium | Evaluate bundle weight; use `<textarea>` + dynamic import as fallback |
| Template preview endpoint slow with large bodies | Low | Low | Resolution is string replacement — O(n) on body length. Under 1ms for any realistic template. |
| Users create templates with unresolvable variables | Medium | Low | `unresolved_variables` field in preview response + UI warning |
| Template names conflict across team | Low | Low | Name is CharField, not unique; use search/disambiguation in picker |