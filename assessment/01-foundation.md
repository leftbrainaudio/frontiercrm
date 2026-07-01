# Phase 1: Foundation — App Overview, IA, Personas & Journey Maps

**Date:** 2026-06-30
**Skills applied:** user-centred-design, user-research, personas, journey-mapping, information-architecture, front-end-fluency
**Reference:** Builds on ui-ux-pro-max-audit.md (56 issues documented)

---

## 1. App Overview

FrontierCRM is a multi-tenant CRM platform for modern sales teams. It manages contacts, deals, pipelines, email, tasks, and activities. The stack is Django REST API + React SPA (Vite + Tailwind v4).

**Current state:** The app is functional but has significant gaps — several pages crash at runtime (Email, Slack settings, Users page, Audit Log page). Most content screens show empty states because the demo account has no seeded data.

### Screen Inventory

| Route | Page Component | State |
|-------|---------------|-------|
| `/login` | LoginPage | ✅ Functional |
| `/signup` | SignupPage | ✅ Functional |
| `/magic-link` | MagicLinkPage | ✅ Functional |
| `/auth/callback` | SocialCallbackPage | ✅ Functional |
| `/auth/saml/callback` | SamlCallbackPage | ✅ Functional |
| `/auth/two-factor-challenge` | TwoFactorChallengePage | ✅ Functional |
| `/onboarding` | OnboardingWizard | ✅ Functional |
| `/dashboard` | DashboardPage | ✅ Functional (empty data) |
| `/reports` | ReportsPage | ✅ Functional (empty data) |
| `/forecast` | ForecastPage | ✅ Functional (empty data) |
| `/contacts` | ContactListPage | ✅ Functional (empty data) |
| `/contacts/:id` | ContactDetailPage | ➖ Not tested (no contacts) |
| `/pipeline` | PipelinePage | ✅ Functional (empty data) |
| `/activities` | TimelinePage | ✅ Functional (empty data) |
| `/timeline` | TimelinePage | ✅ Functional (same as activities) |
| `/email` | EmailPage | ❌ **Crash: `connections?.find is not a function`** |
| `/email/templates` | EmailTemplatesPage | ➖ Untested |
| `/settings` | SettingsPage | ✅ Functional |
| `/settings/users` | UsersPage | ❌ **Crash: 404 Not Found** |
| `/settings/integrations/slack` | SlackSettingsPage | ❌ **Crash: 404 Not Found** |
| `/settings/audit-log` | AuditLogPage | ❌ **Crash: 404 Not Found** |
| `/settings/custom-fields` | CustomFieldsSettingsPage | ➖ Untested |

**3 pages crash at runtime** — this is the most urgent finding. The Email page error (`connections?.find is not a function` at line 335 of email-page.tsx) occurs because `useSyncConnections` returns data that is not an array, and the code calls `.find()` on it without a type guard. The Slack/Users/Audit Log pages are likely missing backend endpoints or the frontend route configuration is hitting the SPA catch-all instead of an existing page.

---

## 2. Information Architecture Map

The app splits cleanly into **auth flows** → **onboarding** → **app (with sidebar)**.

```
FrontierCRM
├── Auth (no sidebar)
│   ├── /login          — Email/password + Google OAuth + Microsoft OAuth + SSO + Magic Link
│   ├── /signup         — First name, Last name, Email, Org, Password
│   ├── /magic-link     — Magic link request
│   └── /auth/*         — OAuth/SAML/2FA callbacks
├── Onboarding (minimal layout)
│   └── /onboarding     — Company setup wizard
└── App (sidebar + topbar)
    ├── Dashboard       /dashboard    — Metric cards, pipeline chart, recent activity, tasks due
    ├── Reports         /reports      — Pipeline value, won deals, win rate, charts, funnel
    ├── Forecast        /forecast     — Revenue projections, what-if scenario modelling
    ├── Contacts        /contacts     — Table list with search, pagination, CSV export
    ├── Pipeline        /pipeline     — Kanban board with drag-and-drop, deals table
    ├── Activities      /activities   — Timeline with type/date filters, meeting creation
    ├── Timeline        /timeline     — Duplicate of Activities
    ├── Email           /email        — Gmail integration, inbox/sent/starred, compose
    │   └── Templates   /email/templates — Email template management
    ├── Settings        /settings     — Profile, Team, Security, Integrations, Custom Fields, API Keys
    │   ├── Users       /settings/users        — ❌ 404
    │   ├── Slack       /settings/integrations/slack — ❌ 404
    │   └── Audit Log   /settings/audit-log     — ❌ 404
    └── Hidden links (sidebar but likely broken)
        ├── Slack       /settings/integrations/slack — ❌ 404
        ├── Users       /settings/users              — ❌ 404
        └── Audit Log   /settings/audit-log           — ❌ 404
```

