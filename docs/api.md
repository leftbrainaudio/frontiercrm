# API Documentation — FrontierCRM

The FrontierCRM API is a RESTful JSON API. Base URL: `https://api.frontiercrm.com/api/`.

## OpenAPI schema

An auto-generated OpenAPI 3.0 schema is available at:

```
GET /api/schema/
```

The browsable API is at:

```
GET /api/docs/
```

## Authentication

All API requests (except auth endpoints) require a JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Get tokens

```bash
# Signup (creates account + returns tokens)
curl -X POST https://api.frontiercrm.com/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","username":"alice","password":"supersecret1!","first_name":"Alice","last_name":"Smith","organization_name":"Acme Corp"}'
```

Response (201 Created):

```json
{
  "user": {"id": "uuid", "email": "alice@example.com", ...},
  "access": "eyJhbG...jwt.access.token...",
  "refresh": "eyJhbG...jwt.refresh.token..."
}
```

```bash
# Login
curl -X POST https://api.frontiercrm.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"supersecret1!"}'
```

### Refresh token

Access tokens expire after 30 minutes. Refresh with:

```bash
curl -X POST https://api.frontiercrm.com/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token>"}'
```

Response:

```json
{"access": "new.jwt.access.token"}
```

### Magic link

Request a passwordless sign-in link:

```bash
curl -X POST https://api.frontiercrm.com/api/auth/magic-link/request/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com"}'
```

Confirm the link:

```bash
curl -X POST https://api.frontiercrm.com/api/auth/magic-link/confirm/ \
  -H "Content-Type: application/json" \
  -d '{"token":"<token_from_email>"}'
```

### Google OAuth

1. Get the authorization URL:

```bash
curl https://api.frontiercrm.com/api/auth/google/init/
```

2. Redirect the user to the returned `authorization_url`.
3. Exchange the code for tokens:

```bash
curl -X POST https://api.frontiercrm.com/api/auth/google/callback/ \
  -H "Content-Type: application/json" \
  -d '{"code":"<authorization_code>"}'
```

### Logged-in user profile

```bash
curl https://api.frontiercrm.com/api/accounts/me/ \
  -H "Authorization: Bearer <token>"
```

## Rate limiting

| Role | Limit | Applied to |
|------|-------|------------|
| Anonymous | 100 requests/hour | Auth endpoints |
| Authenticated | 1,000 requests/hour | All endpoints |

429 Too Many Requests responses include a `Retry-After` header (seconds).

## Multi-tenant isolation

Every user belongs to a tenant (organization). All data is isolated by tenant:

- A user sees only records belonging to their tenant.
- On signup, a tenant is created and the user becomes its owner.
- Tenant ID is embedded in the JWT token; not passed in the request body.

**Endpoints that bypass tenant isolation**: auth (signup, login, magic link).

## Pagination

All list endpoints return paginated results.

Default: 25 items per page. Configure via `?page_size=` (max 100).

```
GET /api/contacts/?page=2&page_size=50
```

Response:

```json
{
  "count": 142,
  "next": "https://api.frontiercrm.com/api/contacts/?page=3&page_size=50",
  "previous": "https://api.frontiercrm.com/api/contacts/?page=1&page_size=50",
  "results": [...]
}
```

## Filtering, search, ordering

Most list endpoints support:

**Filtering** (exact match on fields):
```
GET /api/contacts/?tags__contains=enterprise
GET /api/deals/?status=open&pipeline=<pipeline_id>
```

**Search** (case-insensitive contains):
```
GET /api/contacts/?search=alice
GET /api/deals/?search=acme
```

**Ordering**:
```
GET /api/contacts/?ordering=last_name
GET /api/deals/?ordering=-created_at
GET /api/deals/?ordering=pipeline_name,stage_name
```

## Key endpoints

