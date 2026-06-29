# FrontierCRM MVP — Code Review & Security Audit

**Auditor**: allstars-auditor  
**Date**: 2026-06-28  
**Scope**: Entire codebase — backend (Django/DRF) + frontend (React/Vite)  
**Revision**: 4-pass review: Correctness → Security → Tests → Style/Scope

---

## BLOCKERS (must fix before deploy)

### B1. OAuth tokens stored in plaintext on User model

**File**: `backend/apps/accounts/models.py`, lines 30-31  
**Issue**: Google OAuth access and refresh tokens are stored as plain `TextField` on the `User` model:

```python
google_access_token = models.TextField(blank=True, default="")
google_refresh_token = models.TextField(blank=True, default="")
```

These tokens grant permanent access to the user's Gmail account (the `google_refresh_token` never expires without user revocation). If the database is compromised, every user's email is exposed. No encryption-at-rest is applied.

The tokens are written in `accounts/views.py` lines 186-193 (Google OAuth callback) and read/used in `email/tasks.py` lines 22-43 (`_refresh_google_token`) and lines 46-66 (`_gmail_get`) — making this a live attack surface.

**Fix**: Encrypt tokens with Django's `django-cryptography` or a custom `Fernet`-based encrypted field before storage. At minimum, use Django's `signing` module.

---

### B2. `dangerouslySetInnerHTML` with attacker-controlled HTML (XSS)

**File**: `frontend/src/pages/email/email-page.tsx`, line 259  
**Issue**: Email body HTML is rendered unsanitized:

```tsx
<div
  className="prose prose-sm max-w-none dark:prose-invert text-text-primary dark:text-dark-text-primary"
  dangerouslySetInnerHTML={{ __html: email.body_html }}
/>
```

`body_html` originates from the Gmail API via `email/tasks.py` lines 80-95 (`_parse_gmail_message`) and is stored as-is. An attacker who sends an email containing `<script>`, `<img onerror=...>`, or any malicious HTML/JS will have it rendered in the recipient's browser context when they view the email. React's JSX-based XSS protections are entirely bypassed by `dangerouslySetInnerHTML`.

**Fix**: Sanitize HTML with DOMPurify (`npm install dompurify`) before rendering:

```tsx
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(email.body_html) }} />
```

---

### B3. Production CORS allows only localhost origins

**File**: `backend/config/settings/production.py`  
**Issue**: `production.py` does NOT override `CORS_ALLOWED_ORIGINS` from `base.py`. The base setting is:

```python
CORS_ALLOWED_ORIGINS = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173".split(",")
```

In production, the actual frontend domain (e.g. `https://app.frontiercrm.com`) will be rejected by the CORS check. This is both a **security** issue (the setting is effectively dev-only when deployed) and a **functional** blocker (the app will not work in production).

**Fix**: `production.py` must set a production-specific `CORS_ALLOWED_ORIGINS` via env var:

```python
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if os.environ.get("CORS_ALLOWED_ORIGINS") else []
```

---

### B4. Gmail Pub/Sub push notification endpoint is unauthenticated

**File**: `backend/apps/email/push_views.py`, lines 16-49  
**Issue**: The `gmail_push_notification` view is `@csrf_exempt` and has no authentication or authorization check:

```python
@csrf_exempt
@require_POST
def gmail_push_notification(request: HttpRequest) -> JsonResponse:
```

Any external actor can POST to `/api/gmail-push/` with a JSON body containing an `emailAddress` and trigger `sync_gmail_history.delay()` for any user in the system. While Google Pub/Sub is the intended caller, there's no verification that the request came from Google (no JWT bearer token, no IP allowlist, no shared secret, no subscription verification).

**Fix**: Verify the Pub/Sub JWT assertion token from the `Authorization` header. Google Pub/Sub push deliveries include a signed JWT in the `Authorization: Bearer <token>` header that can be verified against Google's public keys.

---

### B5. Webhook receiver is wide-open (no inbound auth)

**File**: `backend/apps/webhooks/views.py`, lines 61-100  
**Issue**: The webhook receiver at (presumably) `/api/webhooks/receive/` is:

```python
@api_view(["POST"])
@permission_classes([AllowAny])
def webhook_receiver(request: Request) -> Response:
```

It accepts POSTs from any source. Signature verification is optional — it only checks if `endpoint.secret` is set AND a signature header is present. An endpoint without a secret (or an attacker who can replay requests) can inject arbitrary webhook events into the dispatch queue. The receiver also queries all active endpoints (`is_active=True`) without scoping to a tenant, meaning it's a global handler.

**Fix**: Require signature verification for all endpoints. If an endpoint has no secret configured, do NOT dispatch events. Consider also requiring HMAC verification on the inbound receiver using a shared system secret.

---

## MAJORS (fix before merging to main)

### M1. Magic link reveals if an email is registered (user enumeration)

**File**: `backend/apps/accounts/serializers.py`, lines 120-125

```python
def validate_email(self, value: str) -> str:
    try:
        UserModel.objects.get(email=value)
    except UserModel.DoesNotExist:
        raise serializers.ValidationError("No account with this email.")
```

An unauthenticated attacker can probe any email address to determine whether it's registered. The response error message confirms the email exists or not.

**Fix**: Always return a 200 response regardless of whether the email exists. The email should be sent only if the user exists; don't reveal the difference in the API response.

---

### M2. Password hashing uses default PBKDF2 (no argon2)

**File**: `backend/requirements.txt` (examined)  
**Issue**: The project doesn't install `argon2-cffi` or configure `PASSWORD_HASHERS`. Django defaults to PBKDF2HMAC-SHA256 with 600,000 iterations (Django 5.x default), which is acceptable but significantly weaker than argon2 for a CRM product storing customer data.

**Fix**: Add `argon2-cffi` to requirements and set `PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher", ...]` in settings.

---

### M3. File upload has no type/extension validation

**File**: `backend/apps/files/views.py`, lines 49-84

The `upload` action checks only `file.size > settings.FILE_UPLOAD_MAX_SIZE`. There is no MIME type whitelist or extension validation. The `presign_upload` action (lines 87-111) similarly accepts any filename and content_type. While S3 has `private` ACL, presigned URLs can be generated for any uploaded file.

An attacker could upload HTML files with XSS payloads, executable scripts, or other dangerous content that would later be served from S3.

**Fix**: Add a whitelist of allowed MIME types (`ALLOWED_UPLOAD_MIME_TYPES = ["application/pdf", "image/png", "image/jpeg", ...]`) and validate before upload. Validate file extension against an allowlist.

---

### M4. No Content Security Policy headers

**Files**: `backend/config/settings/base.py`, `backend/config/settings/production.py`  
**Issue**: Neither base nor production settings configure CSP headers. Production sets `SECURE_BROWSER_XSS_FILTER = True` (an outdated XSS filter, deprecated in modern browsers). Combined with the `dangerouslySetInnerHTML` issue (B2), there is no defense-in-depth against XSS.

**Fix**: Add `django-csp` to requirements and configure CSP headers in production:

```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:", "https://*.googleusercontent.com")
```

---

### M5. WebSocket ActivityConsumer has no tenant isolation

**File**: `backend/apps/core/consumers.py`, lines 30-44

```python
class ActivityConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self) -> None:
        self.entity_type = self.scope["url_route"]["kwargs"]["entity_type"]
        self.entity_id = self.scope["url_route"]["kwargs"]["entity_id"]
        self.group_name = f"activities_{self.entity_type}_{self.entity_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
```

Any authenticated user can connect to any entity's activity feed by specifying any `entity_type` / `entity_id` in the URL (e.g. `ws/activities/contact/00000000-0000-0000-0000-000000000000/`). There's no check that the entity belongs to the user's tenant.

**Fix**: Before accepting the connection, look up the entity and verify `tenant_id == user.tenant_id`.

---

### M6. Membership invite creates users with no password

**File**: `backend/apps/teams/views.py`, lines 76-90

```python
@action(detail=False, methods=["post"])
def invite(self, request) -> Response:
    user, _ = User.objects.get_or_create(email=email, defaults={"username": email.split("@")[0]})
```

