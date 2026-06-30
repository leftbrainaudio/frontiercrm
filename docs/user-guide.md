# User Guide — FrontierCRM

Get started and make the most of your CRM.

## Quickstart

### 1. Sign up

1. Go to https://app.frontiercrm.com
2. Click **Sign up**. Enter your name, email, password, and organization name.
3. You land on the **Dashboard** — your command centre.

### 2. Add a contact

1. Click **Contacts** in the sidebar.
2. Click **+ Add Contact**.
3. Fill in the name, email, phone, company, job title.
4. Click **Save**.

### 3. Create a deal

1. Click **Pipeline** in the sidebar.
2. Click **+ Add Deal**.
3. Name the deal, link it to a contact, set the value.
4. Drag it between stages (Qualified → Proposal → Negotiation → Closed).

### 4. Log an activity

1. Open a contact or deal.
2. Click the **Activity** tab.
3. Log a call, note, meeting, or email.

### 5. Sync email

1. Go to **Settings → Integrations**.
2. Click **Connect Gmail**.
3. Authorize with your Google account. Your Gmail inbox syncs to contact records.

### 6. Invite your team

1. Go to **Settings → Team**.
2. Click **Invite member**. Enter their email.
3. Choose a role and team. They join your organization.

## Feature guide

### Dashboard

The dashboard shows a snapshot of your pipeline health:

- **Total pipeline value** — sum of all open deal values
- **Won value** — deals closed this period
- **Win rate** — percentage of deals won vs lost
- **Active deals** — deals currently in open stages
- **Average deal value** — mean value across all deals
- **Deals by stage** — breakdown of value and count per pipeline stage
- **Tasks due** — count of overdue/upcoming tasks
- **Recent deals** — last 5 deals updated

### Contacts

The contacts module stores people and companies.

**People** — first name, last name, email, phone, mobile, job title, department, LinkedIn, Twitter, address, tags, custom fields.

**Companies** (Accounts) — name, domain, industry, website, phone, address, employee count, annual revenue, tags, custom fields.

Contacts can be linked to accounts (company). A contact belongs to one account.

### Pipeline

Visual sales pipeline with drag-and-drop kanban board.

**Pipelines** — you can create multiple pipelines (e.g. Sales, Upsell, Partnership). Each pipeline has stages.

**Stages** — each stage has a name, display order, win probability (0–100%), and colour. Default pipeline: Qualified → Proposal → Negotiation → Closed Won/Closed Lost.

**Deals** — each deal lives in one stage of one pipeline. Track value, expected close date, probability override, description, tags.

**Win probability** — by default uses the stage probability. Can be overridden per deal. Weighted value = deal value × win probability.

### Activities

A unified timeline across all entities. Each contact, deal, and account has an activity feed.

Activity types: note, call, email, meeting, task, deal stage change, deal status change, file upload, system.

Filter activities by type, date range, or entity.

### Email

Connect Gmail via OAuth to sync email into FrontierCRM.

Features:
- Inbound and outbound email sync
- Email linked to contacts (by matching email addresses)
- Thread view
- Starred and read/unread tracking
- Labels
- **Email compose (v1.1.0)** — compose and send email from the CRM via Gmail API
  - Open the compose modal from the email page
  - Fill in recipients, subject, and body
  - Click **Send** — the email is created and sent asynchronously
  - Status shows "Sending..." with a spinner — polls every 2s
  - On success: modal closes, green toast "Email sent", email appears in Sent tab
  - On failure: red toast with error message, "Retry" or "Save as Draft" options
  - Requires Gmail to be connected in Settings → Integrations

### Activities — Timeline (v1.1.0)

A unified org-wide activity feed at **/timeline**. Shows all activities across every entity type in one scrollable feed.

- **Date groups** — activities grouped by day (Today, Yesterday, This Week, Older)
- **Type icons** — colour-coded icons per activity type (note, call, email, meeting, etc.)
- **Actor info** — name and avatar of who performed the action
- **Entity links** — clickable links to the related deal, contact, account, or email

**Filters:**
| Filter | What it does |
|--------|-------------|
| Date range | Presets: Today, This Week, This Month, Custom range |
| Activity type | Show only emails, only stage changes, etc. |
| Actor | Filter to one team member's activity |

**Dashboard widget** — the dashboard shows the latest 10 timeline items with a "View full timeline" link.

**Entity drill-down** — contact detail pages and deal modals link to the timeline pre-filtered to that entity.

### Pipeline Forecasting (v1.1.0)

A dedicated **Forecast** page at **/forecast** for revenue projections.

**Three projection models:**
1. **Simple weighted** — `Σ(deal.value × stage.probability)` for all open deals
2. **Win-rate adjusted** — weighted pipeline multiplied by your historical win rate
3. **Velocity-based** — deals grouped by estimated close month, using historical stage velocity

