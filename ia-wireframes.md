# Information Architecture & Wireframes — FrontierCRM

**Date:** 2026-06-30
**Author:** Creative (ALLSTARS Design)

> A structured analysis of FrontierCRM's current information architecture with proposed improvements and low-fidelity wireframes for the four highest-impact screens.

---

## 1. Current Site Map

### Top-Level Routes

```
/login                          Auth (email/password, Google, Microsoft, SSO, magic link)
/signup                         Registration
/auth/saml-callback             SAML SSO redirect handler
/auth/social-callback           Social auth redirect
/auth/two-factor-challenge      2FA challenge
/auth/magic-link                Magic link verification

/onboarding                     Onboarding wizard (5 steps)
  ├── Company Setup (name, industry, logo)
  ├── Invite Team (email invite)
  ├── Import Data (stub)
  ├── Connect Email (Gmail OAuth)
  ├── Pipeline Setup (stub)
  └── Done (summary + finish)

/dashboard                      Dashboard (metrics, chart, activity, tasks)
/reports                        Reports (dashboard + forecast tabs)
/forecast                       Standalone forecast page
/contacts                       Contact list (table, search, pagination)
/contacts/:id                   Contact detail (5 tabs)
/pipeline                       Pipeline (Kanban + add/edit deal)
/activities                     Activity timeline (type + date filters)
/timeline                       Same as /activities (alias)
/email                          Email (inbox / sent / starred)
/settings                       Settings (6 tabs)
  ├── Profile
  ├── Team
  ├── Security
  ├── Integrations
  ├── Custom Fields
  ├── API Keys
/settings/integrations/slack    Slack integration (sidebar link target)
/settings/users                 Users management (sidebar link target)
/settings/audit-log             Audit log (sidebar link target)
```

### Sidebar Navigation (Current)

```
─ Dashboard
─ Reports
─ Forecast
─ Contacts
─ Pipeline
─ Activities
─ Timeline
─ Email
─ Settings
─ Slack
─ Users
─ Audit Log
```

### IA Issues Identified

| # | Issue | Detail |
|---|-------|--------|
| IA-1 | **Sidebar overload** | 12 nav items. Activities + Timeline are the same page. Slack, Users, Audit Log are Settings sub-pages listed at top level. |
| IA-2 | **Duplicate routes** | `/activities` and `/timeline` serve the same page (timeline-page.tsx), routing confusion. |
| IA-3 | **Mixed hierarchy** | Settings sub-pages (Slack, Users, Audit Log) appear at root level alongside Dashboard and Pipeline. Settings already has these as tabs — two paths to the same content. |
| IA-4 | **Missing routes** | No `/contacts/new` (quick-add contact), no `/pipeline/:id` (direct pipeline link), no `/activities/log` (direct activity log). |
| IA-5 | **Hidden admin tools** | Pipeline management (create/edit stages) has no UI — only seeded through backend. Custom fields exist but lack validation. |
| IA-6 | **Onboarding routing** | Onboarding guard redirects to `/onboarding` but wizard is 5 steps — most irrelevant for a new rep. |
| IA-7 | **No search results page** | Global search is excellent but limited to a dropdown overlay. No dedicated search results page for complex queries. |

---

## 2. Proposed IA Improvements

### 2.1 Proposed Navigation Structure

**Primary Nav (sidebar — 7 items)**

```
─ Dashboard
─ Pipeline
─ Contacts
─ Activities       <<< merged: Activities + Timeline into one page with view toggle
─ Email
─ Reports
─ Settings
```

**Secondary Nav (settings sub-pages — accessed via tabs within Settings)**

```
Settings
  ├── Profile
  ├── Team & Permissions   <<< renamed from "Team" for clarity
  ├── Pipelines & Stages   <<< NEW — pipeline editor
  ├── Custom Fields
  ├── Integrations
  ├── Security
  ├── API Keys
  └── Audit Log
```

**Quick Actions (topbar or floating)**

```
[+] Add Deal     [📞] Log Call     [📧] Compose Email
```

### 2.2 Rationale

| Change | Why |
|--------|-----|
| Merge Activities + Timeline | Same page, different route. Remove one. Add a "list view" / "timeline view" toggle internally. |
| Remove Slack, Users, Audit Log from sidebar | These are Settings sub-pages. Users and Audit Log already exist as Settings tabs. Removing 3 items from sidebar reduces cognitive load. |
| Add Pipelines & Stages to Settings | Currently no UI exists. Critical for Admin persona. |
| Reorder nav by frequency of use | Dashboard (daily), Pipeline (daily), Contacts (daily), Activities (daily), Email (daily), Reports (weekly), Settings (rare). Current order is alphabetical-ish. |
| Rename "Team" → "Team & Permissions" | More descriptive of what's inside (users, roles, invites). |
| Add quick action buttons | The journey maps show that Alex needs to log calls and create deals without navigating to a specific page first. |