### IA Observations

1. **Timeline is a duplicate route** — `/timeline` and `/activities` render the same component (`TimelinePage`). This is confusing. Timeline should be a view within Activities or removed.
2. **Slack/Users/Audit Log are sidebar links to settings sub-routes** — all three crash with 404, indicating either missing frontend pages or missing backend API endpoints.
3. **No breadcrumbs** — the app relies entirely on sidebar navigation. Deep routes like `/email/templates` and `/contacts/:id` have no breadcrumb trail to help users orient.
4. **Settings is a flat page** — all settings sections (Profile, Team, Security, Integrations, Custom Fields, API Keys) render as sections on a single page rather than navigable sub-routes. This works for the current small surface but won't scale.
5. **Sidebar has 12 navigation links** — for an MVP CRM this is reasonable, but secondary items (Slack, Users, Audit Log) mix primary workflow navigation (Dashboard, Contacts, Pipeline) with admin/settings navigation.

---

## 3. Persona Briefs

Based on the app's feature set and target audience (modern sales teams), I've synthesised three primary personas from the existing product scope and interaction patterns:

### Persona 1: Sarah — Inside Sales Representative

| Attribute | Detail |
|-----------|--------|
| **Role** | Inside sales rep, mid-market |
| **Goals** | Log calls, track deals, see next actions |
| **Needs** | Fast email sync, pipeline drag-and-drop, activity logging |
| **Pain points** | Email page crashes; no data seeded; can't test workflow |
| **Tech comfort** | High — uses Gmail and Slack daily |
| **Frequency** | Daily, 4-6 hours in CRM |
| **Key screens** | Dashboard, Pipeline, Email, Contacts, Activities |

### Persona 2: Marcus — Sales Manager

| Attribute | Detail |
|-----------|--------|
| **Role** | Team lead, 8 reps reporting |
| **Goals** | Forecast accuracy, pipeline health, team performance |
| **Needs** | Reports, forecast modelling, team view, activity timeline |
| **Pain points** | Forecast shows $0 with no data; reports empty; no team management UI |
| **Tech comfort** | Moderate — needs clear data visualisations |
| **Frequency** | Daily, 2-3 hours in CRM |
| **Key screens** | Reports, Forecast, Dashboard, Activities/Timeline |

### Persona 3: Alex — Operations Admin

| Attribute | Detail |
|-----------|--------|
| **Role** | CRM administrator |
| **Goals** | Configure fields, manage users, audit activity, set up integrations |
| **Needs** | Custom fields, role-based access, audit log, Slack integration |
| **Pain points** | Settings/Users page crashes (404); Slack settings crashes (404); no audit log UI |
| **Tech comfort** | High — configures SaaS tools |
| **Frequency** | Weekly, 1-2 hours in CRM |
| **Key screens** | Settings (all subsections), Custom Fields, API Keys |

---

## 4. Key Journey Maps

### Journey 1: New User Onboarding

**Persona:** Sarah (Inside Sales Rep)
**Goal:** Sign up, set up company, start using CRM
**Emotion line:** 😐 → 🙂 → 😊 → 😟

