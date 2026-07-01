# User Journey Maps — FrontierCRM

**Date:** 2026-06-30
**Author:** Creative (ALLSTARS Design)
**Personas:** Alex Chen (Sales Rep), Monica Reyes (Sales Manager), Jordan Taylor (Admin)

> Three journey maps mapping critical FrontierCRM user flows. Each map documents the current experience (what exists now), the desired experience (what should be), and the opportunity gaps between them.

---

## Journey 1: New User Onboarding + First Deal Creation

**Persona:** Jordan Taylor (Admin / Onboarder) → Alex Chen (Sales Rep)
**Scenario:** A new sales rep joins the team. The CRM admin sets up the workspace, and the new rep completes onboarding, then creates their first deal.
**Goal:** Get a new sales rep from zero to productive (first deal created) in under 15 minutes.

### Phase 1: Admin Setup

| *Admin prepares the workspace* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. Configure pipelines & stages | ❌ No pipeline management UI exists. Pipelines appear to be seeded via database. | Drag-and-drop pipeline editor with add/rename/delete stages. Save and publish. | **HIGH** — Admin cannot configure the core sales process without developer intervention |
| 2. Set up custom fields | ⚠️ Custom Fields tab exists (CRUD) but no validation rules, required flags, or field types. | Full field editor: text, number, date, select, multi-select. Validate on save. | **MEDIUM** — Basic custom fields work, but the lack of validation means data quality suffers |
| 3. Create user & assign permissions | ⚠️ Invite Team step exists in onboarding. Settings > Team shows members. No role picker. | Invite by email with role assignment (Admin / Manager / Rep). Batch invite. | **HIGH** — No role-based permissions during invite |
| 4. Integrate email & calendar | ⚠️ Settings > Integrations has Gmail OAuth, Calendar auth URLs. Setup is disjointed across tabs. | Guided "Connect your tools" wizard with OAuth flow and success confirmation. | **MEDIUM** — Integration exists but scattered |
| 5. Configure company profile | ✅ Company Setup step in onboarding (name, industry, logo). | Works well. Add timezone and currency defaults. | **LOW** — Solid foundation, minor polish |

### Phase 2: New User Onboarding

| *New rep's first experience* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. Sign up / accept invite | ✅ Signup page exists with email/password, Google, Microsoft, SSO auth. | Works well. Add magic link option. | **LOW** |
| 2. Onboarding wizard (5 steps) | ⚠️ OnboardingWizard covers: Company → Invite → Import → Email → Pipeline → Done. Most steps are stubs or skippable. | Condensed to 3 essential steps: (1) Set up company, (2) Connect email, (3) Quick pipeline tour. | **HIGH** — Too many steps, most are irrelevant for a new rep. Import data is an admin task |
| 2a. Company step | ✅ Pre-filled with admin's settings. Name/industry/logo. | Good. Add phone and website. | **LOW** |
| 2b. Invite team | ❌ Pointless for a new rep — they're the one being invited. | Skip entirely for non-admin users. | **MEDIUM** — Should be role-gated |
| 2c. Import data | ❌ CSV import step is a stub. Irrelevant for a first-day user. | Remove from onboarding. Show as admin tool later. | **MEDIUM** |
| 2d. Email step | ✅ Connect Gmail via OAuth. | Works well. Add calendar integration here too. | **LOW** |
| 2e. Pipeline setup | ⚠️ PipelineSetupStep exists but shows no UI for configuring stages. Just a "skip" option. | If admin has configured pipelines, show a summary + quick tour. If not, redirect to admin. | **MEDIUM** |
| 3. Dashboard first view | ✅ Dashboard loads with metrics, charts, activity feed. All empty state shown gracefully (No data / No deals yet). | Add contextual tooltips on first visit: "Click here to add your first deal" | **LOW** — Good empty states, could add guidance |

### Phase 3: First Deal Creation