### 2.3 Recommended Route Structure

```
/login                          Auth
/signup                         Auth
/onboarding                     New user onboarding (role-gated steps)

/app/dashboard                  Dashboard
/app/pipeline                   Pipeline (Kanban)
/app/pipeline/:id               Pipeline (specific pipeline)
/app/contacts                   Contacts list
/app/contacts/new               Quick-add contact
/app/contacts/:id               Contact detail
/app/activities                 Activity timeline (list/timeline toggle)
/app/email                      Email (inbox/sent/starred)
/app/reports                    Reports (dashboard + forecast)

/app/settings                   Settings hub
/app/settings/profile
/app/settings/team
/app/settings/pipelines         <<< NEW — pipeline editor
/app/settings/custom-fields
/app/settings/integrations
/app/settings/security
/app/settings/api-keys
/app/settings/audit-log
```

> **Note:** `/app/` prefix optional — could be flat routes as today. The `/app/` grouping makes it easier to add role-based guards (public routes outside `/app/`, authenticated routes inside).

### 2.4 Redundant Routes to Consolidate

| Current | Action | Target |
|---------|--------|--------|
| `/activities` | Remove | → `/app/activities` (or merge into single `/activities`) |
| `/timeline` | Remove | → `/activities` with view toggle |
| `/settings/users` | Remove sidebar link | → `/settings/team` |
| `/settings/audit-log` | Remove sidebar link | → `/settings/audit-log` (inside Settings tabs) |
| `/settings/integrations/slack` | Remove sidebar link | → `/settings/integrations` (Slack as integration card) |
| `/forecast` | Remove standalone route | → `/reports?tab=forecast` (already has a tab) |

---

## 3. Low-Fidelity Wireframes

### 3.1 Improved Sidebar / Layout

**Current layout:**
```
┌──────────┬──────────────────────────────────────────┐
│ 60px (lg)│  Header (h-16): search, theme, user      │
│ w-240px  ├──────────────────────────────────────────┤
│ (hidden  │  Main content                             │
│  < 1024) │  p-3 sm:p-4 lg:p-6                       │
│          │                                           │
│ 12 nav   │                                           │
│ items    │                                           │
│          │                                           │
│          │                                           │
└──────────┴──────────────────────────────────────────┘
```

**Proposed layout:**
```
┌─────┬──────────────────────────────────────────────────────┐
│     │  Header (h-14 compact): search 🔍 | [+] Quick Add    │
│ 48px├──────────────────────────────────────────────────────┤
│ (lg)│  Breadcrumb + Page Title                              │
│     ├──────────────────────────────────────────────────────┤
│ Icon│                                                      │
│ only│  Main content (max-w-7xl mx-auto)                    │
│     │  p-4 sm:p-6 lg:p-8                                    │
│ 7   │                                                      │
│ key │                                                      │
│ nav │                                                      │
│     │                                                      │
│ ────┤                                                      │
│ User│                                                      │
└─────┴──────────────────────────────────────────────────────┘
```

**Changes:**
1. **Collapsed state becomes default on desktop** — icons-only sidebar (48px) reveals labels on hover. Saves 160px+ of horizontal space.
2. **7 nav items instead of 12** — removed duplicates and Settings sub-pages.
3. **Tooltip on hover** shows nav label when collapsed.
4. **Floating "Quick Add" button** (`+`) appears in header or as a FAB on main pages.
5. **Breadcrumb** added above page title for context (e.g., `Contacts > Acme Corp`).
6. **Max-width container** (`max-w-7xl`) on main content prevents ultra-wide line lengths on large monitors.

```
┌──────────┐
│  ┌──┐   │
│  │F │   │  FrontierCRM  [Collapse]
│  └──┘   │
│ ────── │
│  🏠    │  Dashboard    ○ active
│  📈    │  Pipeline
│  👥    │  Contacts
│  📅    │  Activities
│  ✉️    │  Email
│  📊    │  Reports
│  ⚙️    │  Settings
│ ────── │
│  👤    │  Demo User
│        │  demo@...
└──────────┘

[Hover: label slides out to the right]
```

### 3.2 Streamlined Deal Creation Flow