**What-if scenarios:** pick a pipeline stage and a hypothetical close rate to see the projected upside. Useful for "what if we close 80% of Negotiation deals?"

**Confidence levels:**
| Level | Effect |
|-------|--------|
| Conservative | Projections × 0.8 |
| Medium | Projections × 1.0 (default) |
| Optimistic | Projections × 1.15 |

**Per-deal breakdown:** a table shows every open deal with its probability weight, projected value, and estimated close date.

### Export (v1.1.0)

Export your CRM data as CSV from the pipeline and contacts pages.

**Available exports:**
|| Export | What's included |
||--------|----------------|
|| Contacts CSV | Name, email, phone, job title, company, owner, tags |
|| Deals CSV | Deal name, value, stage, probability, owner, close date |
|| Pipeline report CSV | Stage-by-stage breakdown with deal count and total value |

Exports are streaming — large datasets download progressively. All files are tenant-scoped (your data only).

### Calendar Sync (v1.2.0)

Connect your Google Calendar to see events linked to your contacts and deals.

**Setup:**
1. Go to Settings → Integrations.
2. Click **Connect Google Calendar**.
3. Authorize with your Google account (same account as Gmail sync).
4. Once connected, calendar events sync every 15 minutes.

**What gets synced:**
- Events from the last 90 days and next 30 days
- Event title, description, start/end time, and participants
- Events are linked to contacts by matching participant email addresses
- Activity entries are created for each synced event — visible on the related contact's timeline

**Manual sync:** You can trigger a sync from the integration status panel.

### Slack Notifications (v1.2.0)

Get real-time pipeline notifications in Slack when deals move or activities are logged.

**Setup:**
1. Create an **Incoming Webhook** in your Slack workspace:
   - Go to https://api.slack.com/messaging/webhooks
   - Click **Create Incoming Webhook**
   - Select the channel to post to
   - Copy the webhook URL (starts with `https://hooks.slack.com/services/`)
2. In FrontierCRM, go to Settings → Integrations → Slack.
3. Paste the webhook URL and optionally:
   - **Channel override** — post to a different channel than the webhook's default
   - **Event filter** — only get notifications for deal stage changes, won/lost, or specific activity types
   - **Pipeline filter** — only notify on deals in a specific pipeline

**Notifications trigger when:**
- A deal changes stage (e.g. Qualified → Proposal)
- A deal is won, lost, or abandoned
- An activity (note, call, email, meeting) is logged on a deal or contact

### Progressive Web App (v1.2.0)

FrontierCRM can be installed on your phone or desktop as a standalone app — no app store required.

**Install on Android (Chrome):**
1. Open https://app.frontiercrm.com in Chrome.
2. Tap the menu (three dots) → **Add to Home screen**.
3. Tap **Install**.

**Install on iOS (Safari):**
1. Open https://app.frontiercrm.com in Safari.
2. Tap the **Share** button.
3. Scroll down and tap **Add to Home Screen**.
4. Tap **Add**.

**What the PWA gives you:**
- Full-screen standalone app (no browser chrome)
- App icon on your home screen
- Offline-capable: previously visited pages load from cache
- Background data cache for faster load times

### Tasks

Task management with priority and assignee.

Priorities: low, medium, high, urgent.
Statuses: todo, in_progress, done, cancelled.

Tasks can be linked to entities (contact, deal, account).

### Notes

Free-form notes with markdown support. Notes can be attached to any entity.

### Search

Global full-text search powered by Meilisearch. Searches contacts (name, email, phone), deals (name, description), and tasks (title, description).

Prefix search: `alice` matches "Alice Smith", "Alice's Bakery".

## FAQ

**Q: Can I have multiple pipelines?**
A: Yes. Go to Pipeline → settings to create new pipelines and stages.

**Q: How do I reset my password?**
A: Use the Magic Link feature on the login page. Enter your email and you'll receive a sign-in link.

**Q: Is my data isolated from other users?**
A: Yes. FrontierCRM is multi-tenant. Your organization gets its own isolated workspace. No other tenant can see your contacts or deals.

**Q: How often does Gmail sync?**
A: Every 10 minutes via Celery Beat. You can also trigger a manual sync from Settings → Integrations.

**Q: How do I export my data?**
A: Go to the Pipeline or Contacts page and click the **Export** button. Downloads a CSV file with your data. Contacts, deals, and pipeline reports are all available for export.

**Q: What happens if I delete a contact?**
A: Contacts are soft-deleted (hidden from the UI, retained in the database for 30 days per backup retention). Deleted contacts can be restored by an admin.

**Q: Can I customize fields?**
A: Custom fields are supported on contacts, accounts, and deals via the `custom_fields` JSON field on the API. UI support is in development.

## Keyboard shortcuts

Coming in a future release.

## Browser support

- Chrome 120+
- Firefox 120+
- Safari 17+
- Edge 120+