| *The rep creates their first deal* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. Navigate to Pipeline | ✅ Sidebar > Pipeline link. Page shows "No deals yet" + "Add Deal" button. | Works well. | — |
| 2. Click "Add Deal" | ✅ Modal opens with form: name, value, company, pipeline, stage, close date. | Good. Add contact selector (linked to CRM contacts). | **MEDIUM** — Company field is free text, no lookup |
| 3. Fill deal details | ⚠️ Fields: name (required), value (required, number), company (text, optional), pipeline (select), stage (select), close date (date). Pipeline/Stage selects use native `<select>` without consistent styling. | Add contact ownership picker. Stage color coding in the dropdown. | **MEDIUM** — Native selects don't match design system |
| 4. Save deal | ✅ Deal saved. Toast success. Pipeline Invalidated. Modal closes. | Works well. Consider redirecting to the new deal in pipeline view. | **LOW** |
| 5. See deal in pipeline | ✅ Kanban view shows column with deal card. Card shows name, value, contact, close date. | Great visual feedback. Add animation for new card appearing. | **LOW — Delight** |

### Journey Emotion Map

```
😊 ┤                                    ┌─────────┐
   │                                    │ Deal in  │
   │                            ┌───────┤ Pipeline │
   │    ┌───────────────────────┤ Onboard│(delight) │
   │    │   Login                │ wizard │         │
   │    │(neutral)              │(tedious)│         │
😐 ┤────┤                        │         └─────────┘
   │    │                        │         ┌─────────┐
   │    │   Admin setup           │         │  Fill   │
   │    │  (frustration -         │         │ form    │
   │    │   no pipeline UI)       │         │(ok)     │
😟 ┤    └────────────────────────┘         └─────────┘
```

**Emotional low points:** Admin setup (pipeline config not possible), Invite step (irrelevant for new rep), Import step (stub)

### Key Opportunity Gaps

| # | Gap | Impact | Effort | Recommendation |
|---|-----|--------|--------|----------------|
| 1 | No pipeline management UI | Admin cannot configure CRM core | **High** | Add pipeline editor to Settings or a dedicated Admin panel |
| 2 | Onboarding too long for non-admin reps | Drop-off before first deal | **High** | Role-gate steps; hide Invite/Import for reps |
| 3 | Company field is free text | Data inconsistency, no contact linking | **Medium** | Add contact lookup + create-on-the-fly |
| 4 | No guided first-task after onboarding | Users leave after onboarding ends | **Medium** | Add "Quick start" checklist on first dashboard visit |
| 5 | Import step is a stub | Cannot migrate existing data | **High** | Build CSV import with field mapping |

---

## Journey 2: Sales Rep Daily Workflow

**Persona:** Alex Chen (Sales Rep)
**Scenario:** A typical Tuesday. Alex starts her day by reviewing pipeline, updates a deal stage, logs a call, and checks the activity timeline for context on an upcoming meeting.
**Goal:** Complete the daily pipeline review + activity logging loop in under 5 minutes.

### Phase 1: Morning Pipeline Scan

| *Alex opens the CRM and takes stock* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. Log in | ✅ Auth screen, email/password or SSO. Fast redirect to dashboard. | Add "remember me" for SSO users. Keep session alive for 24h. | **LOW** |
| 2. Dashboard scan | ✅ Dashboard loads with: Total Pipeline Value, Won Deals, Win Rate, Active Deals. Bar chart, recent activity, tasks due. Stale deals warning. | Excellent overview. Add "My Deals" filter (vs global). | **MEDIUM** — Dashboard is global, no per-rep view |
| 3. Check stale deals | ✅ Red banner shows count of stale deals. "View Reports" button links to Reports page. | Add inline actions: "Nudge contact" or "Reassign" directly from banner. | **MEDIUM** — Information but no action |
| 4. Quick tasks view | ✅ Tasks Due card shows with priority colors and due dates. | Add quick-complete checkbox inline. | **MEDIUM** — Read-only tasks, must go elsewhere to complete |
| 5. Navigate to Pipeline | ✅ Sidebar click → Pipeline page loads with Kanban columns and deal cards. | Good. Consider keyboard shortcut for pipeline (g+p). | **LOW** |

### Phase 2: Pipeline Deal Management

