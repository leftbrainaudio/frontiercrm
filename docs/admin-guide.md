# Admin Guide — FrontierCRM

This guide covers administrative tasks for FrontierCRM: settings, team management, integrations, and billing.

## Settings

Available from the sidebar → **Settings** (/settings).

### Profile

Update your personal profile:

- Avatar
- Name
- Email
- Phone
- Timezone
- Locale

Changes save immediately on the `GET/PATCH /api/accounts/me/` endpoint.

### Organization settings

Organization-wide settings (owner and admins only):

- **Organization name** — shown on invoices, team member emails
- **Timezone** — default timezone for the tenant (affects activity timestamps, scheduled tasks)
- **Locale** — default language for the tenant

## Team management

Settings → **Team**.

### Roles

Roles control what a user can do. Default roles:

| Role | Description | Can manage settings? | Can invite members? |
|------|-------------|---------------------|---------------------|
| Owner | Full access. Created at signup. | Yes | Yes |
| Admin | Full access except delete tenant | Yes | Yes |
| Member | Standard access | No | No |
| Viewer | Read-only access to contacts and deals | No | No |

Custom roles can be created with granular permissions:

```json
{
  "name": "Sales Manager",
  "description": "Can manage deals and team",
  "permissions": {
    "contacts:write": true,
    "deals:write": true,
    "reports:view": true,
    "team:view": true,
    "settings:read": false
  }
}
```

### Inviting members

1. Go to Settings → Team → **Invite member**.
2. Enter the member's email.
3. Choose a role.
4. Assign to a team (optional).
5. Click **Send invite**.

The member receives an email with a sign-up link. Once they create an account, they join your tenant.

### Teams

Teams group members together. Use them to organize by department (Sales, Marketing, Support).

```bash
# Create a team via API
curl -X POST https://api.frontiercrm.com/api/teams/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Sales","description":"Sales team"}'
```

### Removing a member

1. Settings → Team → find the member.
2. Click **Remove**.
3. Confirm.

Removing a member revokes their access. Their data remains in the tenant (contacts they created, deals they owned) — owned by the tenant, not the individual.

## Integrations

Settings → **Integrations**.

### Gmail / Google Workspace

Connect Gmail to sync email to contact records.

1. Click **Connect Gmail**.
2. Authorize with your Google account.
3. FrontierCRM requests the `gmail.modify` scope (read, send, and modify messages).

Once connected:
- Inbound/outbound emails sync every 10 minutes.
- Emails are linked to contacts by matching the sender/recipient email address.
- Each user's Gmail sync is independent (per-user OAuth tokens).
- **Email compose (v1.1.0):** users can send email from the CRM compose modal. Gmail must be connected — sends fail with a clear error if no connection exists.

To disconnect: Settings → Integrations → **Disconnect**.

### Google Calendar

Sync calendar events to contact activity timelines — **v1.2.0**.

1. Click **Connect Google Calendar**.
2. Authorize with your Google account.
3. FrontierCRM requests the `calendar.events.readonly` scope (read-only event access).

Once connected:
- Events sync every 15 minutes via Celery Beat (`sync_all_calendars` task).
- Sync window: 90 days past, 30 days future.
- Uses Google Calendar syncToken for efficient delta sync — falls back to time-range full sync if token expires (410 response).
- Event participants are matched to contacts by email address within the tenant.
- Each event creates an `Activity` record with type `event` and metadata stored in `Activity.metadata` JSONField.
- Tokens refresh automatically when expired.

**Calendar uses the same Google OAuth credentials (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET) as Gmail sync** — no additional environment variables required. The `calendar.events.readonly` scope is additive and does not require re-consent for existing Gmail connections.

### Slack Notifications (v1.2.0)

Slack notifications can be configured per tenant via the UI or API. Unlike infrastructure alerts (below), these are user-managed webhook configurations.

