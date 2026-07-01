# Persona Briefs — FrontierCRM

**Date:** 2026-06-30
**Author:** Creative (ALLSTARS Design)

> Three research-grounded personas representing FrontierCRM's core user segments. Each persona is built from observed behavioural patterns in the current app structure, UI audit findings, and common CRM user archetypes. These personas anchor the journey maps and IA recommendations.

---

## Persona 1: Alex Chen — Sales Representative (Power User)

> *"I need to move deals fast. If I have to click four times to log a call, I'll forget what the prospect said."*

### Demographics
| Attribute | Detail |
|-----------|--------|
| Age | 28 |
| Role | Mid-Market Sales Rep |
| Industry | Technology / SaaS |
| Tenure in role | 3 years |
| Technical comfort | High — uses CRM daily, power user of keyboard shortcuts |
| Devices | MacBook (primary), iPhone (mobile access between meetings) |
| CRM experience | Has used Salesforce, HubSpot, and Pipedrive |

### Goals & Motivations
- Meet monthly quota by moving deals through pipeline stages
- Log every interaction efficiently so nothing falls through the cracks
- Spend maximum time selling, minimum time entering data
- Quickly understand deal history before any call or meeting

### Behaviours & Patterns
- Starts the day by scanning her pipeline Kanban — which deals need attention today
- Frequently uses the global search to pull up a contact or deal without navigating menus
- Logs calls/meetings immediately after they happen (phone in one hand, laptop in the other)
- Relies on the activity timeline to remember what was discussed last week
- Gets frustrated when a form has unnecessary required fields or too much friction
- Often has 8+ browser tabs open — needs the CRM to be fast and focused

### Pain Points (Current FrontierCRM)

| Pain | Severity | Evidence |
|------|----------|----------|
| Add Deal modal has no contact selector — must type company name as free text | High | add-deal-modal.tsx: contact_name is a plain text input, not a picker |
| Pipeline Kanban has no inline quick-edit for deal value/stage | Medium | Must open full detail modal to edit |
| No shortcut to log a call directly from the contact's row in the table | High | Must navigate to contact detail, then Activity tab |
| Mobile sidebar takes over full screen — no quick access from phone | Medium | sidebar.tsx: mobile overlay is full-width w-72 |
| Search requires 2+ characters before showing results | Low | Debounce at 300ms / 2-char threshold |

### Frustrations
- "I hate typing in the same notes twice — once during the call and again into the CRM"
- "Why can't I drag a deal to 'Won' without opening a modal?"
- "I need a call log button right next to the contact name in the table"

### What Success Looks Like
- Able to log a call in < 10 seconds from the contact list view
- Drag-and-drop pipeline updates feel instant
- One glance at the dashboard tells her exactly which deals need attention today
- Keyboard navigation covers 90% of her daily actions

### Device & Usage Patterns
| Context | Device | Frequency | Session Length |
|---------|--------|-----------|----------------|
| Desk work | MacBook | 6-8x daily | 15-45 min each |
| Between meetings | iPhone | 3-4x daily | 2-5 min each |
| End-of-day review | MacBook | Once daily | 20-30 min |

---

## Persona 2: Monica Reyes — Sales Manager

> *"I need to see the truth — not a spreadsheet I have to build myself. If my team is stuck, I want to catch it before month-end."*

### Demographics
| Attribute | Detail |
|-----------|--------|
| Age | 42 |
| Role | Regional Sales Director |
| Industry | Financial Services |
| Tenure in role | 8 years (5 in management) |
| Technical comfort | Moderate — comfortable with dashboards, dislikes complex configuration |
| Devices | Windows laptop (day-to-day), iPad (in meetings) |
| CRM experience | Has administered Salesforce, used Tableau for reporting |

### Goals & Motivations
- Get an accurate, real-time forecast to report to leadership
- Identify coaching opportunities: which reps are stuck, which deals are stale
- Understand team performance trends without building custom reports
- Hold effective 1:1s backed by data, not gut feel

### Behaviours & Patterns
- Starts Monday morning reviewing the team's pipeline and forecast
- Checks the stale deals warning on the dashboard first thing
- Dives into the Reports page for trend analysis and win rates
- Uses the Forecast page to model scenarios before leadership calls
- Reviews the Audit Log periodically for compliance
- Prefers summary views with drill-down capability over data-dense tables
- Gets frustrated when reports show data without context (raw numbers but no trend)

### Pain Points (Current FrontierCRM)

| Pain | Severity | Evidence |
|------|----------|----------|
| Forecast page is separate from Reports — requires mental context switch | Medium | Reports has a tab for forecast, but setting it up requires multiple filter selections |
| No team-member filter on dashboard — can only see aggregate data | High | Dashboard is global, no per-rep breakdown |
| Reports page has many filters (pipeline, group-by, date range) without saved presets | Medium | Each visit requires re-selecting filters |
| No ability to compare current period vs previous period side-by-side | High | Trends show change % but no overlay |
| Stale deals warning is visible but has no action to reassign or nudge | Medium | Shows count but no quick action |