| *Alex works through her deals* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. Scan Kanban columns | ✅ Columns show stage names with color bars, deal count badge, total value. Cards show name, value, contact, close date, win probability. | Excellent visual hierarchy. Add column-summary tooltip. | **LOW — Delight** |
| 2. Reorder deals within a stage | ✅ Drag handle appears on hover, drag-and-drop reorders using `@dnd-kit`. | Works well. Add audible/haptic feedback on drop. | **LOW — Delight** |
| 3. Move deal to another stage | ✅ Drag and drop between columns. SortableContext + DndContext handles cross-column moves. | Smooth interaction. Add undo toast on accidental move. | **LOW** |
| 4. Open deal detail | ✅ Click deal card → modal opens with: status badge, probability, name, value, stage dropdown, contact, close date, custom fields, action buttons (Win/Lost/Abandoned). | Good depth. Add activity history timeline inside the modal. | **MEDIUM** — No deal-specific activity view in the modal |
| 5. Edit deal inline | ⚠️ Edit mode replaces fields with inputs. "Save" button commits changes. No inline editing on the Kanban card itself. | Add quick-edit: click value on card to edit in place without opening modal. | **MEDIUM** — Speed improvement for frequent updates |
| 6. Change deal status | ✅ Status buttons: Win (green), Lost (red), Abandoned (neutral). Lost requires close reason. | Works well. Add "Mark Won" drag target at top of Kanban. | **LOW — Delight** |

### Phase 3: Activity Logging

| *After a phone call, Alex logs her interaction* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. Find the contact | ⚠️ Navigate to Contacts → search → click row → contact detail page. 3 clicks to reach the contact. | Global search is fast. Add a "Quick Log" button in the topbar that opens an activity form without leaving current page. | **HIGH** — Too many clicks for a quick log |
| 2. Navigate to Activity tab | ✅ Contact detail has tabs: Overview, Activity, Deals, Notes, Emails. | Well-structured tabs. Remember last active tab per contact. | **LOW** |
| 3. Log a call | ⚠️ Activity tab shows past activity but there's no "Log Call" or "Add Activity" button visible in the page code examined. Activities are read-only display. | Add inline "Log Call" / "Add Note" buttons in the Activity tab header. Quick form: type selector, notes field, duration. | **HIGH** — Cannot log an activity from the contact page |
| 4. Log a note | ⚠️ Notes tab exists in tab config but no notes form seen in contact-detail (truncated read at 500 lines — not visible). | Inline notes editor with save. Auto-sync to activity timeline. | **MEDIUM** — Notes tab exists but unclear if functional |
| 5. Return to pipeline | ✅ Sidebar click → Pipeline page. | Works well, but no "Back to where I was" breadcrumb. | **LOW** |

### Phase 4: Context Check Before Meeting

| *Alex has a 2pm meeting with a prospect* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. Search for contact | ✅ Global search in topbar — type name, keyboard navigate, Enter to open. Full combobox pattern with keyboard shortcuts. | Excellent search. Add recent contacts section when search input is focused but empty. | **LOW — Delight** |
| 2. View contact overview | ✅ Overview tab shows: email, phone, address, account, tags, owner, source, job details, LinkedIn, Twitter. Contact info is well-organised. | Good info density. Add deal summary right in the overview. | **MEDIUM** — Must switch to Deals tab to see associated deals |
| 3. Check recent activity | ✅ Activity tab shows timeline of past interactions (calls, emails, notes, meetings) with type-specific icons and color coding. | Works well. Add filter by activity type within the contact. | **LOW** |
| 4. Check associated deals | ✅ Deals tab shows deals linked to this contact. | Good. Add deal stage color indicator. | **LOW** |
| 5. Start call/meeting confident | ✅ All context available in one place. | Add a "Prep Summary" card at the top of the contact page: last interaction date, next action, open deals. | **MEDIUM** — Manual context gathering takes time |

### Journey Emotion Map

```
😊 ┤     ┌────────┐          ┌─────────┐      ┌────────┐
   │     │Pipeline│          │  Deal   │      │Contact │
   │ ┌───┤ Scan   ├──────────┤  Detail ├──────┤ Context│
   │ │   │ (good) │          │  (good) │      │ (good) │
😐 ┤─┤   └────────┘          └─────────┘      └────────┘
   │ │          ┌────────┐          ┌────────┐
   │ │          │  Log   │          │  Edit  │
   │ │          │Activity│          │ inline │
   │ │          │(frustrate│       │(frustrate│
😟 ┤─┘          └────────┘          └────────┘
```

**Emotional low points:** No quick activity logging from contact list, no inline edit on Kanban card, too many clicks to log a simple call

### Key Opportunity Gaps

