# Phase 4 — Onboarding Flow Specification

**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)
**Status:** Draft
**Priority:** P3

---

## Table of Contents

1. [ADR-026: Onboarding Architecture](#1-adr-026-onboarding-architecture)
2. [Data Model](#2-data-model)
3. [API Contracts](#3-api-contracts)
4. [State Machine](#4-state-machine)
5. [Frontend Component Tree](#5-frontend-component-tree)
6. [Onboarding Steps Detail](#6-onboarding-steps-detail)
7. [Settings — Revisit Wizard](#7-settings--revisit-wizard)
8. [Existing Code to Reuse / Modify](#8-existing-code-to-reuse--modify)
9. [Implementation Order](#9-implementation-order)
10. [Acceptance Criteria](#10-acceptance-criteria)

---

## 1. ADR-026: Onboarding Architecture

**Status:** Proposed
**Date:** 2026-06-30

### Context

FrontierCRM has no onboarding flow. After signup, users land on a new-tenant dashboard with seed demo data (17 deals, 12 contacts) but no guided setup. New tenants have:

- An auto-created "Everyone" team
- An auto-created "Admin" role
- No pipeline stages configured (pipeline defaults exist but are generic)
- No email sync connected
- No team members beyond the creator

The User model already has `is_onboarded` (bool) and `onboarded_at` (datetime) fields. The router already has a `/onboarding` route stubbed with an `OnboardingPage` import that does not exist yet.

The scope is a P3 guided wizard — 5 steps (Company Setup, Invite Team, Import Data, Connect Email, Pipeline Stages) plus a "Done" screen. Users should be able to skip any step, return to incomplete steps from Settings, and never see the wizard again once completed.

### Decision

1. **No new onboarding model.** Store per-step completion state in `Tenant.settings` (JSONField) under a `onboarding` key. The `User.is_onboarded` boolean marks overall completion. This avoids a new DB table for a finite, per-tenant state.

2. **Onboarding routes live in the `accounts` app.** The `PATCH /api/accounts/onboarding/progress/` endpoint updates step state and optionally marks onboarding complete. This keeps onboarding close to the user lifecycle in `apps/accounts/` rather than creating a new app.

3. **Frontend guard, not backend.** The frontend checks `user.is_onboarded` after login/signup and redirects to `/onboarding` if false. The backend does not enforce a gated state — authenticated users can access any other page even if un-onboarded (they just lose the wizard prompt on next login).

4. **Wizard as a page, not a modal.** Use `frontend/src/pages/onboarding/` with a dedicated route (`/onboarding`). The wizard takes the full viewport (no sidebar, no topbar) so the user focuses on setup. A separate `OnboardingLayout` component renders without the `AppLayout` shell.

5. **Seed demo data is untouched.** The 17 deals and 12 contacts remain as contextual samples. Onboarding steps run alongside them — they are not a prerequisite for seeing the dashboard.

6. **Skip is always available.** Every step has a visible "Skip" link. Skipped steps never re-prompt on the next login. Steps can be re-attempted from Settings > Getting Started.

7. **Pipeline quick config is a single-screen selector.** Instead of a full pipeline CRUD UI, present a dropdown of 3 common templates (Sales, SaaS Sales, Recruitment) plus "Start from scratch". Selecting a template pre-populates stages.

### Rejected Alternatives

1. **Dedicated `Onboarding` model with per-step flags** — rejected. The `Tenant.settings` JSONField is sufficient for 5 booleans. A dedicated model adds migration + serialization overhead for no query benefit at this scale. If onboarding grows to 20+ steps per user, revisit with a model.

2. **Backend redirect (302 to /onboarding)** — rejected. The backend is stateless after JWT auth; the frontend handles routing.

3. **Onboarding as a modal overlay on the dashboard** — rejected. A full-viewport wizard avoids layout complexity (no sidebar clipping, no responsive issues with the step indicator) and matches the pattern users expect from SaaS products (Linear, Notion, Stripe).

4. **Cancel/resume with persistence** — rejected for this phase. On first login the user sees the wizard once. If they close the tab, next login redirects them to the dashboard (already `is_onboarded=false`). Revisit the wizard from Settings. This keeps the auth flow simple: after signup → immediately show wizard.

5. **Per-user onboarding state** — rejected. The initial tenant setup (company info, pipeline) is tenant-wide. Per-user steps (like "complete your profile") are simpler and can be driven by User model fields directly. Tenant settings is the right place for tenant-wide setup flags.

### Consequences

- `Tenant.settings` grows a `onboarding` key with step flags.
- `User.is_onboarded` is set to `True` when the final "Done" button is clicked.
- The `AppLayout` component must be conditionally replaced by `OnboardingLayout` for the `/onboarding` route.
- New frontend directory: `frontend/src/pages/onboarding/`.

---

## 2. Data Model

**No new database tables.** All changes use existing fields.

### Tenant.settings.onboarding

```json
{
  "onboarding": {
    "company_done": true,
    "invite_done": true,
    "import_done": false,
    "email_done": false,
    "pipeline_done": true,
    "skipped_steps": ["import", "email"]
  }
}
```

| Key | Type | Description |
|-----|------|-------------|
| `company_done` | bool | Company name, logo, industry saved |
| `invite_done` | bool | At least one invite sent or skipped |
| `import_done` | bool | CSV import completed or skipped |
| `email_done` | bool | Gmail OAuth connected or skipped |
| `pipeline_done` | bool | Pipeline template selected or skipped |
| `skipped_steps` | string[] | Array of step keys that were explicitly skipped |

### User.is_onboarded

Existing field, currently unused. Set to `True` when the user clicks "Finish" on the last step. Never reset — even if steps are later revisited from Settings, `is_onboarded` stays `True`.

### Company info on Tenant

Existing `Tenant.name` (set from signup `organization_name` or `email's Organization`).
Existing `Tenant.logo_url` can be set during the Company Setup step.
Add an `industry` field to Tenant:

```python
# apps/teams/models.py — add to Tenant model
industry = models.CharField(max_length=100, blank=True, default="")
```

This is the **only schema change** for this phase. The industry field is used for pipeline template selection (Sales vs Recruiting vs Real Estate etc.) and later for reporting benchmarks.

### Migration Summary

| Migration | App | Description |
|-----------|-----|-------------|
| `teams.NNNN_tenant_industry` | teams | Add `Tenant.industry` (CharField, blank, max=100) |

---

## 3. API Contracts

All endpoints are under `api/accounts/onboarding/` — a new URL entry in `apps/accounts/urls.py`.

### GET /api/accounts/onboarding/status/

Get the current onboarding state for the user's tenant.

**Authentication:** JWT (IsAuthenticated)
**Response:**

```json
{
  "is_onboarded": false,
  "company_done": false,
  "invite_done": false,
  "import_done": false,
  "email_done": false,
  "pipeline_done": false,
  "skipped_steps": [],
  "tenant": {
    "name": "Acme Corp",
    "logo_url": "",
    "industry": ""
  }
}
```

---

### PATCH /api/accounts/onboarding/progress/

Update onboarding progress for one or more steps.

**Authentication:** JWT (IsAuthenticated)

**Request body (partial — send only changed fields):**

```json
{
  "company_done": true,
  "company": {
    "name": "Acme Corp",
    "logo_url": "https://...",
    "industry": "technology"
  },
  "pipeline_template": "sales"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_done` | bool | No | Mark company step done |
| `company` | object | No | Company setup payload (see below) |
| `invite_done` | bool | No | Mark invite step done |
| `import_done` | bool | No | Mark import step done |
| `email_done` | bool | No | Mark email step done (handled by OAuth callback) |
| `pipeline_done` | bool | No | Mark pipeline step done |
| `pipeline_template` | string | No | One of: `sales`, `saas`, `recruiting`, `custom` |
| `mark_complete` | bool | No | Set `true` to mark onboarding fully complete |
| `skip_step` | string | No | Step key to skip (e.g. `"import"`, `"email"`) |

`company` object when updating company info:

```json
{
  "name": "Acme Corp",
  "logo_url": "https://...",
  "industry": "technology"
}
```

**Response:**

```json
{
  "is_onboarded": true,
  "company_done": true,
  "invite_done": true,
  "import_done": false,
  "email_done": false,
  "pipeline_done": true,
  "skipped_steps": ["import", "email"],
  "tenant": {
    "name": "Acme Corp",
    "logo_url": "https://...",
    "industry": "technology"
  }
}
```

**Behavior:**

1. When `company` is provided, updates `Tenant.name`, `Tenant.logo_url`, and `Tenant.industry`.
2. When `pipeline_template` is provided and `pipeline_done` is not already set, auto-creates pipeline stages from the selected template. See section 6.5 for template definitions.
3. When `mark_complete=true`, sets `User.is_onboarded=True` and `User.onboarded_at=now()`. All incomplete steps are auto-skipped.
4. When `skip_step` is provided, adds the step key to `skipped_steps` and sets the corresponding `{step}_done=true`.

---

### POST /api/accounts/onboarding/reset/

Reset onboarding state (returns wizard to "not started").

**Authentication:** JWT (IsAuthenticated)
**Purpose:** Allows re-running the wizard from Settings.

**Response:**

```json
{
  "status": "reset"
}
```

**Behavior:**

1. Clears `Tenant.settings.onboarding` key.
2. Sets `User.is_onboarded=False` and `User.onboarded_at=None`.
3. Does NOT delete any data created during original onboarding (invites sent, pipeline created, emails connected — those persist).

---

### URL Registration

Add two new paths to `apps/accounts/urls.py`:

```python
from django.urls import path

from . import views
from .onboarding_views import OnboardingStatusView, OnboardingProgressView, OnboardingResetView

urlpatterns = [
    path("me/", views.me_view, name="account-me"),
    path("onboarding/status/", OnboardingStatusView.as_view(), name="onboarding-status"),
    path("onboarding/progress/", OnboardingProgressView.as_view(), name="onboarding-progress"),
    path("onboarding/reset/", OnboardingResetView.as_view(), name="onboarding-reset"),
]
```

Views live in a new `apps/accounts/onboarding_views.py` file to keep the auth views clean.

---

## 4. State Machine

### Transition Diagram

```
SIGNUP ──► ONBOARDING_PENDING ──► (wizard shown)
                │                        │
                ├── Company Setup ───────┤ (skip: ✓)
                ├── Invite Team ─────────┤ (skip: ✓)
                ├── Import Data ─────────┤ (skip: ✓)
                ├── Connect Email ───────┤ (skip: ✓)
                ├── Pipeline Stages ─────┤ (skip: ✓)
                │                        │
                └── Done / Finish ───────┘
                         │
                         ▼
                is_onboarded = True
                   ──► DASHBOARD
```

### States

| State | Condition | UI Behaviour |
|-------|-----------|-------------|
| `ONBOARDING_PENDING` | `!user.is_onboarded` | Redirect to `/onboarding` on login |
| `ONBOARDING_ACTIVE` | In-progress wizard | Full-page wizard, no sidebar |
| `ONBOARDING_COMPLETE` | `user.is_onboarded` | Normal app (sidebar, dashboard) |
| `ONBOARDING_REVISIT` | From Settings | Wizard with "Update" instead of "Next" |

### Guard Logic (Frontend)

In `AppLayout.tsx`:

```tsx
// After auth check and before rendering the app shell:
if (!user?.is_onboarded && location.pathname !== '/onboarding') {
  return <Navigate to="/onboarding" replace />;
}
```

This guard runs only on the `AppLayout` route. The `/onboarding` route must use a separate layout (`OnboardingLayout`) that does not include this guard.

### Skip Rules

- Skipping a step records it in `skipped_steps` and marks that step done.
- Skipped steps show as skipped (not greyed out) on the step indicator if revisited.
- The Finish button is always enabled regardless of which steps are done or skipped.

---

## 5. Frontend Component Tree

### Route Structure

```
/onboarding           → OnboardingLayout > OnboardingWizard (active step)
```

The router already has `OnboardingPage` imported. Rename the import target to `OnboardingWizard` or create the page component at `frontend/src/pages/onboarding/index.tsx`.

### Layout

Introduce `OnboardingLayout` — a full-viewport layout without sidebar or topbar:

```
OnboardingLayout
├── <main class="min-h-screen flex flex-col">
│   ├── Top bar (minimal — step indicator only)
│   │   ├── FrontierCRM logo (left)
│   │   ├── StepIndicator (center)
│   │   └── Close / Exit → dashboard (right)
│   └── Wizard content (centered, max-w-2xl)
│       └── OnboardingWizard
│           ├── StepRenderer (switches on current_step_index)
│           └── NavigationButtons (Back / Next / Skip / Finish)
```

### Component Tree

```
pages/onboarding/
├── index.tsx                         ← OnboardingPage (router entry point)
├── components/
│   ├── OnboardingLayout.tsx          ← Layout without sidebar
│   ├── OnboardingWizard.tsx          ← Wizard state machine controller
│   ├── StepIndicator.tsx             ← Horizontal step progress bar
│   ├── NavigationButtons.tsx         ← Back / Next / Skip / Finish
│   └── steps/
│       ├── CompanySetupStep.tsx      ← Step 1
│       ├── InviteTeamStep.tsx        ← Step 2
│       ├── ImportDataStep.tsx        ← Step 3
│       ├── ConnectEmailStep.tsx      ← Step 4
│       ├── PipelineSetupStep.tsx     ← Step 5
│       └── DoneStep.tsx              ← Final screen
├── hooks/
│   ├── useOnboarding.ts              ← API hook (GET status, PATCH progress)
│   └── useOnboardingGuard.ts         ← Redirect guard for AppLayout
└── types.ts                          ← OnboardingStep, OnboardingStatus, etc.
```

### Key Components

#### OnboardingLayout.tsx

```
┌─────────────────────────────────────────────────────┐
│ [Logo]     Step 1 · Step 2 · Step 3 · Step 4 · Step 5   [✕] │
├─────────────────────────────────────────────────────┤
│                                                       │
│                     (step content)                    │
│                                                       │
│                                                       │
│     [Back]                  [Skip]  [Next/Finish]     │
└─────────────────────────────────────────────────────┘
```

- Uses no sidebar or topbar from AppLayout.
- Centered card-like container (max-w-2xl).
- Exit (✕) navigates to `/dashboard` without marking things complete.

#### StepIndicator.tsx

Horizontal, numbered dots with labels:

```
◉ —— ◉ —— ◉ —— ◉ —— ◉
Company  Invite  Import  Email  Pipeline
```

- Completed steps: filled circle (brand-500).
- Current step: outlined with brand ring.
- Skipped steps: grey with strikethrough text.
- Future steps: grey outline.
- Clicking a completed step returns to that step (allows revisiting within the wizard).

#### NavigationButtons.tsx

- First step: "Back" is hidden.
- Last step before Done: shows "Finish" instead of "Next".
- Every step: visible "Skip" link.
- "Finish" trigger: `PATCH /api/accounts/onboarding/progress/ { mark_complete: true }`

#### OnboardingWizard.tsx

State machine:

```tsx
const [currentStep, setCurrentStep] = useState(0);
const [status, setStatus] = useState<OnboardingStatus>(initialStatus);

async function handleNext() {
  // Save current step progress
  await saveStepProgress(currentStep);
  // Advance
  if (currentStep < STEPS.length - 1) {
    setCurrentStep(currentStep + 1);
  }
}

async function handleSkip(stepKey: string) {
  await api.patch('/accounts/onboarding/progress/', { skip_step: stepKey });
  setStatus(prev => ({ ...prev, [stepKey]: true, skipped_steps: [...prev.skipped_steps, stepKey] }));
  if (currentStep < STEPS.length - 1) setCurrentStep(currentStep + 1);
}

async function handleFinish() {
  await api.patch('/accounts/onboarding/progress/', { mark_complete: true });
  // Auth store updates user.is_onboarded → triggers redirect to dashboard
  setUser({ ...user, is_onboarded: true });
}
```

---

## 6. Onboarding Steps Detail

### 6.1 Step 1 — Company Setup

**Purpose:** Let the user customise their tenant name, upload a logo, and select industry.

**UI Elements:**

- Company name (text input, pre-filled from signup's `organization_name`).
- Logo upload (drag-and-drop or file picker → calls existing file upload API → updates `Tenant.logo_url`).
- Industry (dropdown: Technology, Financial Services, Healthcare, Real Estate, Recruitment, Media, Education, Other).
- Optional: "Company website" (text input, stored in `Tenant.settings.company_website`).

**Validation:** Company name is required. Industry is recommended but not required.

**Save behaviour:** `PATCH /api/accounts/onboarding/progress/` with:
```json
{
  "company": {
    "name": "Acme Corp",
    "logo_url": "https://cdn.frontiercrm.com/logos/uuid.png",
    "industry": "technology"
  },
  "company_done": true
}
```

**Skip:** Available. Company name defaults to the signup value.

### 6.2 Step 2 — Invite Team Members

**Purpose:** Add colleagues to the CRM.

**UI Elements:**

- Email input field + "Add" button (repeating list of email chips).
- Role selector per invite (default: "Member").
- "Send Invites" button.
- Optional text: "Invite by email — they'll get a magic link to join."

**Existing code reused:** `POST /api/teams/memberships/invite/` endpoint in `apps/teams/views.py` — `MembershipViewSet.invite`.

**Flow:**

1. User types email → clicks Add → email appears as a chip.
2. User adds 1–10 emails.
3. Click "Send Invites" → `POST /api/teams/memberships/invite/` for each email.
4. On success: mark step done.

**Skip:** Visible text: "You can invite team members later from Settings." Skipping does not send invites.

### 6.3 Step 3 — Import Data (Link to CSV)

**Purpose:** Point users to the CSV import feature and offer a quick "Import demo data" button.

**UI Elements:**

- Info card: "Import your contacts and deals from a CSV file."
- Two action buttons:
  - "Import CSV" → navigates to `/imports` (existing CSV import page).
  - "Skip — I'll import later"
- Optional: "Import demo data" button that calls existing seed data endpoint (spike: does one exist?).

**Existing code reused:** The `imports` app at `apps/imports/` with its CSV preview and confirmation flow.

**Note:** This step does NOT embed the CSV upload UI. It's a navigational step that links to the existing import flow and marks itself done when the user confirms they're satisfied, or when they skip.

**Skip:** Primary action for this step if the user doesn't want to import. Acknowledged with: "No data yet? No problem — start by adding deals manually from the Pipeline page."

### 6.4 Step 4 — Connect Email (Gmail OAuth)

**Purpose:** Connect the user's Gmail account to enable email sync and compose.

**UI Elements:**

- Info card: "Connect your Gmail to sync emails with FrontierCRM."
- "Connect Gmail" button → triggers existing Google OAuth flow.
- On success: back to wizard, step marked done.
- "Skip" link available.

**Existing code reused:**

- `GET /api/auth/google/init/` — returns OAuth authorization URL.
- `POST /api/auth/google/callback/` — exchanges code for tokens.

**Flow:**

1. User clicks "Connect Gmail" → opens Google OAuth popup or redirect.
2. After successful auth, Google callback fires → user lands back in the app.
3. The OAuth callback sets a query param (`?onboarding=true`) so the frontend redirects back to `/onboarding` instead of `/dashboard`.
4. Step 4's completion is detected by checking `SyncConnection` records for a `gmail` provider.

**Skip:** Available. "Skip — I'll connect email later from Settings."

### 6.5 Step 5 — Pipeline Setup (Quick Config)

**Purpose:** Let the user choose a pipeline template or define stages from scratch.

**UI Elements:**

- Prompt: "Choose a pipeline that matches your sales process."
- Card selector with 4 options:
  - **Sales Pipeline** — 5 stages: Lead → Qualified → Proposal → Negotiation → Closed Won
  - **SaaS Sales** — 4 stages: Trial → Demo → Negotiation → Closed
  - **Recruitment** — 5 stages: Sourced → Screening → Interview → Offer → Hired
  - **Custom** — opens Stage Editor with 3 default stages (Lead → Qualified → Closed), user can rename/add/remove
- Each template card shows: name, stage count, and stage names.
- "Custom" selected: expandable inline editor below the cards.

**Backend behaviour:**

```python
PIPELINE_TEMPLATES = {
    "sales": [
        {"name": "Lead", "order": 0, "probability": 10},
        {"name": "Qualified", "order": 1, "probability": 25},
        {"name": "Proposal", "order": 2, "probability": 50},
        {"name": "Negotiation", "order": 3, "probability": 75},
        {"name": "Closed Won", "order": 4, "probability": 100},
    ],
    "saas": [
        {"name": "Trial", "order": 0, "probability": 10},
        {"name": "Demo", "order": 1, "probability": 30},
        {"name": "Negotiation", "order": 2, "probability": 60},
        {"name": "Closed", "order": 3, "probability": 100},
    ],
    "recruiting": [
        {"name": "Sourced", "order": 0, "probability": 5},
        {"name": "Screening", "order": 1, "probability": 20},
        {"name": "Interview", "order": 2, "probability": 50},
        {"name": "Offer", "order": 3, "probability": 80},
        {"name": "Hired", "order": 4, "probability": 100},
    ],
}
```

On save with `pipeline_template=...`:
1. Check if a default pipeline already exists. If yes, skip creation.
2. Create a `Pipeline` with `name={template_name} Pipeline`, `is_default=True`.
3. Create `Stage` records from the template (pipeline color defaults: `#6366f1`).
4. Set `pipeline_done=True`.

Custom pipeline: the frontend sends an array of stage objects, and the backend creates the stages.

**Skip:** Available. Selects a generic default pipeline (the one that may already exist) and continues.

### 6.6 Step 6 — Done

**Purpose:** Congratulate the user and transition to the app.

**UI Elements:**

- Large checkmark animation (CSS transition: scale + fade).
- Heading: "You're all set!"
- Subtitle: "Explore FrontierCRM and start managing your pipeline."
- Optional summary: bullet list of what was set up (company, team size, email status, pipeline).
- "Go to Dashboard" button.

**Actions on click:**

1. `PATCH /api/accounts/onboarding/progress/ { mark_complete: true }`
2. Auth store: `setUser({ ...user, is_onboarded: true })`
3. React Router: `navigate('/dashboard')`
4. AppLayout guard detects `is_onboarded === true` and allows rendering.

---

## 7. Settings — Revisit Wizard

### Entry Point

Settings page (`/settings`) adds a new section: "Getting Started"

```
Getting Started
┌────────────────────────────────────────────────┐
│ Onboarding wizard   [Resume / Re-run]          │
│ Complete your initial CRM setup or revisit     │
│ any steps you skipped.                         │
└────────────────────────────────────────────────┘
```

### Resume vs Re-run

| State | Button Label | Behaviour |
|-------|-------------|-----------|
| `is_onboarded=false`, steps incomplete | "Continue Setup" | Navigate to `/onboarding`, wizard resumes at first incomplete step |
| `is_onboarded=true` | "Review Setup" | Navigate to `/onboarding`, wizard opens in read-only/review mode with "Edit" button per section |

### Review Mode

When `is_onboarded=true` and user re-enters via Settings:
- Step indicator shows all steps as completed or skipped.
- Clicking a step shows a read-only summary of what was configured.
- Each step has an "Edit" button that enables editing for that step only.
- Changes save via the existing `PATCH /api/accounts/onboarding/progress/` endpoint.
- No guard redirect — the user stays in the wizard view until they click "Back to Settings".

### URL

Settings entry: `/settings` → "Getting Started" section → `/onboarding?mode=review`

The `?mode=review` query param is read by `OnboardingWizard` which selects the review flow.

---

## 8. Existing Code to Reuse / Modify

### Backend

| File | What to do |
|------|-----------|
| `apps/accounts/models.py` | Already has `is_onboarded`, `onboarded_at` — no change. |
| `apps/accounts/urls.py` | Add 3 new onboarding routes. |
| `apps/accounts/onboarding_views.py` | **NEW** — `OnboardingStatusView`, `OnboardingProgressView`, `OnboardingResetView`. |
| `apps/accounts/auth.py` | No change — onboarding is not auth. |
| `apps/accounts/views.py` | No change — me_view already returns `is_onboarded`. |
| `apps/teams/models.py` | Add `Tenant.industry` field. Migration: `teams.NNNN_tenant_industry`. |
| `apps/pipelines/models.py` | No change — `Pipeline` + `Stage` models already exist. |
| `apps/pipelines/views.py` | No change — pipeline creation uses existing ViewSet logic. The onboarding view calls it programmatically. |
| `apps/teams/views.py` | No change — `MembershipViewSet.invite` reused. |
| `apps/imports/views.py` | No change — CSV import flow exists. Step 3 just links to it. |
| `apps/sync/views.py` | No change — OAuth flows reused. |

### Frontend

| File | What to do |
|------|-----------|
| `frontend/src/router/index.tsx` | Already imports `OnboardingPage` from `'../pages/onboarding'`. Change route to use `OnboardingLayout` instead of `AppLayout`. Add new layout route. |
| `frontend/src/pages/onboarding/` | **NEW directory** — all onboarding components. |
| `frontend/src/components/templates/app-layout.tsx` | Add onboarding guard: if `!user.is_onboarded && path !== '/onboarding'`, redirect to `/onboarding`. |
| `frontend/src/store/auth.ts` | Add `setUser` (already exists). After onboarding finish, call `setUser({ ...user, is_onboarded: true })`. |
| `frontend/src/types/index.ts` | Add `OnboardingStatus` interface. |
| `frontend/src/pages/settings/settings-page.tsx` | Add "Getting Started" section with link to `/onboarding?mode=review`. |

### Router Modification

Current router (simplified):

```tsx
{
  path: '/',
  element: <AppLayout />,
  children: [
    { path: 'dashboard', ... },
    { path: 'onboarding', element: <OnboardingPage /> },  // inside AppLayout
  ],
}
```

Change to:

```tsx
// — Onboarding route (no sidebar, no topbar) —
{
  path: '/onboarding',
  element: <OnboardingLayout />,
  children: [
    { index: true, element: <OnboardingWizard /> },
  ],
},
// — App routes (with sidebar) —
{
  path: '/',
  element: <AppLayout />,
  children: [
    { path: 'dashboard', ... },
    // ... all other routes
  ],
},
```

---

## 9. Implementation Order

### Phase 4.3a — Backend (2 days)

| Step | Description | File(s) |
|------|-------------|---------|
| 1 | Add `Tenant.industry` field, run migration | `apps/teams/models.py` |
| 2 | Create `onboarding_views.py` with status + progress + reset views | `apps/accounts/onboarding_views.py` |
| 3 | Implement `OnboardingStatusView` — reads `Tenant.settings.onboarding` + `User.is_onboarded` | Same file |
| 4 | Implement `OnboardingProgressView` — updates tenant settings, auto-creates pipeline from template | Same file |
| 5 | Implement `OnboardingResetView` — clears onboarding state | Same file |
| 6 | Add URL routes to `apps/accounts/urls.py` | `apps/accounts/urls.py` |
| 7 | Implement pipeline template creation logic (reusable function in `apps/pipelines/services.py`) | `apps/pipelines/services.py` (new) |
| 8 | Write tests for all 3 views (status, progress with skip + mark_complete, reset) | `apps/accounts/tests/` |
| 9 | Write test for pipeline template creation | `apps/pipelines/tests/` |

### Phase 4.3b — Frontend (2 days)

| Step | Description | File(s) |
|------|-------------|---------|
| 10 | Create `OnboardingLayout.tsx` — full-viewport layout, no sidebar | `frontend/src/pages/onboarding/components/` |
| 11 | Create `StepIndicator.tsx` — horizontal dot navigation | Same |
| 12 | Create `NavigationButtons.tsx` — Back/Next/Skip/Finish | Same |
| 13 | Create `OnboardingWizard.tsx` — step state machine + API integration | Same |
| 14 | Create `CompanySetupStep.tsx` — name, logo upload, industry | `.../steps/` |
| 15 | Create `InviteTeamStep.tsx` — email chip input + call `POST /teams/memberships/invite/` | Same |
| 16 | Create `ImportDataStep.tsx` — link to CSV import page + skip | Same |
| 17 | Create `ConnectEmailStep.tsx` — "Connect Gmail" button + OAuth flow | Same |
| 18 | Create `PipelineSetupStep.tsx` — template card selector + custom editor | Same |
| 19 | Create `DoneStep.tsx` — success animation + "Go to Dashboard" | Same |
| 20 | Create `useOnboarding.ts` API hook (react-query) | `frontend/src/pages/onboarding/hooks/` |
| 21 | Create `useOnboardingGuard.ts` — redirect logic | Same |
| 22 | Define `OnboardingStatus` type in `frontend/src/types/index.ts` | `frontend/src/types/` |
| 23 | Update router — extract `/onboarding` from AppLayout to its own layout | `frontend/src/router/index.tsx` |
| 24 | Add onboarding guard to `AppLayout.tsx` | `frontend/src/components/templates/app-layout.tsx` |
| 25 | Add "Getting Started" section to Settings page | `frontend/src/pages/settings/settings-page.tsx` |
| 26 | Handle OAuth redirect back to wizard (`?onboarding=true`) | `OnboardingWizard.tsx` + auth callback |
| 27 | Add review mode support (`?mode=review`) | `OnboardingWizard.tsx` |
| 28 | Write component tests (step indicator, wizard navigation, each step form) | `frontend/src/test/` |

---

## 10. Acceptance Criteria

### Backend

1. `GET /api/accounts/onboarding/status/` returns correct `is_onboarded` and per-step flags for a fresh tenant.
2. `PATCH /api/accounts/onboarding/progress/` with `company` payload updates `Tenant.name`, `Tenant.logo_url`, and `Tenant.industry`.
3. `PATCH /api/accounts/onboarding/progress/` with `pipeline_template="sales"` creates a Pipeline with 5 stages.
4. Calling with `pipeline_template` on a tenant that already has a default pipeline is a no-op (idempotent).
5. `PATCH /api/accounts/onboarding/progress/` with `skip_step="import"` records the skip and sets `import_done=true`.
6. `PATCH /api/accounts/onboarding/progress/` with `mark_complete=true` sets `User.is_onboarded=True` and `User.onboarded_at`.
7. `POST /api/accounts/onboarding/reset/` clears all onboarding state without deleting created data.
8. Unauthenticated requests return 401.

### Frontend

1. After signup/login with `is_onboarded=false`, user is redirected to `/onboarding` (full-viewport wizard).
2. Five steps are displayed in order with a visible step indicator.
3. Each step has a "Skip" link that marks the step as skipped and advances.
4. "Back" button is hidden on Step 1, active on Steps 2–5.
5. "Finish" button only appears on the final step (Done screen).
6. Closing/exiting the wizard navigates to dashboard without marking things complete.
7. Completing the wizard navigates to dashboard and the wizard is never shown again on login.
8. Settings page has "Getting Started" section. Clicking "Review Setup" opens the wizard in review mode.
9. OAuth callback with `?onboarding=true` returns to wizard on `/onboarding`.
10. Responsive: wizard works on mobile (single column, stacked buttons on small screens).

### Edge Cases

1. **Refresh during wizard** — fetching onboarding status returns current progress; wizard resumes at the first incomplete step.
2. **Multiple tabs** — if a user marks complete in one tab, the other tab's `fetchMe` call picks up the updated `is_onboarded` on next mount or refetch.
3. **OAuth callback race** — if the OAuth redirect lands on `/dashboard` instead of `/onboarding`, the AppLayout guard will redirect to `/onboarding`. The `?onboarding=true` param is a UX optimisation, not a safety requirement.
4. **Already has default pipeline** — `PATCH /onboarding/progress/` with `pipeline_template` is a no-op if a default pipeline exists.
5. **No seed demo data override** — the 17 deals and 12 contacts persist through onboarding. The pipeline template step creates a NEW pipeline alongside them.

---

## Appendix: Frontend Types (TypeScript)

Add to `frontend/src/types/index.ts`:

```typescript
export interface OnboardingStatus {
  is_onboarded: boolean;
  company_done: boolean;
  invite_done: boolean;
  import_done: boolean;
  email_done: boolean;
  pipeline_done: boolean;
  skipped_steps: string[];
  tenant: {
    name: string;
    logo_url: string;
    industry: string;
  };
}

export type PipelineTemplate = 'sales' | 'saas' | 'recruiting' | 'custom';

export interface OnboardingProgressPayload {
  company_done?: boolean;
  company?: {
    name?: string;
    logo_url?: string;
    industry?: string;
  };
  invite_done?: boolean;
  import_done?: boolean;
  email_done?: boolean;
  pipeline_done?: boolean;
  pipeline_template?: PipelineTemplate;
  mark_complete?: boolean;
  skip_step?: string;
}

export const PIPELINE_TEMPLATES: Record<PipelineTemplate, { name: string; stages: string[] }> = {
  sales: {
    name: 'Sales Pipeline',
    stages: ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Closed Won'],
  },
  saas: {
    name: 'SaaS Sales Pipeline',
    stages: ['Trial', 'Demo', 'Negotiation', 'Closed'],
  },
  recruiting: {
    name: 'Recruitment Pipeline',
    stages: ['Sourced', 'Screening', 'Interview', 'Offer', 'Hired'],
  },
  custom: {
    name: 'Custom Pipeline',
    stages: ['Lead', 'Qualified', 'Closed'],
  },
};

export const ONBOARDING_STEPS = [
  { key: 'company', label: 'Company', icon: 'Building2' },
  { key: 'invite', label: 'Invite', icon: 'UserPlus' },
  { key: 'import', label: 'Import', icon: 'Upload' },
  { key: 'email', label: 'Email', icon: 'Mail' },
  { key: 'pipeline', label: 'Pipeline', icon: 'GitBranch' },
] as const;
```

---

## Appendix: Backend View Stubs

### apps/accounts/onboarding_views.py (structure)

```python
"""Views for onboarding flow — status, progress, and reset."""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.pipelines.services import create_pipeline_from_template
from apps.teams.models import Tenant


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def onboarding_status(request: Request) -> Response:
    """Return current onboarding progress for the user's tenant."""
    tenant = Tenant.objects.get(id=request.user.tenant_id)
    settings = tenant.settings or {}
    onboarding = settings.get("onboarding", {})

    return Response({
        "is_onboarded": request.user.is_onboarded,
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
    })


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def onboarding_progress(request: Request) -> Response:
    """Update onboarding progress for one or more steps."""
    tenant = Tenant.objects.get(id=request.user.tenant_id)
    settings = tenant.settings or {}
    onboarding = settings.get("onboarding", {})

    data: dict[str, Any] = request.data

    # Handle company setup
    if "company" in data:
        company = data["company"]
        if "name" in company:
            tenant.name = company["name"]
        if "logo_url" in company:
            tenant.logo_url = company["logo_url"]
        if "industry" in company:
            tenant.industry = company["industry"]
        tenant.save(update_fields=["name", "logo_url", "industry"])

    # Handle step completion
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

    # Handle pipeline template
    if "pipeline_template" in data and not onboarding.get("pipeline_done"):
        create_pipeline_from_template(
            tenant_id=tenant.id,
            template_name=data["pipeline_template"],
        )
        onboarding["pipeline_done"] = True

    # Persist onboarding settings
    settings["onboarding"] = onboarding
    tenant.settings = settings
    tenant.save(update_fields=["settings"])

    # Handle mark_complete
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

    # Return updated status
    return Response({
        "is_onboarded": request.user.is_onboarded,
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
    })


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
```