| Phase | Actions | Thoughts | Pain Points |
|-------|---------|----------|-------------|
| **Discover** | Lands on login page | "I need to create an account" | Brand font (Inter) not applied |
| **Sign up** | Fills in first_name, last_name, email, password | "Standard signup — clean form" | No username autofill from email |
| **Onboard** | Company name + industry dropdown | "Quick setup, I like it" | Premium CRM features shown immediately |
| **Dashboard** | Sees metric cards, charts, activity | "Where's my data?" | **No demo data seeded** — all metrics show $0/empty |
| **Explore** | Navigates to Pipeline | "Let me add my first deal" | Pipeline shows "No deals yet" |
| **Try Email** | Opens Email page | "Let me connect Gmail" | **Page crashes** — "connections?.find is not a function" |
| **Result** | Cannot complete first day tasks | "This doesn't work yet" | 3 pages crash; no data to explore |

### Journey 2: Daily Deal Management

**Persona:** Sarah (Inside Sales Rep)
**Goal:** Update deal stages, log activities, manage pipeline
**Emotion line:** 😐 → 🙂 → 🤨 → 😟

| Phase | Actions | Thoughts | Pain Points |
|-------|---------|----------|-------------|
| **Login** | Enters credentials | "Quick — 2-step auth if enabled" | Branding not applied |
| **Dashboard** | Reviews pipeline metric | "Need to see my deals today" | No daily/weekly activity summary |
| **Pipeline** | Views kanban board | "Drag-and-drop — nice" | Empty state — no deals to practice with |
| **Activities** | Logs a call/meeting | "Let me record this meeting" | Timeline shows "No activity yet" |
| **Navigate** | Goes to Email | "Check if client replied" | **Crash** — can't access email |
| **Result** | Workflow broken | "I can't do my job through here" | Email integration is a core workflow blocker |

### Journey 3: Managerial Reporting

**Persona:** Marcus (Sales Manager)
**Goal:** Review team performance, create forecast, identify risks
**Emotion line:** 🙂 → 🤔 → 😟 → 😞

| Phase | Actions | Thoughts | Pain Points |
|-------|---------|----------|-------------|
| **Dashboard** | Views pipeline by stage chart | "Let's see how the team is doing" | Chart renders but no data |
| **Reports** | Opens Reports page | "I need real numbers" | All metrics $0, charts show no data |
| **Forecast** | Opens Forecast page | "Revenue projection — key feature" | $0 projected, no monthly breakdown |
| **What-If** | Adjusts scenario slider | "If we close 50%... $0" | No data means no useful scenarios |
| **Team** | Clicks Users in sidebar | "Need to check my reps" | **Crash** (404) |
| **Result** | Cannot manage team | "The analytics framework looks solid but unusable without data" | Complete tooling exists but no content |

---

## 5. Key Findings Summary

### Critical Issues (from this phase)

1. **❌ 3 pages crash at runtime** — Email (`connections?.find is not a function`), Slack settings (404), Users (404), Audit Log (404). This is the #1 user-facing blocker.
2. **❌ No demo/seed data** — Every content page shows empty states. A CRM cannot be evaluated without data. This is deliberate for MVP but blocks all downstream UX validation.
3. **❌ Duplicate routes** — `/timeline` and `/activities` render the same component. Confusing navigation.
4. **❌ No skip-to-content or keyboard landmarks** — The app lacks skip navigation links. Keyboard users must tab through all sidebar links before reaching main content.

### IA Recommendations

- **Eliminate duplicate `/timeline` route** — redirect to `/activities`
- **Add breadcrumbs** to deep pages (Contacts > Contact Detail, Email > Templates)
- **Structure Settings** as sub-routes (Settings > Profile, Settings > Security) rather than a flat page
- **Move Slack/Users/Audit Log** into a proper settings sub-navigation, not the main sidebar
- **Add a "Getting Started" wizard** that seeds demo data for new users

### Next Phase

Proceed to **Phase 2: Craft** — deep-dive into component code, design tokens, accessibility, responsive behaviour, and UX copy.