**Current flow:** Click "Add Deal" → modal with 6 fields → submit → back to pipeline.

```
┌───────────────────────────────────────────┐
│  Add Deal                              ✕  │
│  ───────────────────────────────────────  │
│  Create a new deal in the pipeline        │
│                                           │
│  Deal Name*          [________________]   │
│  Value ($)*          [________________]   │
│  Company             [________________]   │
│                                           │
│  Pipeline            [Sales Pipeline ▼]   │
│  Stage               [Qualified ▼]        │
│                                           │
│  Expected Close Date [____/____/____]     │
│                                           │
│              [Cancel] [Create Deal]       │
└───────────────────────────────────────────┘
```

**Proposed — Inline quick-create (1-step):**

```
┌──────────────────────────────────────────────┐
│  Quick Create Deal                        ✕  │
│  ───────────────────────────────────────────  │
│                                               │
│  Deal Name*          [____________________]  │
│  Value*              [________]  USD [$ ▼]   │
│                                               │
│  Contact             [Search contacts... 📇]  │
│                       ┌─ Acme Corp ─────────┐ │
│                       │ John Smith          │ │
│                       │ VP of Engineering   │ │
│                       └─────────────────────┘ │
│                                               │
│  Stage               [Qualified ▼]            │
│                                               │
│            [Cancel]  [Create]  [Create + Add] │
└──────────────────────────────────────────────┘
```

**Improvements:**
1. **Contact selector** replaces free-text "Company" field — search existing contacts or create on-the-fly.
2. **Currency picker** next to value (USD default, dropdown for others).
3. **"Create + Add" button** — creates deal and opens another blank form for rapid batch entry.
4. **Inline stage dropdown** only (pipeline is inferred from active view — no need to select if coming from Pipeline page).
5. **Tab from deal detail** — alternatively, clicking a pipeline column header could reveal a compact inline form:

```
┌─────────────────────────────┐
│  Qualified             3    │  ┌─ Click column header ──┐
│  $150k                     │  │                        │
│ ──────────────────────────│  │  + New Deal             │
│ ┌─────────────────────┐   │  │  [________________]     │
│ │ Acme Corp - $50k   │   │  │  Name                   │
│ └─────────────────────┘   │  │  [________]             │
│ ┌─────────────────────┐   │  │  Value                  │
│ │ Beta Inc - $100k   │   │  │  [+] Enter...           │
│ └─────────────────────┘   │  │  Contact                │
│                           │  │  [Save] [Cancel]       │
│                           │  │                        │
└─────────────────────────────┘ └────────────────────────┘
```

### 3.3 Better Contact-Detail Information Hierarchy

**Current layout:**
```
┌──────────────────────────────────────────────────┐
│  Contact Name                                     │
│  ──────────────── Breadcrumb ───────────────────  │
│                                                    │
│  [Avatar]  Alex Chen                  [Edit][Del]  │
│            alex@acme.com                           │
│                                                    │
│  [Overview] [Activity] [Deals] [Notes] [Emails]   │
│  ───────────────────────────────────────────────── │
│                                                    │
│  ┌─ Contact Info ────────────┐  ┌─ Job Details ─┐ │
│  │ ✉️ Email: alex@acme.com  │  │ Job Title     │ │
│  │ 📞 Phone: +1234567890    │  │ Department    │ │
│  │ 📍 Address: 123 Main St  │  └───────────────┘ │
│  │ 🏢 Account: Acme Corp    │  ┌─ Social & Web ─┐ │
│  │ 🏷️ Tags: [VIP] [Tech]   │  │ LinkedIn       │ │
│  │ 👤 Owner: unassigned     │  │ Twitter        │ │
│  │ 🌐 Source: Referral      │  └───────────────┘ │
│  │ 📅 Created: Jun 1, 2026   │                    │
│  └───────────────────────────┘                    │
└──────────────────────────────────────────────────┘
```

