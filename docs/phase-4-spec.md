# Phase 4 Feature Specification

**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)
**Status:** Draft

---

## Table of Contents

1. [Activity Timeline (P1)](#1-activity-timeline-p1)
2. [Email Compose & Send — Wire Gmail Send (P2)](#2-email-compose--send--wire-gmail-send-p2)
3. [Pipeline Forecasting (P2)](#3-pipeline-forecasting-p2)
4. [Export (P2)](#4-export-p2)

---

## 1. Activity Timeline (P1)

### ADR-023: Activity Timeline Endpoint

**Status:** Proposed
**Date:** 2026-06-30

#### Context

The `Activity` model (`apps/activities/models.py`) already records 9 activity types with entity references (entity_type, entity_id) and actor_ids. The existing `ActivityViewSet` provides basic CRUD + filtering by `activity_type`, `entity_type`, `entity_id`, `actor_id`. What's missing:

1. A timeline feed that aggregates activities **across all entities** (org-wide view)
2. **Actor details** (user name, avatar) resolved in the response
3. **Entity reference resolution** (deal name, contact name, etc.) in the response
4. Date range filtering for "What happened today?"
5. Efficient pagination for large volumes

#### Decision

Add a dedicated timeline endpoint (`GET /api/activities/timeline/`) with a custom view that:

- Returns paginated activities with actor and entity metadata embedded
- Uses the existing `(tenant_id, -created_at)` index for org-wide queries
- Resolves actor names from the User model (batched, via prefetch)
- Resolves entity references via a polymorphic strategy: a dict mapping `entity_type` → model class, with a single `select_related` batch per type

#### Rejected Alternatives

1. **Denormalizing actor/entity data into Activity model** — rejected because it creates sync problems when user names or deal names change.
2. **GraphQL-style resolver** — rejected for simplicity; REST endpoint with joined data is sufficient at current scale.
3. **Separate materialized view** — rejected for phase 4; revisit at >1M activities.

#### Data Model Changes

**None.** The existing Activity model with its indexes is sufficient. The newly created `entity_reference` metadata convention is a convention, not a schema change — the `metadata` JSONField already carries entity-specific data (`deal_name`, `contact_name`, etc.) that was written when the activity was created.

#### API Contract

```
GET /api/activities/timeline/
```

**Query Parameters:**

| Param         | Type   | Required | Default | Description |
|---------------|--------|----------|---------|-------------|
| `start_date`  | ISO 8601 date | No | 30 days ago | Start of date range |
| `end_date`    | ISO 8601 date | No | today | End of date range |
| `activity_type` | enum string | No | — | Filter by type (note, call, email, etc.) |
| `actor_id`    | UUID   | No | — | Filter by actor |
| `page`        | int    | No | 1 | Page number (cursor-based in future) |
| `page_size`   | int    | No | 25 | Items per page (max 100) |

**Response:**

```json
{
  "count": 142,
  "next": "https://api.example.com/api/activities/timeline/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "activity_type": "deal_stage_change",
      "title": "Deal moved to Proposal",
      "description": "Acme Corp deal moved from Qualified to Proposal",
      "created_at": "2026-06-30T14:30:00Z",
      "actor": {
        "id": "uuid",
        "name": "Jane Smith",
        "avatar_url": "https://..."
      },
      "entity": {
        "type": "deal",
        "id": "uuid",
        "name": "Acme Corp - Q3 Deal",
        "url": "/deals/uuid"
      },
      "metadata": {
        "from_stage": "Qualified",
        "to_stage": "Proposal"
      }
    }
  ]
}
```

#### Frontend Components Required

| Component | Source | Description |
|-----------|--------|-------------|
| `ActivityTimeline` | New | Main feed component — paginated list of activity cards |
| `ActivityCard` | New | Single activity row with icon (by type), actor avatar, entity link, timestamp |
| `ActivityFilters` | New | Date range picker + dropdown for activity_type + actor search |
| `useActivityTimeline` | New API hook | Calls `/api/activities/timeline/` with query params |

The existing `activity-page.tsx` at `frontend/src/pages/activities/activity-page.tsx` can be extended or replaced with the timeline view. The new component tree lives under `frontend/src/pages/activities/`.

#### Existing Code Reused

- `Activity` model and `ActivityType` — fully reused
- `(tenant_id, -created_at)` index — fully reused
- `ActivityFilter` (django-filter) — can be extended with date filters
- Core pagination infrastructure (rest_framework pagination)

#### Implementation Order

1. Create `TimelineView` in `apps/activities/views.py` (custom APIView using DRF pagination)
2. Add `TimelineSerializer` with nested ActorSerializer and EntitySerializer
3. Register route at `/api/activities/timeline/`
4. Add date range filters to existing `ActivityFilter`
5. Create frontend hook `useActivityTimeline` in `frontend/src/api/activities.ts`
6. Create `ActivityTimeline`, `ActivityCard`, `ActivityFilters` components

#### Acceptance Criteria

- [ ] `GET /api/activities/timeline/` returns paginated activities with actor details (name + avatar)
- [ ] Each activity includes resolved entity name and clickable link
- [ ] Filtering by `start_date`/`end_date` returns correct date range
- [ ] Filtering by `activity_type` and `actor_id` works
- [ ] Default query (today's activities) completes in <200ms at 10K activities
- [ ] Frontend renders timeline correctly with loading, empty, and error states

---

## 2. Email Compose & Send — Wire Gmail Send (P2)

### ADR-024: Asynchronous Email Send via Celery

**Status:** Proposed
**Date:** 2026-06-30

#### Context

The email compose modal (`email-page.tsx`) calls `useSendEmail()` which POSTs to `/api/emails/` → `EmailViewSet.perform_create`. Currently `perform_create` saves the EmailMessage to DB with `status=DRAFT` but **never calls the existing `send_gmail_message()` Celery task** (`apps/email/tasks.py:210`).

The `send_gmail_message` task already:
- Builds RFC-2822 MIME message
- Posts to Gmail API `/gmail/v1/users/me/messages/send`
- Handles token refresh (401 → refresh → retry)
- Creates a new EmailMessage with `direction=OUTBOUND`

The gap: the frontend POST and the Celery task are not connected.

#### Decision

Wire the existing task into `EmailViewSet.perform_create` with an asynchronous flow:

1. **Frontend** POSTs to `/api/emails/` with `direction=outbound`, `to_emails`, `subject`, `body_text`, `body_html`
2. **Backend** creates EmailMessage with `status=SENDING` and `direction=OUTBOUND`
3. **Backend** enqueues `send_gmail_message.delay(user_id, to, subject, body_text, body_html)` via Celery
4. **Celery task** sends via Gmail API, updates EmailMessage status to `SENT` or `FAILED`
5. **Backend** creates an Activity entry (type=email) as part of the send flow

#### Rejected Alternatives

1. **Synchronous send on the POST request** — rejected. Gmail API calls can take 2-10s. Blocking the HTTP request is poor UX.
2. **WebSocket push for status** — rejected for phase 4. Use polling on the email detail endpoint instead.
3. **Frontend-orchestrated send via WebSocket** — rejected. Keep the flow server-driven.

#### Data Model Changes

**None.** The `EmailMessage` model already has `SENDING`, `SENT`, `FAILED`, `DRAFT` statuses. The `error_message` field is ready for Gmail API error details.

#### API Contract

**Post-send state machine:**

```
DRAFT ──(compose)──> SENDING ──(success)──> SENT
                          │
                          └──(failure)──> FAILED
                                          (error_message populated)
```

**Changes to `POST /api/emails/` (existing endpoint):**

The response body after save includes the email ID so the frontend can track status.

**New endpoint for send status:**

```
GET /api/emails/{id}/send-status/
```

Response:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `sending`, `sent`, `failed` |
| `error_message` | string | Present only when status=failed |
| `message_id` | string | Gmail message ID when sent |

#### Frontend Changes (`email-page.tsx`)

**Current flow:**
```
Compose Modal → handleSend → useSendEmail.mutateAsync → POST /api/emails/ → close modal
```

**New flow:**
```
Compose Modal → handleSend →
  1. Show "Sending..." state (disabled button, spinner)
  2. POST /api/emails/ → receive email ID
  3. Poll GET /api/emails/{id}/send-status/ every 2s
  4a. On SENT: close modal, show success toast, refresh email list
  4b. On FAILED: show error toast with error_message, keep modal open,
      allow "Retry" or "Save as Draft"
  5. On timeout (30s): show "Send is taking longer than expected" with
     "Check later" option
```

**Component changes:**

| Component | Change |
|-----------|--------|
| Compose Modal footer | Add `sendStatus` state machine (idle → sending → sent/failed) |
| `handleSend` | Show sending state, poll for status, handle failure |
| Email list page | After send success, refresh list to show outbound email |
| Toast system | Success toast "Email sent" / Error toast with message |

#### Celery Task Changes (`tasks.py`)

The existing `send_gmail_message` task needs these **modifications**:

1. Accept an `email_id` parameter so it can update the existing EmailMessage record
2. On success: update status to `SENT`, set `external_id` (Gmail message ID), `is_read=True`
3. On failure: update status to `FAILED`, set `error_message`
4. Create an Activity entry (type=email) on success

**Modified function signature:**
```python
@shared_task(bind=True, max_retries=2)
def send_gmail_message(
    self,
    user_id: str,
    email_id: str,
) -> dict[str, Any]:
```

The MIME construction stays the same. The task loads the EmailMessage record from DB, constructs the message from its fields, sends via Gmail API, and updates status.

#### Error Handling

| Scenario | Behavior |
|----------|----------|
| Gmail API returns 401 | Auto-refresh token; retry once. Fail if second attempt also 401. |
| Gmail API returns 403 (quota) | Retry with default_retry_delay=30. After 3 retries, mark FAILED. |
| Network timeout | Mark FAILED with error_message "Gmail API unavailable". |
| User has no Google token | Fail immediately with "No Gmail connection configured". |
| Token refresh fails | Fail with "Gmail authentication expired — reconnect". |

#### Frontend Error Display

- Inline error message below the compose body (not a toast)
- `error_message` displayed verbatim
- Action buttons: "Retry" (re-POST to same endpoint) and "Save as Draft" (update status back to DRAFT)
- Failed email appears in Sent tab with a red indicator

#### Existing Code Reused

- `send_gmail_message()` task — 85% reused (modified to accept email_id instead of raw fields)
- `EmailMessage` model with `SENDING/SENT/FAILED` statuses — fully reused
- `EmailViewSet.perform_create` — extended, not replaced
- `_refresh_google_token()` helper — fully reused
- Activity creation patterns — follow `apps/activities/` conventions

#### Implementation Order

1. Modify `send_gmail_message` to accept `email_id`, update EmailMessage record
2. Modify `EmailViewSet.perform_create` to enqueue the Celery task
3. Add `send-status` endpoint to `EmailViewSet`
4. Add Activity creation in the Celery task
5. Update the frontend `useSendEmail` hook to support status polling
6. Update the compose modal with sending/failure states
7. Add error handling UI

#### Acceptance Criteria

- [ ] Clicking "Send" in compose modal creates `SENDING` email record
- [ ] Email is sent via Gmail API within 30 seconds
- [ ] Status transitions to `SENT` or `FAILED` correctly
- [ ] Activity log entry is created for sent emails
- [ ] Gmail API failure shows clear error in the compose modal
- [ ] User can retry a failed send or save as draft
- [ ] Sent email appears in the "Sent" tab
- [ ] Emails sent from CRM appear in user's Gmail Sent folder

---

## 3. Pipeline Forecasting (P2)

### ADR-025: Pipeline Forecasting Endpoint

**Status:** Proposed
**Date:** 2026-06-30

#### Context

The reports app (`apps/reports/views.py`) already computes:
- `weighted_pipeline` (sum of deal.value × stage.probability)
- `win_rate`, `deal_velocity` (avg days per stage)
- `pipeline_value_trend` (daily values)
- `deals_by_stage`, `conversion_rate_by_stage`

These are computed in `DashboardReportView` as static snapshots. What's missing:
1. Revenue projection into future periods (quarters)
2. What-if scenario modeling ("if I close X% of stage Y deals")
3. Expected close date projections based on historical velocity
4. A dedicated endpoint separate from the dashboard

#### Decision

Create a new `ForecastView` at `GET /api/reports/forecast/` that returns multiple forecast models:

1. **Simple weighted projection** — already computed as `weighted_pipeline` in `_compute_summary`
2. **Win-rate adjusted projection** — `weighted_pipeline × historical_win_rate`
3. **Velocity-based projection** — expected close dates per deal based on avg days-in-stage
4. **What-if scenario** — parameterized via query params

#### Data Model Changes

**None.** All data is computed from existing `Deal`, `Stage`, and `Activity` models.

#### API Contract

```
GET /api/reports/forecast/
```

**Query Parameters:**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `pipeline_id` | UUID | No | all active | Filter to one pipeline |
| `quarter` | string | No | current quarter | e.g. "2026-Q3" or "current" |
| `scenario_stage` | string | No | — | Stage name for what-if |
| `scenario_close_rate` | float | No | — | Hypothetical close rate (0.0-1.0) for what-if |
| `confidence_level` | string | No | "medium" | "conservative", "medium", "optimistic" (maps to different win rate multipliers) |

**Response:**

```json
{
  "period": {
    "quarter": "2026-Q3",
    "start_date": "2026-07-01",
    "end_date": "2026-09-30"
  },
  "projections": {
    "simple_weighted": {
      "projected_revenue": 425000.00,
      "deals_in_pipeline": 28,
      "total_pipeline_value": 850000.00,
      "description": "Sum of deal.value × stage.probability for all open deals"
    },
    "win_rate_adjusted": {
      "projected_revenue": 318750.00,
      "historical_win_rate": 0.75,
      "adjustment_factor": 0.75,
      "description": "Weighted pipeline × historical win rate"
    },
    "velocity_based": {
      "projected_revenue": 385000.00,
      "expected_close_count": 12,
      "deals_with_expected_dates": 18,
      "avg_days_to_close": 45.3,
      "monthly_breakdown": [
        {"month": "2026-07", "projected_value": 120000.00, "expected_deals": 4},
        {"month": "2026-08", "projected_value": 165000.00, "expected_deals": 5},
        {"month": "2026-09", "projected_value": 100000.00, "expected_deals": 3}
      ]
    }
  },
  "scenario": null,
  "what_if": null
}
```

**What-if scenario response (when `scenario_stage` + `scenario_close_rate` are provided):**

```json
{
  "period": { ... },
  "projections": { ... },
  "what_if": {
    "stage_name": "Negotiation",
    "current_close_rate": 0.60,
    "scenario_close_rate": 0.80,
    "deals_affected": 5,
    "current_projected_value": 180000.00,
    "scenario_projected_value": 240000.00,
    "upside": 60000.00
  }
}
```

#### Computation Details

**Simple weighted projection:**
```
Σ(open_deals: deal.value × stage.probability)
```
Already computed via `_compute_summary` → `weighted_pipeline`.

**Win-rate adjusted:**
```
weighted_pipeline × historical_win_rate
```
Historical win rate = `won_count / (won_count + lost_count)` across all deals in the last 12 months.

**Velocity-based monthly breakdown:**
For each open deal with `expected_close_date`:
- Use existing `deal_velocity` avg days per stage to estimate close date if `expected_close_date` is null
- Group by month and sum projected values

For deals without `expected_close_date`:
- Estimate close date as `entered_stage_at + avg_days_in_stage` for current stage
- If deal has been in stage longer than avg, use a closer date probability

**What-if:**
```
current_value_in_stage × (scenario_close_rate / current_stage_probability)
```
Show delta between current projection and scenario projection.

**Confidence levels:**
| Level | Multiplier on win rate |
|-------|----------------------|
| conservative | × 0.8 |
| medium | × 1.0 |
| optimistic | × 1.15 |

#### Frontend Components Required

| Component | Description |
|-----------|-------------|
| `ForecastPage` | Dedicated forecasting page (or section on Reports page) |
| `ForecastSummaryCards` | 3-4 cards showing simple, adjusted, velocity projections |
| `ForecastChart` | Bar chart showing monthly projected revenue |
| `ScenarioForm` | Dropdown to select stage + slider for close rate |
| `ScenarioComparison` | Side-by-side before/after comparison |
| `QuarterSelector` | Dropdown to select forecast quarter |

The reports-page.tsx at `frontend/src/pages/reports/reports-page.tsx` can include a "Forecast" tab.

#### Existing Code Reused

- `_compute_summary` → `weighted_pipeline` — directly reused
- `_compute_deal_velocity` — directly reused
- `_compute_win_rate_by_stage` — partially reused for historical win/loss
- `_parse_date_params` — reused with quarter parsing
- Deal model with `expected_close_date` — fully reused

#### Implementation Order

1. Create `ForecastView` in `apps/reports/views.py`
2. Add `_compute_simple_weighted_forecast()`, `_compute_win_rate_adjusted()`, `_compute_velocity_forecast()`, `_compute_what_if()`
3. Add URL at `/api/reports/forecast/`
4. Add TypeScript types in `frontend/src/types/index.ts`
5. Create frontend API hook `useForecast`
6. Build UI components

#### Acceptance Criteria

- [ ] `GET /api/reports/forecast/` returns projected revenue for the current quarter
- [ ] All 3 projection models are populated (simple, win-rate, velocity)
- [ ] Monthly breakdown in velocity projection sums to total
- [ ] What-if scenario with `scenario_stage` + `scenario_close_rate` returns correct delta
- [ ] Quarter selector produces correct date range
- [ ] Frontend renders forecast cards with formatted currency values

---

## 4. Export (P2)

### ADR-026: Streaming CSV Export for Contacts, Deals, and Reports

**Status:** Proposed
**Date:** 2026-06-30

#### Context

FrontierCRM has CSV import (`apps/contacts/csv_import.py`, `apps/imports/views.py`) but **no export functionality**. Users need to download:
- Contact list as CSV (all fields, filtered by current search/segment)
- Deal list as CSV (with pipeline stage, value, owner)
- Pipeline report data as CSV/PDF

There are no PDF generation libraries or patterns in the project yet.

#### Decision

Implement CSV export as HTTP streaming CSV responses. For PDF, use a server-side Markdown-to-PDF approach (weasyprint or similar) as a future phase; for now, CSV is the primary deliverable with report data rendered as printable HTML.

#### Export Strategy

| Entity | Format | Trigger | Notes |
|--------|--------|---------|-------|
| Contacts | CSV | Download button on contacts list page | Same filters as current list |
| Deals | CSV | Download button on deals list page | Same filters + pipeline stage, owner |
| Accounts | CSV | Download button on accounts list page | Same filters |
| Pipeline Report | CSV + printable HTML | Download button on reports page | Current report data as CSV + print-friendly page |

#### Data Model Changes

**None.** Export is computed on-the-fly from existing models.

#### API Contract

**Streaming CSV endpoints (all follow same pattern):**

```
GET /api/contacts/export/csv/
GET /api/deals/export/csv/
GET /api/reports/export/csv/
```

**Query Parameters:**

For list exports, the same filter params as the corresponding list endpoint:

| Endpoint | Params |
|----------|--------|
| Contacts export | `search`, `tags`, `owner_id`, `source`, `page_size` (ignored — exports are unlimited) |
| Deals export | `search`, `status`, `pipeline_id`, `stage_id`, `owner_id`, `tags` |
| Accounts export | `search`, `industry`, `owner_id` |
| Reports export | `start_date`, `end_date`, `pipeline_id` |

**Response Headers:**

```http
Content-Type: text/csv
Content-Disposition: attachment; filename="contacts-2026-06-30.csv"
```

**Response Body:** Streaming CSV line-by-line. First row is headers.

#### CSV Column Mappings

**Contacts export:**
```
first_name,last_name,email,phone,mobile,job_title,department,
street,city,state,postal_code,country,source,tags,
account_name,owner_name,created_at,updated_at
```

**Deals export:**
```
name,value,currency,status,stage_name,pipeline_name,
probability,expected_close_date,owner_name,contact_name,
account_name,description,tags,created_at,updated_at
```

**Accounts export:**
```
name,domain,industry,description,website,phone,
address_line1,address_line2,city,state,postal_code,country,
employees_count,annual_revenue,tags,owner_name,created_at,updated_at
```

**Report export:**
```
Section,Metric,Value
Summary,Total Pipeline Value,$850,000.00
Summary,Weighted Pipeline,$425,000.00
Summary,Won Value,$320,000.00
Summary,Win Rate,75.00%
Summary,Active Deals,28
Deals by Stage,Qualified (6),$120,000.00
Deals by Stage,Proposal (8),$340,000.00
...
Deal Velocity,Qualified,14.2 days
Deal Velocity,Proposal,21.5 days
...
```

#### Backend Implementation

**Use Django's `StreamingHttpResponse`** with a generator that yields CSV rows. Use `csv.writer` with `io.StringIO` buffer per row.

**Pattern (contacts example):**
```python
class ContactExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Contact.objects.filter(tenant_id=request.user.tenant_id)
        # Apply same filters as list endpoint
        queryset = self._apply_filters(queryset, request.query_params)
        # Prefetch related data
        queryset = queryset.select_related('account')

        def stream():
            writer = csv.writer(io.StringIO())
            yield writer.writerow([
                'first_name', 'last_name', 'email', ...
            ])
            for contact in queryset.iterator(chunk_size=500):
                yield writer.writerow([
                    contact.first_name,
                    contact.last_name,
                    ...
                ])

        response = StreamingHttpResponse(
            streaming_content=stream(),
            content_type='text/csv',
        )
        response['Content-Disposition'] = (
            f'attachment; filename="contacts-{date.today().isoformat()}.csv"'
        )
        return response
```

**Batched iterator:** Use `.iterator(chunk_size=500)` to avoid loading all rows into memory. For very large exports (10K+ rows), the streaming response keeps memory constant.

#### Frontend Components

| Component | Existing/New | Details |
|-----------|-------------|---------|
| `ExportButton` | New | Reusable button component — "Export CSV" with loading state |
| `contacts-page.tsx` | Extend | Add ExportButton next to search/filter bar |
| `deals-page.tsx` | Extend | Add ExportButton next to search/filter bar |
| `reports-page.tsx` | Extend | Add ExportButton on report summary section |

**Hook:**
```typescript
function useExportCsv(endpoint: string) {
  // Fetches the CSV URL and triggers browser download
  // Returns { isExporting, exportError, exportCsv }
}
```

**Frontend download trigger:**
```typescript
async function exportCsv(endpoint: string, params: Record<string, string>) {
  const response = await apiClient.get(endpoint, {
    params,
    responseType: 'blob',
  });
  const url = URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${entity}-${today}.csv`);
  document.body.appendChild(link);
  link.click();
  URL.revokeObjectURL(url);
}
```

#### Report Export as Printable HTML

For reports, also support a print-friendly HTML view:

```
GET /api/reports/export/html/
```

Returns a styled HTML page with the report data suitable for printing or PDF via browser "Save as PDF". No server-side PDF generation in Phase 4.

#### Existing Code Reused

- `csv` standard library — basis for all exports
- `DEFAULT_DEDUP_KEYS` field sets (`CONTACT_FIELDS`, `DEAL_FIELDS`, `ACCOUNT_FIELDS`) — define export columns
- `csv_import.py` column alias maps — useful for reverse mapping
- Existing filter sets (ContactFilter, DealFilter, etc.) — applied to export querysets
- `_compute_summary` and report helpers — used for report export
- `StreamingHttpResponse` — Django built-in

#### Implementation Order

1. Create `ContactExportView`, `DealExportView`, `AccountExportView` in respective apps
2. Create `ReportExportView` in `apps/reports/views.py`
3. Register URLs (e.g., `path("export/csv/", ContactExportView.as_view(), name="contact-export-csv")`)
4. Create reusable frontend `ExportButton` component
5. Add export hook `useExportCsv` to shared API utilities
6. Place buttons on contacts, deals, and reports pages

#### Acceptance Criteria

- [ ] Export contacts CSV downloads with all fields, filtered by current search
- [ ] Export deals CSV includes pipeline stage, value, owner name
- [ ] Export accounts CSV includes all account fields
- [ ] Report export produces both CSV and printable HTML
- [ ] Large exports (10K+ rows) stream without timeout or memory spike
- [ ] CSV files open correctly in Excel and Google Sheets
- [ ] Filename includes entity name + date (e.g., `contacts-2026-06-30.csv`)

---

## Appendix: Project-wide Impact Summary

### Backend Changes

| App | New Files/Endpoints |
|-----|-------------------|
| `apps/activities/` | `TimelineView`, `TimelineSerializer`, route at `/timeline/` |
| `apps/email/` | Modify `perform_create`, modify `send_gmail_message` task, add `send-status` endpoint |
| `apps/reports/` | `ForecastView`, `ReportExportView`, forecast routes, export routes |
| `apps/contacts/` | `ContactExportView`, `AccountExportView`, export routes |
| `apps/pipelines/` | `DealExportView`, export routes |

### Frontend Changes

| Page | Changes |
|------|---------|
| `pages/activities/activity-page.tsx` | Replace or extend with timeline view |
| `pages/email/email-page.tsx` | Update compose modal with send status polling |
| `pages/reports/reports-page.tsx` | Add Forecast tab and export button |
| `pages/contacts/` | Add ExportButton |
| `pages/pipeline/` | Add ExportButton |
| `api/activities.ts` | Add `useActivityTimeline` hook |
| `api/email.ts` | Update `useSendEmail` with status polling |
| `api/reports.ts` | Add `useForecast` hook |
| `api/` | Add shared `useExportCsv` hook |
| `types/index.ts` | Add Forecast types, Export types |

### Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Gmail API rate limits on send | Medium | High | Retry with backoff; Celery auto-retries |
| Large CSV export crashes worker | Low | Medium | Streaming + iterator prevents memory issues |
| Forecast accuracy is poor | Medium | Low | Label as "projection, not guarantee" |
| Timeline query slow at scale (1M+ activities) | Low | Medium | Cursor pagination in Phase 5 |
| User has no Gmail token when sending | Low | Medium | Frontend checks connection state before compose |