# Phase 3: Methods — Heuristic Evaluation, Critique & Testing

**Date:** 2026-06-30
**Skills applied:** heuristic-evaluation, design-critique, usability-testing, design-thinking-double-diamond, agile-lean-delivery, ab-testing, data-informed-design
**Reference:** Builds on ui-ux-pro-max-audit.md and assessment/01-foundation.md, assessment/02-craft.md

---

## 1. Heuristic Evaluation (Nielsen's 10 Heuristics)

Each screen has been evaluated against Jakob Nielsen's 10 usability heuristics. Severity: 0 (no issue) to 4 (catastrophic).

### Screen Scores

| Screen | H1 | H2 | H3 | H4 | H5 | H6 | H7 | H8 | H9 | H10 | Avg |
|--------|----|----|----|----|----|----|----|----|----|-----|-----|
| **Login** | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0.2 |
| **Signup** | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0.3 |
| **Onboarding** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |
| **Dashboard** | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0.3 |
| **Reports** | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0.1 |
| **Forecast** | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0.1 |
| **Contacts** | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0.2 |
| **Pipeline** | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.1 |
| **Activities** | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.1 |
| **Email** | **3** | 0 | **2** | **2** | **2** | 0 | 0 | **2** | 0 | 0 | **1.1** |
| **Settings** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 |

**Heuristics Key:**

| ID | Heuristic | Score Explanation |
|----|-----------|------------------|
| H1 | **Visibility of system status** | Dashboard: metric cards show "No data" instead of contextual status. Email: crash with no feedback. Contacts: no count shown during loading. |
| H2 | **Match between system and real world** | No significant violations — terminology matches CRM conventions |
| H3 | **User control and freedom** | Login: no "Forgot password?" link (uses magic link instead). Activities filters: can't clear individual filter. Email: "Discard" in compose is permanent — no draft recovery. |
| H4 | **Consistency and standards** | Email: error state UI differs from other pages (uses inline error vs consistent EmptyState component). Settings: some sections use design tokens, others hardcode Tailwind classes. |
| H5 | **Error prevention** | Email: crash on connection data shape mismatch (no type guard). Slack/Users/Audit Log: 404 with no prevention. No confirmation on destructive actions. |
| H6 | **Recognition rather than recall** | Signup: field-level validation shows after submit, but no inline hints for password requirements. Dashboard: metric trends show "vs last month" — no way to change period. |
| H7 | **Flexibility and efficiency of use** | No keyboard shortcuts for power users. No bulk edit mode in Contacts beyond basic select. No way to save dashboard/report views. |
| H8 | **Aesthetic and minimalist design** | Email compose modal: "To" field has "Message" label for body — unnecessary if label is clear from context. Settings: "Change Avatar" button exists but avatar section is empty. |
| H9 | **Help users recognize, diagnose, and recover from errors** | Email crash: "connections?.find is not a function" — developer message shown to user. Slack/Users/Audit Log: "404 Not Found" — no recovery path. |
| H10 | **Help and documentation** | No contextual help, no tooltips, no FAQ, no docs link within app |

### Critical Violations (Severity 3-4)

| Violation | Heuristic | Screen | Severity | Description |
|-----------|-----------|--------|----------|-------------|
| V1 | H1, H9 | Email | **4 (Catastrophic)** | Email page crashes on load with `connections?.find is not a function`. No error boundary catches it. User sees React error overlay. |
| V2 | H9 | Slack/Users/Audit Log | **3 (Major)** | 404 crashes with no recovery path. User must use browser back button. |
| V3 | H5 | Email | **3 (Major)** | `useSyncConnections` returns non-array data with no type guard — unhandled runtime exception |
| V4 | H3, H5 | All CRUD | **3 (Major)** | No confirmation on destructive actions (delete contact, delete deal) |
| V5 | H1 | All (empty data) | **3 (Major)** | Every content page shows $0/0/empty state. Users cannot verify CRM works. No demo data seeding. |
| V6 | H8, H10 | Email | **3 (Major)** | Crash error message is developer stack trace — not user-friendly |

---

## 2. Design Critique — Key Decisions vs Best Practice

### What Works Well