### Auth

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/signup/` | None | Create account + tenant |
| POST | `/api/auth/login/` | None | Email + password login |
| POST | `/api/auth/token/refresh/` | None | Refresh access token |
| POST | `/api/auth/magic-link/request/` | None | Request magic link |
| POST | `/api/auth/magic-link/confirm/` | None | Confirm magic link |
| GET | `/api/auth/google/init/` | None | Google OAuth URL |
| POST | `/api/auth/google/callback/` | None | Google OAuth callback |

### Accounts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, PATCH | `/api/accounts/me/` | Get/update current user profile |
| GET | `/api/accounts/` | List users in tenant |
| GET, POST | `/api/accounts/roles/` | List or create roles |
| GET, PATCH, DELETE | `/api/accounts/roles/:id/` | Get/update/delete a role |
| GET, POST | `/api/accounts/memberships/` | List or invite members |

### Contacts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/contacts/` | List contacts |
| POST | `/api/contacts/` | Create a contact |
| GET | `/api/contacts/:id/` | Get contact detail |
| PATCH | `/api/contacts/:id/` | Update contact |
| DELETE | `/api/contacts/:id/` | Delete contact (soft) |

### Accounts (companies)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/contacts/accounts/` | List accounts |
| POST | `/api/contacts/accounts/` | Create an account |
| GET | `/api/contacts/accounts/:id/` | Get account detail |
| PATCH | `/api/contacts/accounts/:id/` | Update account |
| DELETE | `/api/contacts/accounts/:id/` | Delete account |

### Pipelines & Deals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/deals/` | List deals |
| POST | `/api/deals/` | Create a deal |
| GET, PATCH, DELETE | `/api/deals/:id/` | Deal CRUD |
| GET | `/api/deals/pipelines/` | List pipelines |
| POST | `/api/deals/pipelines/` | Create pipeline |
| GET, PATCH, DELETE | `/api/deals/pipelines/:id/` | Pipeline CRUD |
| GET, POST | `/api/deals/stages/` | List/create stages |
| GET, PATCH, DELETE | `/api/deals/stages/:id/` | Stage CRUD |

### Activities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/activities/` | List activities (paginated) |
| POST | `/api/activities/` | Log an activity |
| GET, PATCH, DELETE | `/api/activities/:id/` | Activity CRUD |

Activity types: `note`, `call`, `email`, `meeting`, `task`, `deal_stage_change`, `deal_status_change`, `file_upload`, `system`.

### Email

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/emails/` | List emails |
| GET | `/api/emails/threads/` | List email threads |
| GET | `/api/emails/:id/` | Get email detail |
| POST | `/api/emails/:id/send/` | Send a reply |
| GET | `/api/emails/sync/status/` | Sync status per user |

### Notes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notes/` | List notes |
| POST | `/api/notes/` | Create note |
| GET, PATCH, DELETE | `/api/notes/:id/` | Note CRUD |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks/` | List tasks |
| POST | `/api/tasks/` | Create task |
| GET, PATCH, DELETE | `/api/tasks/:id/` | Task CRUD |

Task priorities: `low`, `medium`, `high`, `urgent`.
Task statuses: `todo`, `in_progress`, `done`, `cancelled`.

### Teams

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/teams/` | List teams |
| POST | `/api/teams/` | Create team |
| GET, PATCH, DELETE | `/api/teams/:id/` | Team CRUD |
| POST | `/api/teams/:id/members/` | Add member to team |
| DELETE | `/api/teams/:id/members/:id/` | Remove member from team |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/webhooks/` | List webhooks |
| POST | `/api/webhooks/` | Create webhook |
| GET, PATCH, DELETE | `/api/webhooks/:id/` | Webhook CRUD |
| POST | `/api/webhooks/:id/test/` | Send test event |

### Files

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/files/` | List files |
| POST | `/api/files/` | Upload file (multipart) |
| GET | `/api/files/:id/` | Get file metadata |
| DELETE | `/api/files/:id/` | Delete file |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search/?q=<query>` | Full-text search (contacts, deals, tasks) |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/` | Liveness check |
| GET | `/api/health/ready/` | Readiness check (includes DB) |

## Error format

All errors return consistent JSON:

```json
{
  "detail": "Human-readable error message.",
  "code": "error_code"
}
```

Validation errors:

```json
{
  "field_name": ["This field is required."],
  "other_field": ["Ensure this value has at most 255 characters."]
}
```

## HTTP status code conventions

| Code | Meaning |
|------|---------|
| 200 | Success (GET, PATCH) |
| 201 | Created (POST) |
| 204 | Deleted (DELETE) |
| 400 | Bad request / validation error |
| 401 | Missing or invalid token |
| 403 | Not authorized (wrong tenant) |
| 404 | Not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Postman / Insomnia

Import the OpenAPI schema from `/api/schema/` into your API client for full endpoint discovery.