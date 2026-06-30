# Phase 4 — Bulk Operations Specification

**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)
**Status:** Proposed
**Priority:** P2

---

## Table of Contents

1. [ADR-027: Bulk Operations Architecture — Async + Sync Hybrid](#1-adr-027-bulk-operations-architecture--async--sync-hybrid)
2. [Data Model: BulkJob Model](#2-data-model-bulkjob-model)
3. [API Contracts — Contacts](#3-api-contracts--contacts)
4. [API Contracts — Deals](#4-api-contracts--deals)
5. [API Contracts — Accounts](#5-api-contracts--accounts)
6. [API Contracts — BulkJob Status Endpoints](#6-api-contracts--bulkjob-status-endpoints)
7. [Frontend: BulkSelect Component](#7-frontend-bulkselect-component)
8. [Frontend: BatchActionToolbar Component](#8-frontend-batchactiontoolbar-component)
9. [Frontend: Confirmation Dialog](#9-frontend-confirmation-dialog)
10. [Frontend: Enriched Contacts API Hooks](#10-frontend-enriched-contacts-api-hooks)
11. [Progress Tracking for Async Operations](#11-progress-tracking-for-async-operations)
12. [Implementation Order](#12-implementation-order)
13. [Acceptance Criteria](#13-acceptance-criteria)
14. [Open Questions](#14-open-questions)

---

## 1. ADR-027: Bulk Operations Architecture — Async + Sync Hybrid

**Status:** Proposed
**Date:** 2026-06-30

### Context

FrontierCRM needs bulk operations on contacts, accounts, and deals. The operations include:

- **Bulk delete** — soft-delete multiple records at once
- **Bulk assign** — re-assign owner_id in bulk
- **Bulk stage change** — move multiple deals to a new pipeline stage
- **Bulk status change** — update deal status (won/lost/abandoned) in bulk
- **Bulk tag** — add/remove/replace tags on records
- **Bulk export** — streaming CSV export of selected records

The existing export views (`export_views.py`) already stream large CSV responses synchronously via `StreamingHttpResponse`. No async queue is involved — the DB scan is lazy via `.iterator()`. This works well for thousands of records.

For write operations (delete, assign, stage change, etc.), operations on <100 records should be synchronous (sub-second on most DBs). Operations on 100+ records should be async with progress tracking to avoid HTTP timeout.

### Options Considered

**Option A — Fully Async (all bulk write ops go through Celery)**

Every bulk write creates a `BulkJob` record, enqueues a Celery task, returns 202 Accepted immediately, and the frontend polls for completion.

- Pros: Consistent UX for all operations; no HTTP timeout risk; natural audit trail
- Cons: Over-engineered for <50-record operations (200ms HTTP + 500ms Celery round-trip for a 10ms DB op); adds task queue latency to quick actions; user sees a progress bar for deleting 3 contacts

**Option B — Fully Sync (all bulk write ops are synchronous)**

Every bulk write runs inline in the request. Frontend shows a spinner.

- Pros: Simple; no Celery dependency; immediate feedback
- Cons: 5,000-record bulk delete can take 10+ seconds; HTTP gateway/proxy timeouts (many reverse proxies default to 30s); poor UX for large operations with no intermediate progress

**Option C — Hybrid (sync for <100 records, async for 100+)**

The backend checks `len(ids)` and chooses the path: inline synchronous for small batches, async Celery job with `BulkJob` tracking for large batches. The frontend uses the same API contract in both cases — the response tells it whether the operation was immediate (`status: "completed"`) or needs polling (`status: "running"`).

- Pros: Fast path for common small selections; robust path for "select all 5,000 contacts"
- Cons: Dual code paths; slight complexity in the frontend branching on response status
- **Accepted** — the UX benefit of instant feedback for small selections justifies the dual path, and the response contract is unified (frontend always reads `status` from the response)

**Option D — Bulk Export is always synchronous streaming**

Export is a read-only streaming CSV. Django's `StreamingHttpResponse` handles any record count efficiently via lazy queryset iteration. No Celery needed. Already proven by existing `export_views.py`.

- Cons: No progress bar (CSV just streams)
- **Accepted** — streaming HTTP response is the standard pattern; browsers handle the download natively; progress would add complexity with no user benefit (the file appears when it's ready)

### Decision

**Hybrid of Option C + Option D:**

- **Write operations** (delete, assign, tag, stage change, status change): sync for <100 records, async Celery task for 100+. Both paths return `{status, bulk_job_id, results}`.
- **Export operations**: always synchronous streaming CSV via `StreamingHttpResponse`.

### Bulk Action Catalog

| Action | Entities | Sync Threshold | Async Required | Permission |
|---|---|---|---|---|
| `delete` | Contact, Account, Deal | < 100 | yes | `contacts.delete`, `deals.delete` |
| `assign` | Contact, Deal | < 100 | yes | `contacts.edit`, `deals.edit` |
| `change_stage` | Deal | < 100 | yes | `deals.edit` |
| `change_status` | Deal | < 100 | yes | `deals.edit` |
| `add_tag` | Contact, Account, Deal | < 100 | yes | `contacts.edit`, `deals.edit` |
| `remove_tag` | Contact, Account, Deal | < 100 | yes | `contacts.edit`, `deals.edit` |
| `replace_tags` | Contact, Account, Deal | < 100 | yes | `contacts.edit`, `deals.edit` |
| `export_csv` | Contact, Account, Deal | n/a (always streaming) | no | `contacts.view`, `deals.view` |

Permission keys refer to the RBAC Permission Registry established in ADR-026.

---

## 2. Data Model: BulkJob Model

A `BulkJob` model in `apps/core/models.py` tracks async bulk operations.

### Schema

```python
class BulkJob(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partial"  # some succeeded, some failed

    class Operation(models.TextChoices):
        DELETE = "delete", "Delete"
        ASSIGN = "assign", "Assign"
        CHANGE_STAGE = "change_stage", "Change Stage"
        CHANGE_STATUS = "change_status", "Change Status"
        ADD_TAG = "add_tag", "Add Tag"
        REMOVE_TAG = "remove_tag", "Remove Tag"
        REPLACE_TAGS = "replace_tags", "Replace Tags"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    created_by_id = models.UUIDField(db_index=True)
    operation = models.CharField(max_length=30, choices=Operation.choices)
    entity_type = models.CharField(max_length=30)  # "contact", "deal", "account"
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Query-based selection: filters that describe the selection
    filter_params = models.JSONField(default=dict, blank=True)
    # Explicit ID selection
    record_ids = models.JSONField(default=list, blank=True)
    # Operation payload (the "what to do")
    payload = models.JSONField(default=dict, blank=True)
    # Results
    total_count = models.IntegerField(null=True, blank=True)
    processed_count = models.IntegerField(null=True, blank=True)
    success_count = models.IntegerField(null=True, blank=True)
    error_count = models.IntegerField(null=True, blank=True)
    errors = models.JSONField(default=list, blank=True)  # [{id, reason}, ...]
    task_id = models.CharField(max_length=255, blank=True, default="")  # Celery task ID
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "core_bulk_job"
        indexes = [
            models.Index(fields=["tenant_id", "-created_at"]),
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["tenant_id", "created_by_id"]),
        ]
        ordering = ["-created_at"]
```

### Payload Schema by Operation

| Operation | payload keys |
|---|---|
| `delete` | `{}` (no additional params) |
| `assign` | `{owner_id: "uuid"}` |
| `change_stage` | `{stage_id: "uuid"}` |
| `change_status` | `{status: "won" / "lost" / "abandoned", close_reason?: ""}` |
| `add_tag` | `{tags: ["tag1", "tag2"]}` |
| `remove_tag` | `{tags: ["tag1", "tag2"]}` |
| `replace_tags` | `{tags: ["tag1", "tag2"]}` |

### Filter Params Schema

`filter_params` mirrors the list endpoint's query parameters so a user can say "delete all contacts matching these filters":

```json
{
  "search": "",
  "owner_id": "",
  "tags": ["tag1"],
  "created_after": "2026-01-01",
  "created_before": "2026-06-30",
  "source": ""
}
```

When `record_ids` is non-empty, `filter_params` is ignored. When `record_ids` is empty and `filter_params` is populated, the job resolves the matching records at job-start time.

### Celery Task Interface

```python
# apps/core/tasks.py
@app.task(bind=True, max_retries=3, default_retry_delay=10)
def run_bulk_job(self, bulk_job_id: str) -> dict:
    """Execute a BulkJob, updating progress as it goes."""
    ...
```

---

## 3. API Contracts — Contacts

All bulk endpoints live at `/api/contacts/bulk/<operation>/`.

### 3.1 `POST /api/contacts/bulk/delete/`

**Request:**
```json
{
  "record_ids": ["uuid1", "uuid2", ...],
  "filter_params": {}
}
```

**Response (sync, <100 records):**
```json
{
  "status": "completed",
  "bulk_job_id": "uuid",
  "total": 3,
  "success": 3,
  "errors": []
}
```

**Response (async, ≥100 records — 202 Accepted):**
```json
{
  "status": "running",
  "bulk_job_id": "uuid",
  "total": 5000,
  "success": 0,
  "errors": []
}
```

**Validation:**
- `record_ids` must contain valid UUIDs
- At least one of `record_ids` or `filter_params` must be non-empty
- Max 10,000 IDs per request (validate on input; if exceeded return 400)

**Permission required:** `contacts.delete`

### 3.2 `POST /api/contacts/bulk/assign/`

**Request:**
```json
{
  "record_ids": ["uuid1", ...],
  "filter_params": {},
  "owner_id": "target-user-uuid"
}
```

**Validation:**
- `owner_id` is required
- `owner_id` must reference an active user in the same tenant

**Permission required:** `contacts.edit`

### 3.3 `POST /api/contacts/bulk/tags/add/`

Add tags to selected contacts. Tags are unioned with existing tags (no duplicates).

**Request:**
```json
{
  "record_ids": ["uuid1", ...],
  "filter_params": {},
  "tags": ["vip", "enterprise"]
}
```

### 3.4 `POST /api/contacts/bulk/tags/remove/`

Remove tags from selected contacts.

**Request:**
```json
{
  "record_ids": ["uuid1", ...],
  "filter_params": {},
  "tags": ["vip"]
}
```

### 3.5 `POST /api/contacts/bulk/tags/replace/`

Replace all tags on selected contacts with a new set.

**Request:**
```json
{
  "record_ids": ["uuid1", ...],
  "filter_params": {},
  "tags": ["new-tag"]
}
```

### 3.6 `GET /api/contacts/bulk/export/csv/`

Streaming CSV of selected contacts. Refactors the existing `ContactExportView` to accept the same `record_ids` / `filter_params` contract as write operations.

**Query parameters (all optional):**
- `record_ids` — comma-separated UUIDs (`id1,id2,id3`)
- `search` — text search filter
- `owner_id` — filter by owner
- `tags` — comma-separated tags
- `source` — filter by source
- Plus all `ContactFilter` fields (`first_name__icontains`, etc.)

When `record_ids` is present, only those records are exported (subject to tenant scoping). When absent, the existing filter params determine the scope.

**Response:** `Content-Type: text/csv` with `Content-Disposition: attachment; filename="contacts-2026-06-30.csv"`

**Permission required:** `contacts.view`

---

## 4. API Contracts — Deals

All bulk endpoints live at `/api/deals/bulk/<operation>/`.

### 4.1 `POST /api/deals/bulk/delete/`

Same contract as contacts bulk delete.

**Permission required:** `deals.delete`

### 4.2 `POST /api/deals/bulk/assign/`

**Permission required:** `deals.edit`

### 4.3 `POST /api/deals/bulk/change-stage/`

**Request:**
```json
{
  "record_ids": ["uuid1", ...],
  "filter_params": {},
  "stage_id": "target-stage-uuid"
}
```

**Validation:**
- `stage_id` is required
- `stage_id` must belong to the same pipeline as the deals' current pipeline (or allow cross-pipeline — permit and let users move deals between pipelines via bulk operation)
- Decision: **allow cross-pipeline moves** — the user may need to move deals from one pipeline to another. Validate that `stage_id.pipeline_id` is active and belongs to the same tenant.

**Permission required:** `deals.edit`

### 4.4 `POST /api/deals/bulk/change-status/`

**Request:**
```json
{
  "record_ids": ["uuid1", ...],
  "filter_params": {},
  "status": "won",
  "close_reason": ""
}
```

**Validation:**
- `status` must be one of: `won`, `lost`, `abandoned`
- When `status` is `won` or `lost`, set `closed_at = now()`

**Permission required:** `deals.edit`

### 4.5 `POST /api/deals/bulk/tags/add/`
### 4.6 `POST /api/deals/bulk/tags/remove/`
### 4.7 `POST /api/deals/bulk/tags/replace/`

Same contracts as contacts tags operations. All require `deals.edit`.

### 4.8 `GET /api/deals/bulk/export/csv/`

Streaming CSV of selected deals. Same pattern as contacts export.

**Additional columns:** deal name, value, currency, status, stage name, pipeline name, contact name, account name, owner name, expected close date, win probability, tags, created at, updated at.

**Permission required:** `deals.view`

---

## 5. API Contracts — Accounts

All bulk endpoints live at `/api/contacts/bulk/accounts/<operation>/`.

### 5.1 `POST /api/contacts/bulk/accounts/delete/`

**Permission required:** `contacts.delete`

### 5.2 `POST /api/contacts/bulk/accounts/tags/add/`
### 5.3 `POST /api/contacts/bulk/accounts/tags/remove/`
### 5.4 `POST /api/contacts/bulk/accounts/tags/replace/`

All require `contacts.edit`.

### 5.5 `GET /api/contacts/bulk/accounts/export/csv/`

**Permission required:** `contacts.view`

Accounts do **not** get bulk assign or bulk stage/status change operations (no owner reassignment is a common use case, but it's deferred — see Open Questions).

---

## 6. API Contracts — BulkJob Status Endpoints

### 6.1 `GET /api/core/bulk-jobs/`

List recent bulk jobs for the current tenant.

**Response:**
```json
{
  "count": 1,
  "results": [
    {
      "id": "uuid",
      "operation": "delete",
      "entity_type": "contact",
      "status": "completed",
      "total_count": 5000,
      "processed_count": 5000,
      "success_count": 5000,
      "error_count": 0,
      "errors": [],
      "started_at": "2026-06-30T10:00:00Z",
      "completed_at": "2026-06-30T10:00:05Z",
      "created_at": "2026-06-30T09:59:59Z"
    }
  ]
}
```

### 6.2 `GET /api/core/bulk-jobs/{id}/`

Get status of a single job. The frontend polls this for async operations.

**Response:**
```json
{
  "id": "uuid",
  "operation": "delete",
  "entity_type": "contact",
  "status": "running",
  "total_count": 5000,
  "processed_count": 2500,
  "success_count": 2498,
  "error_count": 2,
  "errors": [
    {"id": "uuid1", "reason": "Record not found"},
    {"id": "uuid2", "reason": "Permission denied"}
  ],
  "started_at": "2026-06-30T10:00:00Z",
  "completed_at": null,
  "created_at": "2026-06-30T09:59:59Z"
}
```

**Polling interval:** Frontend polls every 2 seconds. After 30 seconds, back off to every 5 seconds. Stop polling when `status` is `completed`, `failed`, or `partial`.

### 6.3 `POST /api/core/bulk-jobs/{id}/cancel/`

Cancel a running bulk job. Sets status to `failed` with a cancellation note in `errors`. If the task is mid-execution, the Celery task checks `status` periodically and stops processing new records.

---

## 7. Frontend: BulkSelect Component

A reusable `BulkSelect` molecule that wraps a `<table>` or list and provides checkbox-based selection.

### Component Signature

```tsx
interface BulkSelectProps<T> {
  items: T[];
  itemId: (item: T) => string;
  disabled?: boolean;
  /** Optional external selected set (controlled) */
  selectedIds?: Set<string>;
  onSelectionChange?: (ids: Set<string>) => void;
  children: (renderProps: {
    selectedIds: Set<string>;
    isAllSelected: boolean;
    isIndeterminate: boolean;
    toggleOne: (id: string) => void;
    toggleAll: () => void;
    clearSelection: () => void;
    checkboxProps: (id: string) => {
      checked: boolean;
      onChange: () => void;
    };
    allCheckboxProps: {
      checked: boolean;
      indeterminate: boolean;
      onChange: () => void;
    };
  }) => React.ReactNode;
}
```

### Behavior

1. **Header checkbox** — "Select all N items on this page". Shows indeterminate state when some but not all rows are selected. Click toggles select-all/deselect-all for the current page.

2. **Row checkbox** — Leftmost cell in each row. Click toggles that row's selection.

3. **"Select all N records" banner** — When all items on the current page are selected, show a banner: "All 20 contacts on this page selected. Select all 1,247 contacts matching this filter." Clicking the banner selects all records matching the current filters across all pages (passed as `filter_params` to the bulk endpoint).

4. **Selection count badge** — In the BatchActionToolbar, show "3 selected" with a "Clear" link.

### Integration in ContactListPage

The `ContactListPage` table gains a checkbox column:

```tsx
<BulkSelect items={contacts} itemId={(c) => c.id} onSelectionChange={setSelectedIds}>
  {({ allCheckboxProps, checkboxProps, selectedIds, toggleAll }) => (
    <>
      <table>
        <thead>
          <tr>
            <th><Checkbox {...allCheckboxProps} /></th>
            <th>Name</th>
            ...
          </tr>
        </thead>
        <tbody>
          {contacts.map((contact) => (
            <tr key={contact.id}>
              <td><Checkbox {...checkboxProps(contact.id)} /></td>
              <td>{contact.full_name}</td>
              ...
            </tr>
          ))}
        </tbody>
      </table>
      {selectedIds.size > 0 && (
        <BatchActionToolbar
          selectedCount={selectedIds.size}
          totalCount={data?.count ?? 0}
          currentFilterParams={currentParams}
          entityType="contact"
          onAction={handleBulkAction}
          onClear={() => selectedIds.clear()}
        />
      )}
      {selectedIds.size === pageSize && totalCount > pageSize && (
        <SelectAllBanner
          onSelectAll={() => handleSelectAllMatching()}
          selectedOnPage={pageSize}
          totalMatching={totalCount}
        />
      )}
    </>
  )}
</BulkSelect>
```

---

## 8. Frontend: BatchActionToolbar Component

A sticky toolbar that appears at the bottom of the page when items are selected.

### Component Signature

```tsx
interface BatchAction {
  id: string;
  label: string;
  icon?: React.ReactNode;
  /** The permission key required to see/use this action */
  permission?: string;
  /** This action opens a sub-dialog for additional input */
  requiresInput?: boolean;
  /** If true, this action is async and will be polled */
  async?: boolean;
}

interface BatchActionToolbarProps {
  selectedCount: number;
  totalCount?: number;
  /** Whether selection covers all matching records (not just this page) */
  isSelectAllMatching?: boolean;
  currentFilterParams?: Record<string, string>;
  entityType: 'contact' | 'deal' | 'account';
  actions?: BatchAction[];
  onAction: (actionId: string, extraData?: Record<string, unknown>) => void;
  onClear: () => void;
}
```

### Default Actions

| Action ID | Label | Entities | Requires Dialog | Async |
|---|---|---|---|---|
| `delete` | Delete | all | yes (confirmation) | yes |
| `assign` | Change Owner | contact, deal | yes (owner picker) | yes |
| `change_stage` | Move Stage | deal | yes (stage picker) | yes |
| `change_status` | Change Status | deal | yes (status select) | yes |
| `add_tag` | Add Tags | all | yes (tag input) | yes |
| `remove_tag` | Remove Tags | all | yes (tag input) | yes |
| `export_csv` | Export CSV | all | no (immediate download) | no |

### Action Visibility

Actions are filtered by RBAC permission. The toolbar queries `useRole()` to check permissions before rendering each action button.

- `delete` — requires `{entity_type}.delete`
- `assign`, `change_stage`, `change_status`, `add_tag`, `remove_tag` — requires `{entity_type}.edit`
- `export_csv` — requires `{entity_type}.view`

### UI States

**Default:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ 3 selected (of 1,247 matching)        [Delete] [Assign] [Tags ▼]   │
│                                      [Export]                       │
│                                          [Clear selection]          │
└─────────────────────────────────────────────────────────────────────┘
```

**Action in progress (sync):**
```
┌─────────────────────────────────────────────────────────────────────┐
│ Deleting 3 contacts...                     [ spinner ]              │
└─────────────────────────────────────────────────────────────────────┘
```

**Action in progress (async):**
```
┌─────────────────────────────────────────────────────────────────────┐
│ Deleting 5,000 contacts...     ████████░░░░ 2,500/5,000 (50%)      │
│                                                    [Cancel]         │
└─────────────────────────────────────────────────────────────────────┘
```

**Completed:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ ✓ Deleted 5,000 contacts (2 errors)              [Dismiss]          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Frontend: Confirmation Dialog

### 9.1 Standard Confirmation

Used for irreversible actions (delete).

```tsx
interface BulkConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  selectedCount: number;
  isAllSelected: boolean;
  totalMatching?: number;
  confirmLabel?: string;
  variant?: 'danger' | 'default';
  onConfirm: () => void;
  onCancel: () => void;
}
```

**Example — Delete:**
```
┌──────────────────────────────────────────────────────┐
│  Delete 3 contacts?                                  │
│                                                      │
│  This action cannot be undone.                       │
│  Contacts: Chris K., Sarah L., ... +2 more           │
│                                                      │
│  [Cancel]              [Delete 3 Contacts (red)]     │
└──────────────────────────────────────────────────────┘
```

**Example — Delete (Select All Matching):**
```
┌──────────────────────────────────────────────────────┐
│  Delete 1,247 contacts?                              │
│                                                      │
│  This action cannot be undone.                       │
│  All contacts matching your current filter will      │
│  be permanently deleted.                             │
│                                                      │
│  Includes: contacts from "Enterprise" account        │
│                                                      │
│  [Cancel]              [Delete All (red)]            │
└──────────────────────────────────────────────────────┘
```

### 9.2 Action-Specific Dialogs

**Assign Owner Dialog:**
```
┌──────────────────────────────────────────────────────┐
│  Change Owner (3 contacts)                           │
│                                                      │
│  New Owner: [User Select Dropdown ▼]                 │
│                                                      │
│  [Cancel]              [Assign]                      │
└──────────────────────────────────────────────────────┘
```

**Change Stage Dialog (Deals only):**
```
┌──────────────────────────────────────────────────────┐
│  Move to Stage (3 deals)                             │
│                                                      │
│  Pipeline: [Pipeline Select ▼]                       │
│  Stage:    [Stage Select ▼]                          │
│                                                      │
│  [Cancel]              [Move]                        │
└──────────────────────────────────────────────────────┘
```

**Tag Dialog:**
```
┌──────────────────────────────────────────────────────┐
│  Add Tags (3 contacts)                               │
│                                                      │
│  Tags: [vip] [enterprise] [Add more...]              │
│                                                      │
│  [Cancel]              [Add Tags]                    │
└──────────────────────────────────────────────────────┘
```

---

## 10. Frontend: Enriched Contacts API Hooks

New TanStack Query hooks in `frontend/src/api/bulk.ts`:

```tsx
// ── Bulk Operations ──

export function useBulkDelete(entity: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkPayload) =>
      apiClient.post(`/contacts/bulk/delete/`, payload),
    onSuccess: (res) => {
      if (res.data.status === 'completed') {
        qc.invalidateQueries({ queryKey: [entity] });
      }
    },
  });
}

export function useBulkAssign(entity: string) { ... }
export function useBulkChangeStage() { ... }
export function useBulkChangeStatus() { ... }
export function useBulkAddTag(entity: string) { ... }
export function useBulkRemoveTag(entity: string) { ... }
export function useBulkReplaceTags(entity: string) { ... }

// ── Bulk Job Polling ──

export function useBulkJob(jobId: string | null) {
  return useQuery({
    queryKey: ['bulk-job', jobId],
    queryFn: () => apiClient.get<BulkJob>(`/core/bulk-jobs/${jobId}/`).then((r) => r.data),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'partial') {
        return false; // stop polling
      }
      // Start at 2s, back off to 5s after 30s
      const elapsed = Date.now() - new Date(data.started_at).getTime();
      return elapsed > 30000 ? 5000 : 2000;
    },
  });
}

// ── Bulk Export ──

export function useBulkExportUrl(
  entity: string,
  params: Record<string, string>,
  selectedIds?: string[],
) {
  const searchParams = new URLSearchParams(params);
  if (selectedIds?.length) {
    searchParams.set('record_ids', selectedIds.join(','));
  }
  return {
    url: `/contacts/bulk/export/csv/?${searchParams.toString()}`,
    filename: `${entity}s.csv`,
  };
}
```

### Frontend Types (add to `frontend/src/types/index.ts`)

```tsx
export type BulkOperation = 'delete' | 'assign' | 'change_stage' | 'change_status' | 'add_tag' | 'remove_tag' | 'replace_tags';

export type BulkJobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'partial';

export interface BulkPayload {
  record_ids?: string[];
  filter_params?: Record<string, string>;
  owner_id?: string;
  stage_id?: string;
  status?: string;
  close_reason?: string;
  tags?: string[];
}

export interface BulkJob {
  id: string;
  operation: BulkOperation;
  entity_type: string;
  status: BulkJobStatus;
  total_count: number;
  processed_count: number;
  success_count: number;
  error_count: number;
  errors: { id: string; reason: string }[];
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface BulkResponse {
  status: BulkJobStatus;
  bulk_job_id: string;
  total: number;
  success: number;
  errors: { id: string; reason: string }[];
}
```

---

## 11. Progress Tracking for Async Operations

### Flow Diagram

```
User selects 5,000 contacts and clicks "Delete"
        │
        ▼
Frontend POST /api/contacts/bulk/delete/
        │
        ▼
Backend creates BulkJob (status=pending), enqueues Celery task
        │
        ▼
Response: 202 {status: "running", bulk_job_id: "uuid", total: 5000}
        │
        ▼
Frontend starts polling GET /api/core/bulk-jobs/{uuid}/ every 2s
        │
        ▼
[Async] Celery task runs:
  - Sets status=running
  - Iterates records in chunks (500 at a time)
  - Updates processed_count, success_count, error_count
  - On completion: status=completed (or failed, or partial)
        │
        ▼
Frontend poll detects status=completed
  - Shows success toast: "Deleted 5,000 contacts"
  - Invalidates list query → table refreshes
  - Clears selection
```

### Celery Task Pseudocode

```python
@app.task(bind=True)
def run_bulk_job(self, bulk_job_id: str):
    from .models import BulkJob

    job = BulkJob.objects.get(id=bulk_job_id)
    job.status = BulkJob.Status.RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    # Resolve records
    ids = resolve_record_ids(job)
    job.total_count = len(ids)
    job.save(update_fields=["total_count"])

    success = 0
    errors = []

    for chunk in chunked(ids, 500):
        # Check if cancelled
        job.refresh_from_db(fields=["status"])
        if job.status == BulkJob.Status.FAILED:
            break  # cancelled mid-execution

        for record_id in chunk:
            try:
                execute_operation(job, record_id)
                success += 1
            except Exception as e:
                errors.append({"id": str(record_id), "reason": str(e)})

        # Update progress
        BulkJob.objects.filter(id=bulk_job_id).update(
            processed_count=F("processed_count") + len(chunk),
            success_count=F("success_count") + success,
            error_count=F("error_count") + len(errors) - success,
            errors=job.errors + errors,
        )
        success = 0
        errors = []

    # Final status
    final_status = (
        BulkJob.Status.COMPLETED if job.error_count == 0
        else BulkJob.Status.PARTIAL if job.success_count > 0
        else BulkJob.Status.FAILED
    )
    BulkJob.objects.filter(id=bulk_job_id).update(
        status=final_status,
        completed_at=timezone.now(),
    )
```

### Progress Bar Component

```tsx
interface BulkProgressBarProps {
  processed: number;
  total: number;
  status: BulkJobStatus;
}

function BulkProgressBar({ processed, total, status }: BulkProgressBarProps) {
  const pct = total > 0 ? Math.round((processed / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <div className="h-2 w-48 overflow-hidden rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
        <div
          className="h-full rounded-full bg-brand-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-text-secondary dark:text-dark-text-secondary">
        {processed}/{total} ({pct}%)
      </span>
    </div>
  );
}
```

---

## 12. Implementation Order

### Phase 1: Backend Foundation (Builder)

| Step | Description | Est. Effort |
|---|---|---|
| 1.1 | Create `BulkJob` model + migration | 0.5h |
| 1.2 | Create `apps/core/tasks.py` with `run_bulk_job` Celery task | 1h |
| 1.3 | Implement `BulkJobViewSet` (list, retrieve, cancel) | 1h |
| 1.4 | Implement bulk delete endpoint for contacts | 1h |
| 1.5 | Implement bulk assign endpoint for contacts | 1h |
| 1.6 | Implement bulk tag endpoints for contacts | 1h |
| 1.7 | Refactor contact export to accept `record_ids` | 0.5h |
| 1.8 | Implement deal bulk endpoints (delete, assign, stage, status, tags) | 2h |
| 1.9 | Implement account bulk endpoints (delete, tags) | 1h |
| 1.10 | Register URL routes | 0.5h |

### Phase 2: Frontend Components (Builder)

| Step | Description | Est. Effort |
|---|---|---|
| 2.1 | Create `BulkSelect` component | 2h |
| 2.2 | Create `BatchActionToolbar` component | 2h |
| 2.3 | Create `BulkConfirmDialog` component | 1h |
| 2.4 | Create action-specific dialogs (Assign, Stage, Tags) | 2h |
| 2.5 | Create `BulkProgressBar` component | 0.5h |
| 2.6 | Create `SelectAllBanner` component | 0.5h |

### Phase 3: Integration (Builder)

| Step | Description | Est. Effort |
|---|---|---|
| 3.1 | Add bulk API hooks (`frontend/src/api/bulk.ts`) | 1h |
| 3.2 | Add bulk types to `frontend/src/types/index.ts` | 0.5h |
| 3.3 | Integrate `BulkSelect` into `ContactListPage` | 2h |
| 3.4 | Integrate `BulkSelect` into pipeline page's deal list view | 2h |
| 3.5 | Wire up async polling in the toolbar | 1h |
| 3.6 | Wire up bulk export download | 0.5h |

### Phase 4: Polish (Builder + Prober)

| Step | Description | Est. Effort |
|---|---|---|
| 4.1 | Backend tests for bulk endpoints | 2h |
| 4.2 | Frontend tests for bulk components | 2h |
| 4.3 | RBAC permission integration (bulk actions respect role permissions) | 0.5h |
| 4.4 | Error handling and edge cases | 1h |
| 4.5 | Storybook / Playwright for bulk UX flows | 1h |

---

## 13. Acceptance Criteria

1. **Single-page selection:** User can select individual contacts/deals via checkboxes on a list page. Header checkbox toggles all items on the current page.

2. **Select-all matching:** When all items on the current page are selected, a banner appears offering to select all items matching the current filter across all pages.

3. **Sync fast path:** Bulk operations on <100 selected records complete synchronously. The frontend shows a brief spinner and the table refreshes immediately.

4. **Async slow path:** Bulk operations on ≥100 records return immediately with a `running` status. A progress bar appears in the toolbar and updates every ~2 seconds as the Celery task progresses.

5. **Cancel:** Users can cancel a running bulk operation. Already-processed records remain changed; unprocessed records are not changed.

6. **Partial success:** If some records succeed and some fail, the job completes with status `partial`. Errors are listed in the response and shown in the UI.

7. **Bulk export:** Selected records can be exported as CSV. The download streams synchronously. When no records are selected, the existing "export all" behavior is preserved.

8. **Permission enforcement:** Bulk actions respect RBAC. A user without `contacts.delete` permission cannot see or use the bulk delete action on contacts.

9. **Edge cases:**
   - Empty selection (no `record_ids` and no `filter_params`) → 400 error
   - Invalid UUIDs in `record_ids` → 400 error
   - Non-existent owner/stage IDs → 400 error
   - Deals moved to a stage from a different pipeline → allowed, tenant-checked
   - Concurrent operations on overlapping records → each operation succeeds independently (last-write-wins)
   - 10,000+ IDs → rejected at input validation level

---

## 14. Open Questions

1. **Account bulk assign:** Should accounts get bulk owner reassignment? Current scope says no — it's primarily a contacts/deals operation. Add as P3 if demand appears.

2. **Activity logging:** Should each bulk operation create individual `Activity` records for each affected entity, or one aggregated Activity? Decision: **one aggregated Activity** per bulk job to avoid event spam. The activity metadata includes the `bulk_job_id` for traceability.

3. **UI location for accounts:** Should accounts get a dedicated list page with bulk operations, or is batch account management only needed from the contact detail page's "linked accounts" section? Decision: **deferred** — accounts are managed individually for now; bulk operations exist on the API but no dedicated page integration is planned.

4. **Recovery from failed Celery:** If Celery is down when an async bulk request arrives, the backend creates the BulkJob (status=pending) and returns 202, but the task never runs. Should there be a heartbeat monitor that marks stale `pending` jobs as failed? Decision: **yes** — a periodic Celery beat task (`check_stale_bulk_jobs`) runs every 5 minutes and fails jobs that have been `pending` for > 10 minutes.

5. **Export format options:** Should bulk export support formats beyond CSV (XLSX, PDF)? Current scope is CSV-only. Add as P3.

6. **Undo:** Should bulk operations be undoable? Decision: **no** — add soft-delete support and activity logging for traceability, but bulk undo is out of scope.