1. **Drag-and-drop pipeline** — Uses `@dnd-kit` with keyboard sensor, multiple sortable contexts. This is a strong interaction design choice that matches how sales teams think about moving deals.
2. **Email split-pane layout** — Desktop split pane with smooth transition to mobile single-pane. The `hidden lg:flex` / `lg:w-[380px]` pattern is a model responsive implementation.
3. **Modal system** — Focus trap, body scroll lock, Escape/click-outside/X close, 3 sizes. This is production-grade.
4. **Dark mode** — Comprehensive dark theme applied throughout, with proper semantic tokens. Toggle is prominent in the topbar.
5. **Empty state pattern** — Consistent icon + title + description + CTA. A best practice that reduces user confusion when data is absent.
6. **Template picker in email** — Integrates with compose modal to apply pre-built email templates.

### What Needs Improvement

| Decision | Current State | Best Practice | Gap |
|----------|--------------|---------------|-----|
| **Settings as flat page** | All settings sections rendered on one page | Sub-navigation with dedicated routes | Will break at 10+ settings sections |
| **Sidebar link count** | 12 links including Slack, Users, Audit Log | < 8 primary navigation + settings for secondary | Users/Logs/Integrations should be Settings sub-nav |
| **Duplicate /timeline route** | Two routes render same component | Single canonical route | Confuses navigation mental model |
| **No breadcrumbs** | Deep pages have no path indicator | Location breadcrumbs for 3+ level deep pages | Users lost in email/templates, contacts/:id |
| **No keyboard shortcuts** | All interactions require clicking | Common shortcuts (g+d dashboard, g+c contacts, c to compose) | Power users slowed down |
| **No global search keyboard shortcut** | Search only accessible via topbar click | `Cmd+K` / `Ctrl+K` to focus search | Standard convention for searchable apps |
| **No undo for actions** | Destructive actions have no reversal | Soft delete with undo toast (Gmail pattern) | Fear of data loss reduces exploration |

---

## 3. A/B Testing Opportunities

With the app currently in early stage (MVP with no seed data), A/B testing preparation should focus on instrumenting the right metrics before the app has real users.

### Ready-to-Test Hypotheses

| # | Hypothesis | Variant A (Current) | Variant B (Proposed) | Metrics |
|---|-----------|---------------------|---------------------|---------|
| AB1 | A compact sidebar with icons only increases pipeline page engagement | Expanded sidebar with labels | Collapsed sidebar with icon-only, label on hover | Pipeline page views, deal creation rate |
| AB2 | Dashboard metric card layout affects comprehension | 4-column grid of metric cards | 2-column grid with metric cards + trend sparklines | Time to find specific metric, scroll depth |
| AB3 | Empty state CTA placement affects first-deal creation | "No deals yet" text with "Add Deal" button at bottom | "Add your first deal" hero CTA centered with import option | Deal creation rate, import rate |
| AB4 | Pipeline kanban vs table on mobile affects deal management | Column/kanban layout (stacks vertically) | Card-style list with sortable deal cards | Deal update frequency, time per deal |
| AB5 | Email compose position affects response time | Modal-based compose | Full-page compose with sidebar email list | Compose completion rate, email send frequency |

### Infrastructure Needed

- User analytics integration (PostHog, Amplitude, or similar)
- Feature flag system for controlled rollouts
- Event tracking on key actions: login, create_deal, move_deal_stage, send_email, add_contact, page_views
- Session recording for qualitative analysis

---

## 4. Data-Informed Design Analysis

### Current State: No Analytics Instrumentation

Based on code analysis, there is **no analytics or telemetry** in the frontend application. No event tracking, no page view capture, no user action logging beyond what the backend audit log may provide. This means:

- **No conversion funnel data** — cannot measure login → first deal creation flow
- **No feature adoption metrics** — cannot tell if users find Pipeline, Email, or Reports
- **No error monitoring** — the Email crash and 404 pages have no telemetry
- **No heatmap/click tracking** — cannot identify where users click most
- **No A/B testing infrastructure**

### What Metrics Current UX Is Likely Harming