**Proposed layout — Information-hierarchy focused:**
```
┌──────────────────────────────────────────────────┐
│  Contacts  >  Acme Corp  >  Alex Chen            │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │  [Avatar]  Alex Chen         [📞 Call] [✉️] │ │
│  │            VP of Engineering                 │ │
│  │            alex@acme.com                     │ │
│  │            Acme Corp  [Tag:VIP] [Tag:Tech]  │ │
│  │                                              │ │
│  │  ┌─ Deal Summary ─────────────────────────┐ │ │
│  │  │  Active Deal: Enterprise Contract      │ │ │
│  │  │  $50,000 · Stage: Negotiation · 80%    │ │ │
│  │  │  Last activity: 2d ago (Call)          │ │ │
│  │  └────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  [Overview] [Activity] [Deals] [Notes] [Emails]   │
│                                                    │
│  ┌─ Key Details ─────────────────────────────────┐ │
│  │  ✉️  alex@acme.com  ·  📞  +1234567890       │ │
│  │  📍  123 Main St, SF, CA                      │ │
│  │  🏢  Acme Corp  ·  💼  VP of Engineering      │ │
│  └────────────────────────────────────────────────┘ │
│                                                    │
│  ┌─ Recent Activity (3) ──┐ ┌─ Open Deals ──────┐ │
│  │ 📞 Call (2d ago)       │ │ Enterprise         │ │
│  │ ✉️ Email sent (5d ago) │ │ Contract · $50k    │ │
│  │ 📝 Note added (1w ago) │ │                    │ │
│  │                        │ │                    │ │
│  └────────────────────────┘ └────────────────────┘ │
│                                                    │
│  ┌─ Details (collapsible) ───────────────────────┐ │
│  │  ▶ Show all fields (Department, Source, ...)  │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

**Improvements:**
1. **Deal Summary card at top** — the most important context for a sales rep: "what deal do I have with this person?" No more switching between tabs.
2. **Action buttons visible without scrolling** — Call, Email buttons in the header area.
3. **Key Details collapsed into one row** — email and phone on same line saves vertical space.
4. **Recent Activity preview right in the overview** — no need to switch to Activity tab for a quick look.
5. **Open Deals side-by-side** — quick glance at deal value and stage.
6. **Detail fields collapsed** — long lists of metadata (source, created date, owner) are secondary and expandable.

### 3.4 Dashboard Redesign

**Current layout:**
```
┌──────────────────────────────────────────────────┐
│  Dashboard                                        │
│  ──────────── Gradient Hero Banner ────────────── │
│  Welcome back! Here's your pipeline overview.     │
│                                                    │
│  ⚠️ [4 deals need attention]  [View Reports]      │
│                                                    │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │
│  │Total │ │Won   │ │Win   │ │Active│             │
│  │Pipe  │ │Deals │ │Rate  │ │Deals │             │
│  │ $0   │ │ $0   │ │  0%  │ │  0   │             │
│  │No data│ │No data│ │No data│ │No data│             │
│  └──────┘ └──────┘ └──────┘ └──────┘             │
│                                                    │
│  ┌─ Pipeline by Stage ──┐ ┌─ Recent Activity ──┐ │
│  │  [Bar Chart]         │ │ 📝 Note added      │ │
│  │  No pipeline data    │ │ 📞 Call logged      │ │
│  │  yet                 │ │ ✉️ Email sent       │ │
│  └──────────────────────┘ └─────────────────────┘ │
│                        ┌─ Tasks Due ─────────────┐ │
│                        │ 🔴 Urgent: Close deal   │ │
│                        │ 🟡 High: Call back      │ │
│                        └─────────────────────────┘ │
│                                                    │
│  [View Contacts] [View Pipeline] [View Reports]    │
└──────────────────────────────────────────────────┘
```

**Proposed redesign — Role-aware, information-rich:**

```
┌──────────────────────────────────────────────────┐
│  Dashboard                              [Nov 2026│
│  ──────────────────────────────────────────────── │
│                                                    │
│  ┌─ My Focus ────────────────────────────────────┐ │
│  │  Good morning, Alex!  🎯 87% to quota ($870k) │ │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━░░ 87%       │ │
│  │  This month: $870k of $1M goal                 │ │
│  │                               [View Forecast]  │ │
│  └────────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │
│  │Active│ │Stale │ │Tasks │ │ Won  │             │
│  │Deals │ │Deals │ │Due   │ │ThisM │             │
│  │  12  │ │   3  │ │   2  │ │$120k │             │
│  │ +2 vs│ │ ⚠️ 1  │ │ 🔴 1  │ │ +15% │             │
│  │lastM │ │overdue│ │overdue│ │      │             │
│  └──────┘ └──────┘ └──────┘ └──────┘             │
│                                                    │
│  ┌─ Pipeline by Stage ──────────────────┐ ┌──────┐│
│  │  ┌──┬──┬──┬──┬──┐                    │ │Stale ││
│  │  │██│  │  │  │  │                    │ │Deals ││
│  │  │██│██│  │  │  │                    │ │••••• ││
│  │  │██│██│██│  │  │                    │ │Acme  ││
│  │  │██│██│██│██│██│                    │ │$50k  ││
│  │  │Qual|Dev|Neg|Cls|Won              │ │2w    ││
│  │  └──┴──┴──┴──┴──┘                    │ │••••• ││
│  │                         [View Full]  │ │      ││
│  └──────────────────────────────────────┘ └──────┘│
│                                                    │
│  ┌─ Next Actions ─────────────────────────────────┐│
│  │  📞 Call John Smith (Acme) — Deal stuck 5d     ││
│  │  ✉️ Send proposal to Beta Inc — Due tomorrow   ││
│  │  📝 Follow up with Jane (TechCo) — 3d overdue  ││
│  │                                        [Dismiss]││
│  └────────────────────────────────────────────────┘│
│                                                    │
│  ┌─ Recent Activity ───────┐ ┌─ Upcoming ────────┐│
│  │ 📞 Called Acme (2h ago) │ │ 📅 Demo at 2pm    ││
│  │ ✉️ Sent proposal (1d)  │ │ 📅 QBR Friday 10am││
│  │ 📝 Note on Beta (2d)    │ │                    ││
│  │                         │ │                    ││
│  └─────────────────────────┘ └────────────────────┘│
└──────────────────────────────────────────────────┘
```

**Improvements:**
1. **Personalised greeting + quota progress bar** — instantly shows the rep where they stand.
2. **"My Focus" section** replaces the gradient hero banner (wasted space). Shows quota progress with a visual progress bar.
3. **Next Actions list** — AI-powered or rule-based: "Call John Smith — deal stuck 5 days". This is the most useful thing for Alex: she doesn't need to scan the pipeline to find what needs attention.
4. **Metric cards reordered** — Active Deals first (most important), then warning metrics (Stale, Tasks), then positive (Won).
5. **Stale deals panel** replaces the red banner — shows actual deals with owner and amount, not just a count.
6. **Calendar integration** — Upcoming events shown directly on dashboard.
7. **Empty state for new users** — no pipeline data shows a friendly "Let's add your first deal" card with a guided CTA instead of "No data" badges.
8. **Role-aware** — Manager sees team overview, not just personal metrics.

---

## 4. Responsive Behaviour Summary

| Screen | Current | Proposed |
|--------|---------|----------|
| **Desktop (1280+)** | Full sidebar (w-60) + content | Collapsible mini-sidebar (w-12) + full content |
| **Tablet (768-1023)** | Sidebar visible (hidden md:flex) | Collapsible sidebar — overlay when open |
| **Mobile (<768)** | Overlay sidebar (w-72) | Slide-in drawer (w-64) + bottom tab bar |
| **Desktop content** | Fluid width | Max-w-7xl centred |
| **Tablet content** | Fluid, stacks vertically | Fluid with 2-col grids |
| **Mobile content** | Single column, compressed | Single column, full-width |

---

## 5. Implementation Priorities

| Priority | Change | Effort | Impact | Notes |
|----------|--------|--------|--------|-------|
| **P0** | Remove duplicate Activities/Timeline routes | Small | Medium | Quick win, reduces confusion |
| **P0** | Add contact picker to Add Deal modal | Medium | High | Removes free-text data entry |
| **P0** | Move Settings sub-pages out of sidebar | Small | Medium | Cleans up navigation |
| **P1** | Collapsible mini-sidebar | Medium | Medium | Saves horizontal space |
| **P1** | Inline Kanban quick-edit | Medium | High | Pipeline power-up |
| **P1** | Deal Summary on contact overview | Medium | High | Key context at a glance |
| **P1** | Dashboard quota progress bar | Small | High | Motivation boost |
| **P1** | Dashboard "Next Actions" list | Medium | High | Reduces daily scan time |
| **P2** | Pipeline management UI in Settings | Large | High | Enables admin self-service |
| **P2** | Role-aware dashboard | Medium | High | Manager-specific view |
| **P2** | Quick activity logging (FAB) | Medium | High | Reduces logging friction |
| **P2** | Period-over-period report comparison | Medium | Medium | Better analysis |
| **P3** | Breadcrumb navigation | Small | Medium | Context on deep pages |
| **P3** | Keyboard shortcuts (g+p, g+c, g+d) | Small | Medium | Power user speed |
| **P3** | Saved report views | Medium | Medium | Manager time saver |

---

*This IA document is informed by app exploration (localhost:5173), code analysis of pages/components, the existing ui-ux-pro-max-audit.md, and the persona briefs + journey maps produced in the same session. All wireframe descriptions are text-based — ready for visual design handoff. Version 1.0 — 2026-06-30.*