| # | Gap | Impact | Effort | Recommendation |
|---|-----|--------|--------|----------------|
| 1 | No quick activity logging | High-friction call/note logging | **High** | Add "Quick Log" floating action button in topbar or pipeline |
| 2 | Cannot log call from contact list | Must visit detail page for every interaction | **High** | Add inline activity buttons to contact table rows (call, email, note) |
| 3 | No inline Kanban card editing | Frequent updates require opening modal | **Medium** | Click-to-edit name/value directly on deal card |
| 4 | No deal-specific activity inside deal modal | Must navigate to contact to see deal history | **Medium** | Add activity timeline sub-section to DealDetailModal |
| 5 | No meeting prep summary | Manual context-gathering before calls | **Medium** | Add "Quick Prep" card to contact overview |

---

## Journey 3: Manager Workflow — Forecast Review & Team Oversight

**Persona:** Monica Reyes (Sales Manager)
**Scenario:** Monday morning. Monica reviews the team forecast, identifies coaching opportunities, and prepares for her weekly 1:1s.
**Goal:** Get the full team picture — pipeline health, forecast accuracy, individual rep performance — in under 10 minutes.

### Phase 1: Pipeline Health Check

| *Monica opens the CRM and scans for problems* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. Dashboard review | ✅ Dashboard shows: Total Pipeline Value ($0 or actual), Won Deals, Win Rate, Active Deals. Bar chart by stage. Stale deals warning. | Solid overview. Add per-rep breakdown. | **HIGH** — Dashboard shows aggregate only |
| 2. Check stale deals banner | ✅ Red banner: "N deals need attention" with count of overdue. "View Reports" button. | Add quick action: assign to rep, send nudge, mark reviewed. | **MEDIUM** — Information without action |
| 3. View pipeline by stage chart | ✅ Bar chart: deal value distribution across stages (empty state handled). Recharts-based. | Good. Add stage conversion rate overlay. | **MEDIUM** — Value only, no conversion data |
| 4. Check recent activity | ✅ Activity feed shows latest actions. | Good. Add team-member filter. | **MEDIUM** — No way to see what a specific rep has done recently |
| 5. View tasks due | ✅ Tasks Due card shows upcoming/overdue. | Good for personal tasks. Add team task overview. | **MEDIUM** |

### Phase 2: Deep Dive — Reports & Analysis

| *Monica needs real numbers* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. Navigate to Reports | ✅ Sidebar > Reports. Dashboard tab shows: metric cards, pipeline value chart, win rate chart, activity metrics, deal velocity, stage funnel, top performers, stale deals. | Extremely comprehensive reports page. Well-organised sections. | — |
| 2. Set date range | ✅ Preset dropdown (7d/30d/90d/quarter/custom) + manual start/end date pickers. | Works well. Add period-over-period comparison toggle. | **MEDIUM** — No side-by-side comparison |
| 3. View win rate chart | ✅ WinRateChart component renders with trend data. | Good. Add per-rep win rate breakdown. | **MEDIUM** — Aggregate only |
| 4. Check top performers | ✅ TopPerformersTable shows ranking. | Good. Add metric selector (by value, by count, by win rate). | **LOW** |
| 5. Export report | ✅ ExportButton component present. | Works well. Add scheduled report delivery (email weekly). | **MEDIUM** — Manual export only |
| 6. Switch to Forecast tab | ✅ Forecast tab with: range selector (3/6/12 months), confidence level (conservative/medium/optimistic), scenario builder. | Very comprehensive. Add automated forecast notes ("3 deals at risk"). | **MEDIUM** — User must build scenarios manually |

### Phase 3: 1:1 Prep — Individual Rep Deep Dive

| *Monica preps her 1:1 with Alex* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. View rep's activity | ❌ No per-rep filtering on any page. Dashboard and Reports show all data together. Monica cannot filter by team member. | Add user/owner filter to Dashboard, Reports, and Timeline pages. | **HIGH** — Cannot do per-rep analysis |
| 2. Find rep's stale deals | ❌ Overview page shows all stale deals, no owner filter. | Add owner column + filter to stale deals list. | **HIGH** |
| 3. View rep's pipeline | ✅ Monica can click to Pipeline and see all deals. Deal cards show contact_name but not owner explicitly (inferred from logged-in user). | Add owner badge on deal cards. Pipeline filter by owner. | **MEDIUM** — Current view is global |
| 4. Review rep's activity timeline | ✅ Timeline page exists with type/date filters. But no user filter. | Add "by user" filter to timeline page. | **HIGH** |
| 5. Check rep's forecast | ✅ Forecast page has scenario builder but no per-rep toggle. | Add rep selector to Forecast page. | **HIGH** |
| 6. Prepare talking points | ❌ No "1:1 prep" or meeting summary view. Monica must manually cross-reference dashboard, pipeline, reports, timeline. | Add a "1:1 Prep" page or section that shows: rep's deals, recent activity, stale deals, forecast contribution. | **HIGH** — High-value feature for managers |

