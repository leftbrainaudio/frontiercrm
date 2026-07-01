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

### Calendar Event Creation (v1.3.0)

Create events in Google Calendar directly from the CRM. Events appear on both your Google Calendar and in the CRM's event list.

**To create an event:**
1. Open a deal or contact.
2. Click the **Calendar** tab or use the event creation button.
3. Set the title, date/time, description, and add attendees.
4. Click **Create Event** — the event is pushed to Google Calendar and linked to the CRM entity.

**To edit:** Open the event from the CRM and update it. Changes sync to Google Calendar.

**To delete:** Remove the event from the CRM — it's removed from Google Calendar too.

Events created here appear alongside synced events in a unified CRM calendar view.

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

### Two-Factor Authentication (v1.3.0)

Add an extra layer of security to your account with TOTP-based 2FA.

**Setup:**
1. Go to **Settings → Security**.
2. Click **Enable 2FA**.
3. Scan the QR code with your authenticator app (Google Authenticator, Authy, 1Password, etc.).
4. Enter the 6-digit code from your app to confirm setup.
5. **Save your recovery codes** — 8 one-time-use codes. Store them somewhere safe. Each code can be used once if you lose access to your authenticator.

**Login with 2FA:**
1. Enter your email and password as usual.
2. On the 2FA prompt, enter the 6-digit code from your authenticator app.
3. If you don't have your phone, click **Use recovery code** and enter one of the 8 codes.

**Disable 2FA:** Settings → Security → **Disable**. You'll be asked to confirm with your current TOTP code.

**Regenerate recovery codes:** Settings → Security → **Regenerate codes**. This invalidates all previous codes.

If you lose access to both your authenticator and recovery codes, contact an admin. They can reset your 2FA from the admin panel.

### Custom Fields (v1.3.0)

Add custom fields to contacts, deals, and accounts to capture information specific to your business.

**Field types:**
- **Text** — free-form text input
- **Number** — numeric values
- **Date** — date picker
- **Select** — drop-down with predefined options

**Manage fields:**
1. Go to **Settings → Custom Fields**.
2. Click **+ Add Field**.
3. Choose the entity type (contacts, deals, or accounts), field type, and name.
4. For Select fields, add the option list.
5. Click **Save**.

Custom fields appear on the contact detail page, deal cards in the pipeline, and account detail pages. They can be filled in during create/update.

### Bulk Operations (v1.3.0)

Perform actions on multiple contacts, deals, or accounts at once.

**Select items:**
1. Go to the Contacts, Pipeline, or Accounts page.
2. Click the checkbox on any row to select it. The batch action toolbar appears.
3. Select individual items, or click **Select all** to choose everything on the current page.
4. The **Select All Banner** offers one-click selection of every item across all pages.

**Available batch actions:**
| Action | Description |
|--------|-------------|
| **Delete** | Confirmation dialog shows count; deletes all selected items |
| **Assign** | Move ownership to another team member |
| **Change Stage** | (Deals only) Move deals to a new pipeline stage |
| **Change Status** | (Deals only) Bulk set deal status (won/lost/abandoned) |
| **Add Tag** | Add a tag to all selected items |
| **Remove Tag** | Remove a tag from all selected items |
| **Replace Tags** | Replace all tags on selected items with a new set |

Progress tracking: a progress bar shows the status of async bulk jobs.

### Email Templates (v1.3.0)

Create reusable email templates with variable substitution for faster email composition.

**Manage templates:**
1. Go to **Email → Templates** (`/email/templates`).
2. Click **+ New Template**.
3. Enter a name, subject, and body.
4. Use **variables** to personalise: click the **Insert Variable** button to add placeholders like `{{contact.first_name}}`, `{{deal.name}}`, `{{account.name}}`, or `{{user.full_name}}`.
5. Categorise templates (e.g. "follow-up", "proposal", "onboarding") and save.

**Use a template:**
1. Open the compose modal from the email page.
2. Click **Pick Template** — a selector shows available templates.
3. Select a template. The subject and body are populated with the template content.
4. Variables are resolved automatically based on the linked contact, deal, or account.

### API Keys (v1.3.0)

Generate API keys for programmatic access to the FrontierCRM API (scripts, CI/CD, integrations).

**Manage keys:**
1. Go to **Settings → API Keys**.
2. Click **+ Create Key**.
3. Give the key a name (e.g. "CI Deploy Token").
4. Optionally set scopes and an expiry date.
5. Click **Create** — the plaintext key is shown **exactly once**. Copy and store it securely.

**Revoke a key:** From the API Keys page, click the key's **Revoke** button. Revoked keys cannot be re-activated.

**Delete a key:** Permanently removes the key record.

**API key format:** `fcrm_` followed by a 40-character alphanumeric string.

**Authentication:** Pass the key in the `Authorization: Bearer fcrm_<key>` header. API key auth does not require 2FA — suitable for automated workflows.

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
A: Yes. Go to Settings → Custom Fields to add text, number, date, or select fields to contacts, deals, and accounts. Custom fields appear on detail pages and deal cards.

## Keyboard shortcuts

Coming in a future release.

## Browser support

- Chrome 120+
- Firefox 120+
- Safari 17+
- Edge 120+