Invited users are created with no password set. The username is auto-derived from the email. No email notification is sent to invite them. The user has no way to log in unless they already existed or use magic link (which requires knowing the email exists — see M1).

**Fix**: Generate a random password (or better, send a magic link / password-set email as part of the invite flow). At minimum, send an email notification.

---

### M7. Magic link token in email URL leaks through referrers

**File**: `backend/apps/accounts/views.py`, line 84

```python
link = f"{request.build_absolute_uri('/api/auth/magic-link/confirm/')}?token={user.magic_link_token}"
```

The magic link token is in a URL query parameter, which means:
- It leaks via the `Referer` header when the user clicks any link on the confirmation page
- It's stored in browser history
- It may appear in server access logs

**Fix**: Use a POST-based flow (send the token in the request body, not the URL), or use a fragment-based approach (`#token=...` which doesn't get sent as a Referer).

---

### M8. No email verification after signup

**File**: `backend/apps/accounts/views.py`, lines 30-49 (SignupView), `backend/apps/accounts/models.py` line 21
**Issue**: After signup, JWT tokens are issued immediately. The `email_verified` field exists but is never checked anywhere. Users can access the full application without verifying their email.

**Fix**: Require email verification before issuing JWT tokens (or at least before accessing sensitive features). Send a verification email on signup.

---

### M9. Test settings strip TenantMiddleware, masking integration bugs

**File**: `backend/config/settings/test.py`, line 18

```python
MIDDLEWARE = [m for m in MIDDLEWARE if "TenantMiddleware" not in m]
```

The TenantMiddleware is removed from the test chain. Tests validate `get_queryset` filtering (which is correct) but never test the JWT → tenant_id extraction that the middleware performs. If the middleware breaks (e.g. the JWT token extraction logic changes), no test catches it.

**Fix**: Keep TenantMiddleware in test settings. Tests should run through the full middleware chain.

---

### M10. No tests for email sync tasks or webhook dispatch

**Files**: `backend/tests/test_email.py`, `backend/tests/test_webhooks.py`  
**Issue**: The email test file covers only CRUD on the `EmailMessage` model — zero tests for `sync_gmail_messages`, `sync_gmail_history`, `_refresh_google_token`, `_gmail_get`, `_parse_gmail_message`, or `send_gmail_message`. The webhook tests likewise cover only CRUD on endpoints/events — zero tests for `webhook_receiver`, `dispatch_webhook`, `_retry_or_fail`, or `_compute_signature`.

These are the most security-critical and error-prone parts of the codebase.

---

## MINORS

### m1. `fail_silently=True` on magic link email suppresses errors

**File**: `backend/apps/accounts/views.py`, line 90

```python
send_mail(..., fail_silently=True)
```

If the email server is unreachable, the user gets neither a magic link nor an error message. The API returns 200 "Magic link sent" regardless.

### m2. `RATE_LIMIT_ENABLED` env var is dead code

**File**: `backend/config/settings/base.py`, line 235

```python
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "True") == "True"
```

This variable is never read anywhere. Rate limiting is always active via `DEFAULT_THROTTLE_CLASSES` in DRF config. Either remove the env var or actually condition on it.

### m3. Test assertions that accept anything

- `test_auth.py` line 455: `assert resp2.status_code in (200, 401)` — accepts any outcome
- `test_auth.py` line 155: `assert resp.status_code in (201, 400)` — accepts both success and failure

These "fence-post" assertions pass regardless of whether the code works correctly.

### m4. `ThreadLocal` class is dead code

**File**: `backend/apps/core/models.py`, lines 67-81

`ThreadLocal` class has `_local = {}` + `get()` returning `threading.local()`. It's never imported or used anywhere in the codebase. Should be removed.

### m5. Webhook `_retry_or_fail` uses `__import__()` instead of normal imports

**File**: `backend/apps/webhooks/views.py`, lines 113, 149-151

```python
last_attempt_at = __import__("django.utils.timezone", fromlist=["now"]).now()
```

This is functionally correct but needlessly obscure. Use standard `from django.utils import timezone` at module level.

### m6. No `SECURE_PROXY_SSL_HEADER` in production

**File**: `backend/config/settings/production.py`

If deployed behind a reverse proxy (Nginx, ELB, Cloudflare), Django needs `SECURE_PROXY_SSL_HEADER` to correctly detect HTTPS.

### m7. `useState` initializer used as side-effect in email detail

**File**: `frontend/src/pages/email/email-page.tsx`, lines 183-185

```tsx
useState(() => {
    handleMarkRead();
});
```

This calls a mutation inside a `useState` initializer, which:
- Is called twice in React 18+ Strict Mode
- Violates the principle that state initializers should be pure
- Should be `useEffect` instead

---

## NITS

### n1. Duplicate auth routes: `/api/accounts/me/` and `/api/auth/` split

The `me_view` is served at `/api/accounts/me/` (in `accounts/urls.py`) while all other auth views are at `/api/auth/*`. Minor inconsistency — either `/api/auth/me/` or `/api/accounts/me/` would be cleaner.

### n2. Migration 0001_initial exists for all apps but no subsequent migrations

All migrations are `0001_initial.py`. After the MVP review fixed several code issues (views.py, serializers), no new migrations were generated. If models were changed, this would cause schema drift in production.

### n3. No linting or type-checking CI gate visible

No `.github/workflows/` or CI config found. The frontend uses `oxlint` for linting (configured) but the backend has no `ruff`/`mypy` CI check enforced.

---

## LGTM (what's done right)

- **Multi-tenant isolation in viewsets**: Every viewset consistently filters by `tenant_id` in `get_queryset` and sets `tenant_id` in `perform_create`. Cross-tenant reads correctly return 404 (not 403), avoiding information leakage.
- **TenantAwarePermission**: Provides object-level isolation with a clear bypass mechanism for auth/public endpoints.
- **JWT configuration**: Reasonable token lifetimes (30min access, 7d refresh with rotation). Tenant_id is embedded in the JWT.
- **S3 storage**: Default ACL is `private`, file keys are prefixed with `tenant_id`, presigned URLs expire in 1 hour.
- **Soft-delete**: Consistent implementation across models via `TimeStampedModel`.
- **Webhook signature verification**: HMAC-SHA256 with payload+timestamp signing is implemented correctly.
- **CORS in base**: Uses explicit origin whitelist, not `CORS_ALLOW_ALL_ORIGINS` (correct for the base config).
- **Sentry integration**: Properly wired with Django+Celery integrations, disabled in dev/test.
- **Celery configuration**: Sensible timeouts (30min), JSON serialization, eager mode for tests.
- **Input validation**: DRF serializers handle input validation consistently; password min_length=8 on signup.
- **Frontend token management**: JWT stored in localStorage with automatic refresh interceptor and redirect on failure.
- **Frontend proxy config**: Vite proxies `/api` to the backend during development, avoiding CORS issues in dev.
- **Package choice**: Modern, maintained dependencies (axios, zustand, tanstack-query, react-router v7, vite 8).

---

## Summary

| Severity | Count | Key items |
|----------|-------|-----------|
| **BLOCKER** | 5 | OAuth tokens in plaintext, XSS via dangerouslySetInnerHTML, prod CORS broken, unauthenticated Gmail push endpoint, open webhook receiver |
| **MAJOR** | 10 | User enumeration, no argon2, no file type validation, no CSP headers, WebSocket tenant isolation gap, invite creates users without pass, magic link leaks via referrer, no email verification, test middleware stripping, untested email sync/webhook dispatch |
| **MINOR** | 7 | fail_silently masking errors, dead RATE_LIMIT_ENABLED env var, fence-post test assertions, dead ThreadLocal class, `__import__` abuse, missing SSL header, useState side-effect |
| **NITS** | 3 | Route naming consistency, no migration after code fixes, no CI gate |

**Recommendation**: Fix all 5 blockers before any production deployment. Address the 10 majors before merging the main branch. The minors and nits can be addressed incrementally without blocking.