### Phase 4: Team Oversight — Ongoing

| *Monica checks in mid-week* | | | |
|--|--|--|--|
| **Step** | **Current Experience** | **Desired Experience** | **Opportunity Gap** |
| 1. Check audit log | ✅ Settings > Audit Log shows system events. | Good for compliance. Add user-friendly summaries. | **LOW** |
| 2. Check team activity | ✅ Activity Timeline shows org-wide activity with type/date filters. | Add user/team filter. | **HIGH** |
| 3. Set coaching goals | ❌ No goal-setting or target management feature. | Add quarterly targets per rep, track progress. | **HIGH** — New feature |
| 4. Review pipeline health | Comes back to dashboard and reports. | Add "Pipeline Health Score" — deals per stage, age in stage, risk indicators. | **MEDIUM** |

### Journey Emotion Map

```
😊 ┤                ┌────────┐
   │                │Reports │
   │   ┌────────┐   │(great!)│   ┌──── Missing ────┐
   │   │Pipeline│   └────────┘   │ Per-rep filter   │
   │   │ Scan   │                │ 1:1 Prep view    │
😐 ┤───┤(good)  ├────────────────┤ Activity by user │
   │   └────────┘                │ Goal tracking    │
   │                             └──────────────────┘
   │          ┌────────┐                   ┌──────┐
   │          │Forecast│                   │ 1:1  │
   │          │ (good) │                   │ Prep │
😟 ┤          └────────┘                   │(manual)│
```

**Emotional low points:** Cannot filter by rep anywhere, must manually piece together 1:1 data from 4+ pages, no per-rep forecast view

### Key Opportunity Gaps

| # | Gap | Impact | Effort | Recommendation |
|---|-----|--------|--------|----------------|
| 1 | No per-rep filtering anywhere | Manager cannot assess individual performance | **Critical** | Add user/owner filter to Dashboard, Reports, Pipeline, Timeline |
| 2 | No 1:1 prep view | Manual context gathering before every meeting | **High** | Create "Team View" dashboard with per-rep cards + "Prep for 1:1" button |
| 3 | No goal/target tracking | No way to measure rep progress against quota | **High** | Add quarterly targets with progress bars per rep |
| 4 | No manager-specific dashboard | Dashboard shows same data for everyone | **High** | Create role-aware dashboard with team metrics when user is Manager |
| 5 | Forecast is global | Cannot see individual rep forecast contribution | **High** | Add owner filter to Forecast page |

---

## Cross-Journey Opportunity Matrix

| Opportunity | Journey 1 | Journey 2 | Journey 3 | Effort | Impact |
|-------------|-----------|-----------|-----------|--------|--------|
| Add owner/user filter to all pages | ⚡ | ⚡ | ⚡⚡⚡ | Medium | Critical |
| Quick activity logging (call/note) | ⚡ | ⚡⚡⚡ | ⚡ | Medium | High |
| Pipeline management UI in Settings | ⚡⚡⚡ | — | ⚡ | Large | High |
| Inline Kanban card editing | — | ⚡⚡⚡ | — | Small | Medium |
| Role-gated onboarding steps | ⚡⚡⚡ | ⚡ | — | Small | High |
| "My Deals" filter on dashboard | — | ⚡⚡ | ⚡ | Small | Medium |
| Contact picker in Add Deal modal | ⚡⚡ | ⚡⚡ | — | Medium | Medium |
| 1:1 Prep view for managers | — | — | ⚡⚡⚡ | Medium | High |
| Goal tracking (quarterly targets) | — | — | ⚡⚡⚡ | Large | High |
| Period-over-period report comparison | — | — | ⚡⚡ | Medium | Medium |

---

*These journey maps are based on observed app behaviour, code analysis, and UX audit findings (ui-ux-pro-max-audit.md). They should be validated with real user testing before prioritising roadmap items. Version 1.0 — 2026-06-30.*