### Frustrations
- "I spend 20 minutes every Monday building the report my VP wants. Can I save this view?"
- "The dashboard shows me my numbers but not my team's — I need to see each rep individually"
- "Why can't I just tap a stale deal and reassign it?"

### What Success Looks Like
- A single "Team Overview" dashboard with per-rep metrics (deals, value, activity count)
- Saved report views that she can name and recall
- Forecast page that surfaces risks (e.g., "3 deals at risk of slipping this quarter")
- Exportable reports that match what her VP expects to see

### Management Cadence
| Activity | Frequency | Tools Used |
|----------|-----------|------------|
| Team pipeline review | Weekly (Monday AM) | Dashboard, Pipeline Kanban |
| Forecast update | Bi-weekly | Forecast page |
| 1:1 coaching calls | Weekly per rep | Contact detail, Activity tab |
| Leadership report | Monthly | Reports page, export CSV |
| Compliance check | Quarterly | Settings > Audit Log |

---

## Persona 3: Jordan Taylor — CRM Admin / Onboarder

> *"I set this up so everyone else can work. If the pipeline stages don't match how we sell, the reps won't use it."*

### Demographics
| Attribute | Detail |
|-----------|--------|
| Age | 35 |
| Role | RevOps Manager / CRM Administrator |
| Industry | Technology (B2B SaaS) |
| Tenure in role | 4 years |
| Technical comfort | High — comfortable with API keys, webhooks, integrations |
| Devices | MacBook Pro (primary), personal phone |
| CRM experience | Administered HubSpot, Salesforce, close.io |

### Goals & Motivations
- Get new team members productive within their first day
- Configure pipelines, stages, and custom fields to match the company's sales process
- Set up integrations (email, calendar, Slack) so data flows automatically
- Ensure data quality through custom validation rules and required fields
- Manage user roles, permissions, and security settings

### Behaviours & Patterns
- Configures the system before handing it off to the team
- Spends most time in Settings — custom fields, integrations, API keys
- Runs through the onboarding wizard when setting up a new tenant
- Tests new configurations with test data before rolling out to the team
- Monitors the audit log for unusual activity
- Gets frustrated when configuration options are buried or require code changes

### Pain Points (Current FrontierCRM)

| Pain | Severity | Evidence |
|------|----------|----------|
| Custom fields can be created but there's no validation rules (required, format) | High | custom-fields-page.tsx: basic CRUD, no validation config |
| No pipeline management UI (create/edit/delete pipelines) | High | Pipelines seem to be seeded data only |
| User roles are not configurable from settings | Medium | settings-page.tsx: invite members but no role picker |
| Onboarding wizard has no "review all settings" before finalising | Low | Steps are sequential, no summary step |
| Integration setup (Slack, Calendar, Gmail) is scattered across Settings tabs | Medium | Multiple tabs with different integration types |
| No data import template or field mapping UI | High | ImportDataStep is a stub — no actual data import flow |

### Frustrations
- "I need to add a 'Close Reason' dropdown with our custom values. Where's the field editor?"
- "Every new hire needs the same onboarding. Can I create a template?"
- "The audit log shows me what changed, but not who changed it — that's half the story"

### What Success Looks Like
- A single "Configuration" section with pipeline management, custom fields, and validation rules
- Import/export tools with field mapping (map CSV columns to CRM fields)
- Role-based permissions that can be assigned at invite time
- Integration setup that's guided (OAuth flow with clear success/failure feedback)
- Bulk operations: invite multiple users, assign roles, set permissions

### Setup & Maintenance Cadence
| Activity | Frequency | Tools Used |
|----------|-----------|------------|
| Initial tenant setup | One-time | Onboarding wizard |
| Custom field management | Weekly (early), monthly (later) | Settings > Custom Fields |
| User management | As needed (new hires, departures) | Settings > Team |
| Integration maintenance | Monthly | Settings > Integrations |
| Security audit | Quarterly | Settings > Security, Audit Log |
| Pipeline adjustments | Quarterly | (Missing — no UI for this) |

---

## Persona Comparison Matrix

| Dimension | Alex (Sales Rep) | Monica (Sales Manager) | Jordan (Admin) |
|-----------|-----------------|----------------------|----------------|
| **Primary mode** | Daily operations | Weekly/monthly oversight | Configuration & maintenance |
| **Time in app** | 2-4 hours/day | 30-60 min/day | 1-2 hours/week (bursty) |
| **Key pages** | Pipeline, Contacts, Dashboard | Reports, Forecast, Dashboard | Settings, Users, Audit Log |
| **Wants speed** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Wants data fidelity** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Wants configurability** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Mobile reliance** | High (between meetings) | Medium (meeting review) | Low (desk-bound work) |

---

*These personas are synthesised from app exploration, UI audit findings, and common CRM user research patterns. They should be validated against real user interviews before being treated as definitive. Version 1.0 — 2026-06-30.*