| Metric | Current Impact | How | Recovery |
|--------|---------------|-----|----------|
| **Email connection rate** | Near 0% | Email page crashes before connection UI renders | Fix crash → instrument → measure |
| **Deal creation rate** | Near 0 | Empty state with no demo data; no import from CSV visible on first visit | Seed demo data; promote CSV import |
| **First-day retention** | Low | User logs in, sees $0 metrics, crashes on Email | Fix crashes; seed data; guide to first value-creating action |
| **Settings exploration** | Low | 3 sidebar links crash with 404 | Fix 404 pages or remove broken links |
| **Activity logging rate** | Near 0 | No clear "Log activity" CTA on all pages | Add floating action button for quick activity logging |
| **Search usage** | Unknown (can't measure) | Search combobox implemented but no analytics | Instrument search queries |
| **Mobile engagement** | Low | Touch targets below 44px, sidebar takes tablet space | Fix touch targets, responsive sidebar |

### HEART Metrics Framework (Proposed)

| Goal | Happiness | Engagement | Adoption | Retention | Task Success |
|------|-----------|------------|----------|-----------|--------------|
| **Login & Onboard** | CSAT after onboarding | 1st day actions completed | % signups who complete onboarding | Day-1 → Day-7 return rate | % who reach dashboard |
| **Manage Pipeline** | Pipeline page satisfaction | Deals created/week | % users with ≥1 deal | Weekly pipeline visits | Deals moved to next stage |
| **Email Integration** | Email page satisfaction | Emails sent/week | % connected accounts | Email page return rate | Successful email send |
| **Reporting** | Reports usefulness rating | Reports viewed/month | % who view reports | Monthly report views | Report export rate |

---

## 5. Usability Testing Plan

### Recommended Tests

| Priority | Test | Method | Participants | Key Questions |
|----------|------|--------|-------------|---------------|
| **P0** | New user onboarding | Moderated remote | 5 sales reps | Can user sign up, complete onboarding, and create first deal? |
| **P0** | Email setup | Moderated remote | 5 sales reps | Can user connect Gmail and find the compose action? |
| **P1** | Deal management | Unmoderated | 8 sales reps | Can user create, move, and close a deal? |
| **P1** | Contact lookup | Moderated remote | 5 users | Can user find a contact and view details? |
| **P2** | Reports comprehension | Unmoderated | 5 managers | Can user find pipeline value and conversion rate? |
| **P2** | Mobile pipeline | Moderated (mobile) | 5 field reps | Can user manage deals on phone? |

### Test Task Script Examples

**Task 1: Create a deal (P0)**
> "You just had a great call with Acme Corp about their software needs. They're interested in a $50,000 annual contract. Add them as a deal in the pipeline."

**Task 2: Connect email (P0)**
> "Your manager asked you to follow up on yesterday's email thread with a client. Connect your work email and find that thread."

**Task 3: Generate a report (P1)**
> "Your quarterly review is next week. Show your manager a report of all deals in the pipeline and their expected close dates."

---

## 6. Agile/Lean Delivery Recommendations

### Current State
The codebase shows signs of an MVP built with good architecture but insufficient QA before shipping. Multiple pages crash at runtime, indicating gaps in testing coverage.

### Recommendations

1. **Adopt Lean UX within sprints** — each sprint should include a hypothesis + user validation, not just feature dev
2. **Fix crashes before new features** — the Email, Slack, Users, and Audit Log crashes block core workflows
3. **Instrument before shipping** — add basic analytics (page views, key actions) to every new screen before launch
4. **Add error boundaries** — wrap every page route in a React Error Boundary with recovery options
5. **Seed demo data** — create a demo data flow for new users so they see a populated CRM on first login
6. **Ship in smaller batches** — rather than building all pages at once, validate each page with users before building the next

### Phase Model

| Phase | Focus | Timeline | Deliverables |
|-------|-------|----------|-------------|
| **Alpha** | Fix crashes + seed data | Sprint 1 | Email page fix, error boundaries, demo data toggle |
| **Beta** | Core flows validated | Sprints 2-3 | Inter font, responsive sidebar, keyboard accessibility |
| **Live** | Analytics + optimization | Ongoing | HEART metrics, A/B testing, user testing cadence |