**To add a webhook:**
1. Create an **Incoming Webhook** in Slack: https://api.slack.com/messaging/webhooks
2. In FrontierCRM, go to Settings → Integrations → Slack.
3. Paste the webhook URL.
4. Optionally configure:
   - **Display name** — a label for this webhook in the UI
   - **Channel override** — post to a specific channel (defaults to the webhook's Slack-configured channel)
   - **Subscribed events** — list of activity types to notify on. Leave empty for all events
   - **Pipeline filter** — only notify on deals in a specific pipeline

**How it works:**
- When an Activity is created (deal stage change, activity logged, etc.), the `deliver_slack_notifications` Celery task fires.
- The task checks all active webhooks in the activity's tenant against the subscription and pipeline filters.
- Matching webhooks receive a Slack Block Kit message with formatted details.
- Rate limiting: 1 request/second per webhook URL.
- Auto-deactivation: a webhook is deactivated after 10 consecutive delivery failures.

**API management:**
```bash
# List webhooks
GET /api/slack/webhooks/

# Create a webhook
POST /api/slack/webhooks/
{
  "webhook_url": "https://hooks.slack.com/services/T00/B00/xxx",
  "display_name": "Sales Alerts",
  "subscribed_events": ["deal_stage_change", "deal_status_change"],
  "is_active": true
}

# Update or delete
PATCH /api/slack/webhooks/{id}/
DELETE /api/slack/webhooks/{id}/
```

### Infrastructure alerts (Slack)

Slack alerts are configured via environment variables (requires Fly.io deploy):

```bash
flyctl secrets set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/... --app frontiercrm-api
```

Alerts are sent to the configured channel for:
- 5xx error rate > 1% in 5 minutes
- p99 latency > 1s sustained for 5 minutes
- Celery task failure rate > 5%
- Database connection pool exhaustion
- Fly.io machine crash/restart

## Outbound Webhook Delivery Engine (v1.3.0)

The outbound webhook delivery engine automatically fires webhook events when Deals, Contacts, or Activities are created or updated.

### How it works

1. A **signal handler** detects changes: `Deal.post_save`, `Contact.post_save`, `Activity.post_save`
2. The **`WebhookDeliveryService`** enriches the payload with hydrated data (full deal with stage/owner, contact with account, etc.)
3. Payloads are signed with **HMAC-SHA256** and the signature is sent in the `X-Signature-256` header
4. Events are dispatched to all matching `WebhookEndpoint` URLs configured for the tenant
5. Delivery uses exponential backoff: 60s / 120s / 240s (3 retries total)
6. Events that exhaust all retries land in `WebhookDeadEvent` — the dead-letter queue

### Verifying webhook payloads

Consumers can verify that a webhook payload genuinely came from FrontierCRM:

```python
import hmac, hashlib

secret = b"<your_webhook_secret>"
payload = request.body
received_sig = request.headers["X-Signature-256"]

expected_sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
if hmac.compare_digest(expected_sig, received_sig):
    print("Verified — payload is from FrontierCRM")
```

### Dead events management

| Action | API |
|--------|-----|
| List dead events | `GET /api/webhooks/dead-events/` |
| View dead event detail | `GET /api/webhooks/dead-events/{id}/` |
| Replay a dead event | `POST /api/webhooks/dead-events/{id}/replay/` |

Dead events are kept until resolved or pruned. Automated cleanup:
- `retry_stale_webhooks` — runs every 5 minutes, retries events past `next_retry_at`
- `prune_dead_events` — runs daily at 03:00 UTC, removes resolved/stale entries

### Creating a webhook endpoint

```bash
POST /api/webhooks/
{
  "url": "https://hooks.example.com/crm-events",
  "secret": "your-webhook-secret",
  "subscribed_events": ["deal.created", "deal.updated", "contact.created"],
  "is_active": true
}
```

Rich payload example (deal created):

```json
{
  "event": "deal.created",
  "timestamp": "2026-06-30T15:00:00Z",
  "tenant_id": "uuid",
  "data": {
    "id": "uuid",
    "name": "Acme Corp Deal",
    "value": "50000.00",
    "stage": {"name": "Proposal", "probability": 60},
    "pipeline": {"name": "Sales Pipeline"},
    "owner": {"email": "alice@example.com", "full_name": "Alice Smith"},
    "contact": {"name": "Bob Jones", "email": "bob@acme.com"}
  }
}
```

## Two-Factor Authentication Admin (v1.3.0)

### Resetting a user's 2FA

If a user loses access to both their authenticator app and recovery codes, an admin can reset their 2FA:

```bash
POST /api/auth/2fa/admin/reset/{user_id}/
Authorization: Bearer <admin_token>
```

This disables 2FA for the user. They must set up 2FA again from Settings → Security.

Only users with admin-level roles can perform this action.

## API Keys Management (v1.3.0)

### Managing keys from the admin panel

API keys are managed per-user via Settings → API Keys. Key characteristics:

| Property | Value |
|----------|-------|
| Format | `fcrm_` + 40-character alphanumeric |
| Storage | SHA-256 hashed (plaintext not retrievable) |
| Expiry | Optional — keys can be set to auto-expire |
| Scopes | Optional permission scopes |

**Best practices:**
- Create separate keys for each integration
- Set expiry dates for temporary integrations
- Rotate keys periodically
- Revoke keys immediately when an integration is decommissioned
- Never share keys in logs or commit them to source control

### Auditing key usage

API key requests are logged in the audit log with `auth_method: apikey`. Review the audit log to track which keys are being used and by which integrations.

## Audit Log (v1.3.0)

The audit log provides a searchable record of all changes made in the system.

### Frontend

Available at **Settings → Audit Log** (`/settings/audit-log`):

| Column | Description |
|--------|-------------|
| Timestamp | When the action occurred |
| User | Who performed the action |
| Action | What was done (created, updated, deleted) |
| Entity Type | Which resource was affected (contact, deal, account, etc.) |
| Entity Name | The specific resource name |
| Details | Additional context (field changes, values) |

**Filters:**
- **Entity type** — filter to one resource type
- **Action** — show only creates, updates, or deletes
- **Date range** — start and end date picker

Action types are colour-coded: create (green), update (blue), delete (red). Active filters show as removable chips with a "Clear All" option.

### API

```bash
# List audit log entries (paginated)
GET /api/accounts/audit-log/?page=1&page_size=50

# Filter by entity type
GET /api/accounts/audit-log/?entity_type=contact

# Filter by action
GET /api/accounts/audit-log/?action=created

# Filter by date range
GET /api/accounts/audit-log/?start_date=2026-06-01&end_date=2026-06-30
```

## Export (v1.1.0)

CSV export is available from the Pipeline and Contacts pages. Exports are tenant-scoped (only this organization's data). The download is a streaming CSV — files start downloading immediately even for large datasets.

Available exports:
- **Contacts CSV** — first name, last name, email, phone, mobile, job title, department, address, account name, owner, tags, created/updated timestamps
- **Deals CSV** — name, value, currency, status, pipeline, stage, probability, weighted value, expected close date, contact, account, owner, tags, entered stage at, created/updated timestamps
- **Pipeline report CSV** — pipeline name, stage name, deal count, total value, probability

### Sentry (error tracking)

Sentry is configured via the `SENTRY_DSN` environment variable:

```bash
flyctl secrets set SENTRY_DSN=https://key@o<org>.ingest.sentry.io/<project> --app frontiercrm-api
```

Captures:
- Unhandled exceptions
- Celery task failures
- Performance traces (10% sample rate)

### Healthchecks.io (uptime monitoring)

Configured via `HEALTHCHECKS_IO_URL`:

```bash
flyctl secrets set HEALTHCHECKS_IO_URL=https://hc-ping.com/<uuid> --app frontiercrm-api
```

The Celery Beat process sends a heartbeat ping every 5 minutes. If no ping for 15 minutes, Healthchecks.io alerts you.

## Monitoring

Admin dashboard links:

| Service | URL | Purpose |
|---------|-----|---------|
| Sentry | https://sentry.io/organizations/<org>/frontiercrm/ | Error tracking |
| Fly.io Dashboard | https://fly.io/apps/frontiercrm-api | Infrastructure |
| Healthchecks.io | https://healthchecks.io/ | Uptime monitoring |
| Cloudflare R2 | Cloudflare Dashboard | File storage |

## Billing / Usage

The MVP uses a simple model:

- **Trial**: 14 days, unlimited users
- **Standard**: $X/user/month, billed monthly
- **Enterprise**: Custom pricing

Usage metrics available via API:

```bash
# Current usage
GET /api/accounts/usage/

# Response
{
  "users_count": 12,
  "contacts_count": 342,
  "deals_count": 89,
  "storage_bytes": 15728640,
  "api_calls_this_month": 8472
}
```

## Data retention

| Data type | Retention |
|-----------|-----------|
| Active records | Until deleted by user |
| Soft-deleted records | 30 days (matching backup retention) |
| Backups | 30 days in Cloudflare R2 |
| Logs | 7 days (Fly.io) |
| Error events | 90 days (Sentry free tier) |

## Managing the tenant via API

Admin endpoints for tenant management:

```bash
# Get tenant details
GET /api/accounts/tenant/

# Update tenant settings
PATCH /api/accounts/tenant/
{
  "name": "Acme Corp",
  "timezone": "America/New_York",
  "locale": "en-US"
}

# List all members
GET /api/accounts/memberships/

# Get audit log
GET /api/accounts/audit-log/

# Reset user 2FA (admin only)
POST /api/auth/2fa/admin/reset/{user_id}/
Authorization: Bearer <admin_token>
```

## Security checklist

- [ ] All secrets set via `flyctl secrets` (not in env files or code)
- [ ] SSL enforced (HSTS preload enabled in production settings)
- [ ] CORS origins restricted to your app domains
- [ ] Rate limiting enabled (1000/hour per user)
- [ ] Sentry DSN configured for error tracking
- [ ] Regular backups configured (Celery Beat runs daily)
- [ ] Staff/Superuser accounts limited to ops team
- [ ] Google OAuth scopes limited to `gmail.modify` (not full mail access)