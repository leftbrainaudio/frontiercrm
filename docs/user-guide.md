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
A: Use the API. Contact list endpoints return JSON. We're working on CSV export.

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