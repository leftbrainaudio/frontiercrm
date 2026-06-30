# Phase 5: Two-Factor Authentication & SSO/SAML Specification

**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)
**Status:** Draft
**Priority:** P2 (2FA) / P3 (SSO/SAML)

---

## Table of Contents

1. [ADR-027: 2FA via TOTP (Custom Implementation)](#1-adr-027-2fa-via-totp-custom-implementation)
2. [Data Model: 2FA Fields](#2-data-model-2fa-fields)
3. [2FA Login Flow (Sequence)](#3-2fa-login-flow-sequence)
4. [2FA REST API Contracts](#4-2fa-rest-api-contracts)
5. [Backup & Recovery](#5-backup--recovery)
6. [Frontend: 2FA Setup in Settings](#6-frontend-2fa-setup-in-settings)
7. [Frontend: 2FA Challenge Screen](#7-frontend-2fa-challenge-screen)
8. [ADR-028: SSO/SAML via python3-saml](#8-adr-028-ssosaml-via-python3-saml)
9. [Data Model: SamlProvider](#9-data-model-samlprovider)
10. [SAML Login Flows (Sequence)](#10-saml-login-flows-sequence)
11. [SAML REST API Contracts](#11-saml-rest-api-contracts)
12. [Just-In-Time User Provisioning](#12-just-in-time-user-provisioning)
13. [Frontend: IdP Config Page in Settings](#13-frontend-idp-config-page-in-settings)
14. [Implementation Order](#14-implementation-order)
15. [Acceptance Criteria](#15-acceptance-criteria)
16. [Open Questions / Spike Items](#16-open-questions--spike-items)

---

## 1. ADR-027: 2FA via TOTP (Custom Implementation)

**Status:** Proposed
**Date:** 2026-06-30

### Context

FrontierCRM needs two-factor authentication to meet enterprise security requirements. The existing login flow is:

1. User submits email + password (or magic link, or social OAuth)
2. Server verifies credentials
3. Server issues JWT (access + refresh) immediately

Adding 2FA means inserting a verification step between credential validation and JWT issuance. The design must accommodate:

- TOTP (Time-based One-Time Password) via authenticator apps (Google Authenticator, Authy, 1Password, etc.)
- Recovery codes for account lockout prevention
- Per-user opt-in (admins may enforce per-tenant)
- Settings UI for setup and management

### Options Considered

**Option A — django-otp plugin**
`django-otp` is the most popular Django library for TOTP, HOTP, and static tokens. It provides models, middleware, and admin integration.

- Pros: mature, well-tested, pluggable device types (TOTP, HOTP, static), middleware auto-challenge
- Cons: opinionated middleware model (globally enables OTP for all users, hard to disable per-user); device model is a separate table per device type; admin integration is Django-admin only; middleware's `is_verified` session-based approach conflicts with stateless JWT design; pulling in a full plugin for ~30 lines of TOTP math is heavy
- **Rejected** — JWT stateless design conflicts with django-otp's session-based `is_verified` middleware. We'd need custom code anyway to integrate with the 2-step JWT flow.

**Option B — Custom TOTP using pyotp library**
Use `pyotp` (a pure-Python TOTP library, 2KB, no deps beyond hashlib/base64). Store the TOTP secret and backup codes directly on the User model. Implement a short-lived `2fa_token` JWT for the challenge step.

- Pros: no model bloat (2 new fields on User), no middleware changes, explicit two-step JWT flow (no session dependency), pyotp is a single-file library with zero Django coupling, recovery codes stored as hashed values in a single JSONField
- Cons: needs to be careful with timing-safe comparison; no built-in admin UI for resetting 2FA
- **Accepted** — simpler data model, explicit JWT flow matches existing auth architecture, pyotp is minimal and auditable. Admin reset of 2FA is a one-endpoint addition.

**Option C — Third-party service (Authy/Twilio Verify)**
Outsource 2FA to a service that handles TOTP push, SMS fallback, and recovery.

- Pros: no crypto code to maintain, SMS fallback included, push notification option
- Cons: recurring cost per user; dependency on external service availability; users need to install another app (Authy) or share phone numbers; offline/air-gapped enterprise deployments break
- **Rejected** — TOTP via authenticator app is the industry standard for CRM; third-party services add cost and latency without corresponding value for internal/enterprise use

### Decision

**Custom TOTP implementation using `pyotp`, with fields on the User model, a short-lived `2fa_token` JWT for the two-step login, and hashed recovery codes.**

Key design points:

1. **Two-step JWT flow.** Password verification produces a short-lived `2fa_token` (5-minute expiry) instead of an access token. The client must exchange this `2fa_token` + TOTP code for real JWT tokens. This avoids any session state on the server.

2. **TOTP secret as a single field.** `totp_secret` is a `CharField` storing the base32-encoded secret. `pyotp.TOTP(secret).provisioning_uri()` generates the standard `otpauth://` URI for QR codes.

3. **Recovery codes stored as bcrypt hashes.** `recovery_codes` is a JSONField storing an array of bcrypt-hashed recovery codes. On verification, the matching hash is removed (one-time use). Ten codes generated per user.

4. **Tenant-level enforcement.** `Tenant.settings` gets a `require_2fa` boolean. When enabled, all members must have 2FA enabled to access the app. Non-2FA users are redirected to the setup page.

5. **Rate limiting.** TOTP verification endpoint is rate-limited to 5 attempts per minute per user to prevent brute-force of 6-digit codes.

---

## 2. Data Model: 2FA Fields

### User Model Additions (`apps/accounts/models.py`)

Add the following fields to the existing `User` model:

```python
class User(AbstractUser):
    # ... existing fields ...

    # ── 2FA / TOTP ───────────────────────────────────────────────────────────
    totp_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=64, blank=True, default="")
    totp_created_at = models.DateTimeField(null=True, blank=True)
    recovery_codes = models.JSONField(default=list, blank=True)
```

**Field details:**

| Field | Type | Description |
|---|---|---|
| `totp_enabled` | BooleanField, default=False | Whether the user has completed 2FA setup |
| `totp_secret` | CharField(64) | Base32-encoded TOTP secret. Generated by `pyotp.random_base32()`. Empty string = not set up. |
| `totp_created_at` | DateTimeField, nullable | When 2FA was enabled (for audit) |
| `recovery_codes` | JSONField, default=list | Array of bcrypt-hashed recovery codes. Max 10 codes. Only populated when 2FA is enabled. |

### No migration for existing users

Existing users will have `totp_enabled=False`. They continue to log in without 2FA.

### Tenant Settings Addition (`apps/teams/models.py`)

In the `Tenant` model's `settings` JSONField, add:

```json
{
  "require_2fa": false,
  "allowed_idp_domains": []
}
```

- `require_2fa` — when true, all members must have 2FA enabled. The backend checks `user.totp_enabled` after JWT authentication and returns a `428 Precondition Required` status if 2FA is not set up.

### pyotp Dependency

Add to `requirements.txt` / `pyproject.toml`:

```
pyotp>=2.9.0
```

Zero Django coupling — pyotp is pure Python from `pyotp import TOTP`.

---

## 3. 2FA Login Flow (Sequence)

### Sequence: Password → TOTP → JWT

```
Frontend                  Backend                        Authenticator App
   │                         │                                 │
   │  POST /auth/login/      │                                 │
   │  {email, password}      │                                 │
   │────────────────────────>│                                 │
   │                         │  Verify credentials             │
   │                         │  Check user.totp_enabled        │
   │                         │  ── if totp_enabled:            │
   │  {2fa_required: true,   │      Generate short-lived       │
   │   2fa_token: "..."}     │      2fa_token JWT (5 min)      │
   │<────────────────────────│                                 │
   │                         │                                 │
   │  (User opens authenticator app, reads TOTP)               │
   │                         │                                 │
   │  POST /auth/2fa/verify/ │                                 │
   │  {2fa_token, code}      │                                 │
   │────────────────────────>│                                 │
   │                         │  Validate 2fa_token             │
   │                         │  TOTP.verify(code, valid_window=1)│
   │                         │  ── if valid:                   │
   │  {access, refresh,      │      Generate access + refresh  │
   │   user: {...}}          │      Remove used 2fa_token from DB
   │<────────────────────────│                                 │
```

### Sequence: Password → Direct Login (2FA disabled)

```
Frontend                  Backend
   │                         │
   │  POST /auth/login/      │
   │  {email, password}      │
   │────────────────────────>│
   │                         │  Verify credentials             │
   │                         │  Check user.totp_enabled        │
   │                         │  ── if NOT totp_enabled:        │
   │  {access, refresh,      │      Generate access + refresh  │
   │   user: {...}}          │      (existing behavior)        │
   │<────────────────────────│
```

### Recovery Code Flow

```
Frontend                  Backend
   │                         │
   │  POST /auth/2fa/verify/ │
   │  {2fa_token,            │
   │   code: "ABCD-1234",    │
   │   is_recovery: true}    │
   │────────────────────────>│
   │                         │  bcrypt.checkpw(code, each hash)│
   │                         │  Remove matched hash from array │
   │                         │  Generate access + refresh      │
   │  {access, refresh,      │
   │   user: {...},          │
   │   remaining_codes: 9}   │
   │<────────────────────────│
```

### Social / Magic Link with 2FA

For social OAuth and magic link flows, the 2FA challenge is identical — those logins currently skip the password step but still authenticate the user, so the same `totp_enabled` check applies:

1. Social OAuth callback or magic link confirm authenticates the user
2. If `user.totp_enabled`, issue a `2fa_token` (same response shape)
3. Frontend shows TOTP challenge screen
4. User enters code → `POST /auth/2fa/verify/` → real JWT

---

## 4. 2FA REST API Contracts

### 4.1 POST /api/auth/2fa/setup/ — Initialize 2FA setup

**Authentication:** JWT required (user must be logged in)
**Rate limit:** 3 requests per hour per user

**Response 200:**

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "provisioning_uri": "otpauth://totp/FrontierCRM:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=FrontierCRM",
  "qr_code_svg": "<svg>...</svg>"
}
```

- `secret` — base32 secret for manual entry
- `provisioning_uri` — standard `otpauth://` URI for QR code rendering
- `qr_code_svg` — optional, inline SVG QR code (generated server-side via `qrcode` library or client-side via `qrcode.js`)

**Notes:**
- This endpoint generates a new secret and stores it in `user.totp_secret` but does NOT enable 2FA yet
- Calling this twice overwrites the previous secret and invalidates any previous setup steps

### 4.2 POST /api/auth/2fa/confirm/ — Confirm and enable 2FA

**Authentication:** JWT required
**Rate limit:** 10 attempts per minute per user

**Request:**

```json
{
  "code": "123456"
}
```

**Response 200:**

```json
{
  "detail": "Two-factor authentication enabled.",
  "recovery_codes": ["ABCD-1234", "EFGH-5678", ...]
}
```

**Response 400:**

```json
{
  "code": ["Invalid code. Please try again."]
}
```

**Notes:**
- Verifies the TOTP code against the stored `totp_secret`
- On success: sets `totp_enabled=True`, generates 10 random recovery codes, bcrypt-hashes them, stores in `recovery_codes`
- Returns the raw recovery codes **once** — the frontend MUST display them and prompt the user to save them
- Future calls to this endpoint return a 409 Conflict (2FA already enabled)
- Recovery codes format: `XXXX-XXXX` (uppercase alphanumeric, 4-4 split)

### 4.3 POST /api/auth/2fa/verify/ — Verify 2FA code during login

**Authentication:** `2fa_token` in request body (not JWT auth header)
**Rate limit:** 5 attempts per minute per user

**Request:**

```json
{
  "2fa_token": "eyJhbGciOiJIUzI1NiIs...",
  "code": "123456"
}
```

**Response 200 (on success):**

```json
{
  "access": "eyJhbGci...",
  "refresh": "eyJhbGci...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "avatar_url": "https://..."
  }
}
```

**Response 400 (bad code):**

```json
{
  "code": ["Invalid code."],
  "attempts_remaining": 4
}
```

**Alternate request (recovery code):**

```json
{
  "2fa_token": "eyJhbGciOiJIUzI1NiIs...",
  "code": "ABCD-1234",
  "is_recovery": true
}
```

**Notes:**
- The `2fa_token` is a short-lived JWT (5 min) encoding `{user_id, tenant_id, purpose: "2fa_challenge"}`
- Code is verified with `pyotp.TOTP(secret).verify(code, valid_window=1)` — tolerates ±1 step (30s clock drift)
- Recovery codes are matched via `bcrypt.checkpw()`. Matched hash is removed. Response includes `remaining_codes` count.
- On 5 failed attempts, the `2fa_token` is revoked and a new login is required (prevents infinite brute-force)

### 4.4 POST /api/auth/2fa/disable/ — Disable 2FA

**Authentication:** JWT required
**Rate limit:** 3 requests per hour per user

**Request:**

```json
{
  "password": "current-password",
  "code": "123456"
}
```

**Response 200:**

```json
{
  "detail": "Two-factor authentication disabled."
}
```

**Notes:**
- Requires re-verification of password + current TOTP code (or recovery code) to prevent accidental/token-snatch disable
- Clears `totp_secret`, `totp_enabled`, `recovery_codes`

### 4.5 POST /api/auth/2fa/recovery-codes/regenerate/ — Generate new recovery codes

**Authentication:** JWT required
**Rate limit:** 3 requests per day per user

**Request:**

```json
{
  "code": "123456"
}
```

**Response 200:**

```json
{
  "recovery_codes": ["NEW1-CODE", "NEW2-CODE", ...]
}
```

**Notes:**
- Requires current TOTP code to authorize
- Invalidates all old recovery codes
- Returns 10 new codes

### 4.6 GET /api/auth/2fa/status/ — Check if 2FA is required by tenant

**Authentication:** JWT required

**Response 200:**

```json
{
  "totp_enabled": true,
  "tenant_requires_2fa": false,
  "has_recovery_codes": true,
  "remaining_recovery_codes": 7
}
```

### 4.7 Admin endpoints (superuser only)

| Method | Path | Description |
|---|---|---|
| POST | `/api/admin/auth/2fa/reset/{user_id}/` | Admin forcibly resets another user's 2FA |
| GET | `/api/admin/auth/2fa/users/` | List users with 2FA status (for audit) |

---

## 5. Backup & Recovery

### Recovery Code Generation

```python
import secrets
import bcrypt

def generate_recovery_codes(n: int = 10) -> tuple[list[str], list[bytes]]:
    """Generate n recovery codes. Returns (raw_codes, hashed_codes)."""
    raw_codes = []
    hashed_codes = []
    for _ in range(n):
        code = f"{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
        raw_codes.append(code)
        hashed_codes.append(bcrypt.hashpw(code.encode(), bcrypt.gensalt()))
    return raw_codes, hashed_codes
```

### Recovery Code Verification

```python
def verify_recovery_code(code: str, hashed_codes: list[str]) -> int | None:
    """Verify a recovery code. Returns its index or None."""
    for i, hashed in enumerate(hashed_codes):
        if bcrypt.checkpw(code.encode(), hashed.encode() if isinstance(hashed, str) else hashed):
            return i
    return None
```

### Admin Reset

A superuser or tenant admin (role with `manage_team` permission) can forcibly reset a user's 2FA from the admin panel or user management settings. This:

1. Clears `totp_secret`, `totp_enabled`, `recovery_codes`
2. Logs an activity record: `{activity_type: "system", title: "2FA reset for user@example.com by admin"}`

### 2fa_token JWT Details

```python
from rest_framework_simplejwt.tokens import AccessToken
import uuid

class TwoFactorToken(AccessToken):
    """Short-lived JWT for the 2FA challenge step."""
    token_type = "2fa"
    lifetime = timedelta(minutes=5)

    @classmethod
    def for_user(cls, user) -> "TwoFactorToken":
        token = super().for_user(user)
        token["purpose"] = "2fa_challenge"
        token["user_id"] = str(user.id)
        if user.tenant_id:
            token["tenant_id"] = str(user.tenant_id)
        return token
```

---

## 6. Frontend: 2FA Setup in Settings

### Page: `/settings/security`

Located under Settings → Security tab (or a dedicated Security sub-page in the settings sidebar).

### State Machine

```
[Not Set Up] ──click "Enable 2FA"──> [Step 1: Scan QR]
                                         │
                                         │ scan QR / enter secret
                                         ▼
                                    [Step 2: Verify Code]
                                         │
                                         │ enter TOTP code
                                         │
                                    ──valid──> [Step 3: Save Recovery Codes]
                                         │
                                         │ show 10 codes, prompt to save
                                         │ click "I've saved my codes"
                                         ▼
                                    [2FA Active]

[2FA Active] ──click "Disable"──> [Confirm: enter password + TOTP]
                                      │
                                      │ valid
                                      ▼
                                 [Not Set Up]
```

### Component Tree

```
SettingsSecurityPage
├── Header: "Security Settings"
├── Section: Two-Factor Authentication
│   ├── StatusCard (enabled/disabled indicator)
│   ├── EnableButton (if disabled)
│   ├── QrCodeStep (if in setup flow)
│   │   ├── QR code image (SVG rendered from provisioning URI)
│   │   └── Manual entry: secret displayed with copy button
│   ├── VerifyCodeStep
│   │   └── Input (6 digits, auto-advance on paste)
│   └── RecoveryCodesStep
│       ├── Code list (10 codes, masked with reveal toggle)
│       ├── Download button (text file)
│       ├── Copy button
│       └── Confirm checkbox: "I have saved my recovery codes"
├── Section: Recovery Codes (when 2FA active)
│   ├── Remaining count (e.g., "7 of 10 remaining")
│   └── Regenerate button (prompts for TOTP code first)
└── Section: Session Management
    └── "Log out all other sessions" button
```

### API Calls from Settings Page

| Action | Endpoint | Trigger |
|---|---|---|
| Check status | `GET /api/auth/2fa/status/` | Page mount |
| Start setup | `POST /api/auth/2fa/setup/` | Click "Enable 2FA" |
| Verify setup | `POST /api/auth/2fa/confirm/` | Submit TOTP code |
| Disable 2FA | `POST /api/auth/2fa/disable/` | Confirm dialog submit |
| Regenerate codes | `POST /api/auth/2fa/recovery-codes/regenerate/` | Click "Regenerate" |

---

## 7. Frontend: 2FA Challenge Screen

### Login Flow Modification

The existing login flow in `src/store/auth.ts` needs an additional state: `awaiting2FA`.

```
login() call
  │
  ├── Response includes user + access/refresh → normal login
  └── Response includes 2fa_required: true + 2fa_token → transition to challenge
```

### Component: `TwoFactorChallenge`

```
TwoFactorChallenge
├── Props: 2fa_token (string), onSubmit(code, isRecovery)
├── State: mode ("totp" | "recovery"), error, loading
├── [TOTP mode]
│   ├── Title: "Two-factor authentication"
│   ├── Subtitle: "Enter the code from your authenticator app"
│   ├── Input: 6-digit code (individual digit boxes × 6, auto-advance)
│   ├── Error message (if invalid)
│   └── Link: "Use a recovery code instead"
│
└── [Recovery mode]
    ├── Title: "Use a recovery code"
    ├── Input: recovery code (XXXXXXXX-XXXXXXXX)
    ├── Error message (if invalid)
    ├── Remaining codes hint (from initial setup screen)
    └── Link: "Use authenticator app instead"
```

### Router Changes

The existing `router/index.tsx` already has an `AuthLayout`. Add the 2FA challenge as a route:

```tsx
{ path: '2fa/challenge', element: <TwoFactorChallenge /> }
```

But more practically, the challenge should be embedded into the login callback handler in `useAuth` — when `login()` or `socialLogin()` returns `2fa_required: true`, the component switches to the challenge UI without a full page navigation.

### Zustand Store Changes

Add to `src/store/auth.ts`:

```typescript
interface AuthState {
  // ... existing fields
  twoFactorToken: string | null;
  isAwaiting2FA: boolean;

  // New methods
  verifyTwoFactor: (code: string, isRecovery?: boolean) => Promise<void>;
  cancelTwoFactor: () => void;
}
```

---

## 8. ADR-028: SSO/SAML via python3-saml

**Status:** Proposed
**Date:** 2026-06-30

### Context

Enterprise customers require Single Sign-On via SAML 2.0 identity providers (Okta, Azure AD, OneLogin, Google Workspace). FrontierCRM must act as a SAML Service Provider (SP).

Requirements:

- Multi-tenant: each tenant configures their own IdP
- Both SP-initiated and IdP-initiated login flows
- Just-in-time (JIT) user provisioning — users created on first SAML login
- Attribute mapping (IdP SAML attributes → User model fields)
- Frontend settings page for IdP configuration
- Coexist with existing auth methods (email/password, social OAuth, magic link)

### Options Considered

**Option A — django-saml2-auth**
A Django app that provides SAML SP functionality out of the box.

- Pros: plug-and-play, includes URL routes and views, handles certificate management
- Cons: single-tenant by design (one `SAML_CONFIG` in settings.py); hard to adapt to multi-tenant; tightly coupled to Django session auth; conflicts with JWT flow
- **Rejected** — single-tenant assumption doesn't fit FrontierCRM's architecture

**Option B — python3-saml (onelogin)**
The industry-standard Python SAML library, maintained by OneLogin. Provides `OneLogin_Saml2_Auth`, `OneLogin_Saml2_Response`, `OneLogin_Saml2_Settings` classes. No Django coupling.

- Pros: fully SAML 2.0 compliant; handles all bindings (HTTP-Redirect, HTTP-POST); supports encryption and signing; battle-tested at enterprise scale; zero Django assumptions
- Cons: requires writing SAML glue code (request handling, auth response parsing, user provisioning); library API is low-level
- **Accepted** — the per-tenant configuration model maps naturally to per-tenant `SamlProvider` instances, and the low-level API gives us full control over the JWT issuance flow

**Option C — Auth0 / WorkOS / Clerk**
Third-party auth platforms that handle SAML as a managed service.

- Pros: zero SAML code; UI for IdP configuration; automatic certificate rotation
- Cons: per-seat pricing; data residency concerns; vendor lock-in; FrontierCRM would cede control of the auth UX
- **Rejected** — FrontierCRM is the auth platform; delegating SAML to a third party introduces cost and data exposure that the existing architecture doesn't need

### Decision

**Use `python3-saml` (onelogin) with a tenant-scoped `SamlProvider` model. Each tenant creates a `SamlProvider` record with their IdP metadata. All SAML endpoints are backed by per-tenant configuration resolution.**

Key design points:

1. **Tenant-scoped SamlProvider model.** Each tenant can have exactly one active `SamlProvider`. The model stores IdP metadata (entity ID, SSO URL, SLO URL, x509 certificate) and attribute mapping configuration.

2. **Unique SP entity ID per tenant.** `https://{frontiercrm-domain}/api/auth/saml/{tenant_id}/metadata/` as the SP entity ID, preventing cross-tenant confusion.

3. **SP-initiated flow.** User clicks "Sign in with SSO" on login page → enter email → backend resolves tenant → redirect to IdP → ACS endpoint → JIT provision → JWT issuance.

4. **IdP-initiated flow.** IdP sends unsolicited SAML response to the ACS endpoint → backend identifies tenant from `issuer` → JIT provision → redirect to app with JWT in URL fragment.

5. **JIT provisioning.** On first SAML login, create a `User` record with fields populated from SAML attributes (email, first_name, last_name). Assign the default role (configured in `SamlProvider.default_role_id`). No invitation flow needed — SAML users authenticate through their IdP.

6. **Login hint integration.** The login page detects the user's email domain and auto-switches to SAML if that domain is associated with an IdP. This requires a lightweight `GET /api/auth/saml/domain-check/?email=user@company.com` endpoint.

### python3-saml Dependency

```
python3-saml>=1.16.0
```

---

## 9. Data Model: SamlProvider

### New Model (`apps/accounts/models.py`)

```python
class SamlProvider(TenantScopedModel):
    """SAML 2.0 identity provider configuration, scoped to a tenant."""

    # Identity Provider metadata
    idp_entity_id = models.CharField(max_length=500, help_text="IdP Entity ID (issuer)")
    idp_sso_url = models.URLField(max_length=500, help_text="IdP Single Sign-On URL (HTTP-Redirect binding)")
    idp_slo_url = models.URLField(max_length=500, blank=True, default="", help_text="IdP Single Logout URL (optional)")
    idp_x509_cert = models.TextField(help_text="IdP X.509 certificate (PEM format, one cert)")

    # Attribute mapping — SAML attribute names → User model fields
    attribute_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'SAML attribute mapping. E.g. '
            '{"email": "email", "first_name": "firstName", '
            '"last_name": "lastName", "avatar_url": "photo"}'
        ),
    )

    # Service Provider settings
    sp_entity_id = models.CharField(max_length=500, help_text="SP Entity ID (auto-generated)")
    acs_url = models.URLField(max_length=500, help_text="Assertion Consumer Service URL (auto-generated)")
    audience = models.URLField(max_length=500, blank=True, default="", help_text="Optional: restrict to a specific IdP audience")

    # JIT provisioning
    default_role = models.ForeignKey(
        "teams.Role",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Role assigned to JIT-provisioned users. If null, new users get no role and must be assigned manually.",
    )
    auto_create_users = models.BooleanField(
        default=True,
        help_text="Automatically create user accounts on SAML login from this IdP",
    )
    allowed_domains = models.JSONField(
        default=list,
        blank=True,
        help_text="Restrict SAML login to specific email domains. Empty list = allow any domain.",
    )

    # Status
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_saml_provider"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id"],
                condition=models.Q(is_active=True),
                name="uq_active_saml_provider_per_tenant",
            ),
        ]

    def __str__(self) -> str:
        return f"SAML({self.idp_entity_id}) for tenant {self.tenant_id}"

    def get_sp_settings(self) -> dict:
        """Return the SP configuration dict for python3-saml."""
        return {
            "strict": True,
            "debug": settings.DEBUG,
            "sp": {
                "entityId": self.sp_entity_id,
                "assertionConsumerService": {
                    "url": self.acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": self.idp_slo_url or "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
            },
            "idp": {
                "entityId": self.idp_entity_id,
                "singleSignOnService": {
                    "url": self.idp_sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "singleLogoutService": {
                    "url": self.idp_slo_url or "",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": self.idp_x509_cert,
            },
        }
```

### Auto-generated Fields

When creating a `SamlProvider`, the SP entity ID and ACS URL are auto-generated:

```python
def save(self, *args, **kwargs):
    if not self.sp_entity_id:
        self.sp_entity_id = (
            f"{settings.SAML_BASE_URL}/api/auth/saml/{self.tenant_id}/metadata/"
        )
    if not self.acs_url:
        self.acs_url = (
            f"{settings.SAML_BASE_URL}/api/auth/saml/{self.tenant_id}/acs/"
        )
    super().save(*args, **kwargs)
```

### SAML Settings

Add to `config/settings/base.py`:

```python
# ── SAML ──────────────────────────────────────────────────────────────────
SAML_BASE_URL = os.environ.get("SAML_BASE_URL", "http://localhost:8000")
```

---

## 10. SAML Login Flows (Sequence)

### SP-Initiated Login

```
Frontend                  Backend                        IdP
   │                         │                             │
   │ POST /auth/saml/login/  │                             │
   │ {email: "a@b.com"}      │                             │
   │────────────────────────>│                             │
   │                         │  Resolve tenant from email  │
   │                         │  domain against Provider    │
   │                         │  Generate SAMLRequest       │
   │                         │  Store request_id in session│
   │  {redirect_url:         │                             │
   │   "https://idp/..."}    │                             │
   │<────────────────────────│                             │
   │                         │                             │
   │  Redirect browser       │                             │
   │──────────────────────────────────────────────────────>│
   │                         │                             │
   │                         │               User authenticates at IdP
   │                         │                             │
   │            IdP POSTs SAMLResponse to ACS URL          │
   │<──────────────────────────────────────────────────────│
   │                         │                             │
   │  POST /api/auth/saml/{tenant_id}/acs/                 │
   │  (SAMLResponse via HTTP-POST binding)                 │
   │────────────────────────>│                             │
   │                         │  Parse SAMLResponse          │
   │                         │  Verify signature            │
   │                         │  Validate conditions         │
   │                         │  Extract attributes          │
   │                         │  JIT provision / find user   │
   │                         │  Issue JWT tokens            │
   │  {access, refresh,      │                             │
   │   user: {...}}          │                             │
   │<────────────────────────│                             │
```

### IdP-Initiated Login

```
Frontend                  Backend                        IdP
   │                         │                             │
   │                         │     IdP sends unsolicited   │
   │                         │     SAMLResponse to ACS URL │
   │            POST /api/auth/saml/{tenant_id}/acs/       │
   │<──────────────────────────────────────────────────────│
   │                         │                             │
   │  (Browser posts to      │                             │
   │   ACS endpoint)         │                             │
   │────────────────────────>│                             │
   │                         │  Parse SAMLResponse          │
   │                         │  Resolve tenant from issuer │
   │                         │  JIT provision / find user  │
   │                         │  Issue JWT tokens           │
   │  Redirect to             │                             │
   │  /auth/saml/callback    │                             │
   │  #access=...&refresh=.. │                             │
   │<────────────────────────│                             │
   │                         │                             │
   │  (Hash fragment —       │                             │
   │   frontend reads it)    │                             │
```

### Domain Detection

```
Frontend                  Backend
   │                         │
   │ GET /auth/saml/domain-check/    │
   │ ?email=user@company.com │
   │────────────────────────>│
   │                         │  Extract domain: company.com
   │                         │  Look up SamlProvider with
   │                         │  allowed_domains containing
   │                         │  "company.com" (or no domains)
   │  {has_saml: true,       │
   │   provider_name:        │
   │   "Company IdP"}        │
   │<────────────────────────│
```

---

## 11. SAML REST API Contracts

### 11.1 POST /api/auth/saml/login/ — SP-initiated login start

**Authentication:** None (public)
**Rate limit:** 10 per minute per IP

**Request:**

```json
{
  "email": "user@company.com"
}
```

**Response 200:**

```json
{
  "redirect_url": "https://company.okta.com/app/frontiercrm/...",
  "relay_state": "/dashboard"
}
```

**Logic:**
1. Extract domain from email
2. Find active `SamlProvider` where `allowed_domains` contains the domain (or `allowed_domains` is empty)
3. If no matching provider, return `404 {"error": "No SAML provider configured for this domain."}`
4. Generate SAML AuthnRequest via `python3-saml`
5. Store `request_id` in session/cache for response validation
6. Return the IdP redirect URL

### 11.2 POST /api/auth/saml/{tenant_id}/acs/ — Assertion Consumer Service

**Authentication:** None (public — called by IdP)
**Rate limit:** 10 per minute per IP

**Request:** Form-encoded `SAMLResponse` (from IdP HTTP-POST binding)

**Response 200 (with redirect):**

```json
{
  "redirect_url": "https://app.frontiercrm.com/auth/saml/callback#access=...&refresh=..."
}
```

**Logic:**
1. Instantiate `OneLogin_Saml2_Auth` with provider's settings
2. Call `auth.process_response()` — validates signature, conditions, audience
3. Extract attributes using `provider.attribute_mapping`
4. Find or create user (JIT provisioning — see section 12)
5. Issue JWT tokens
6. Return redirect with tokens in URL hash fragment

### 11.3 GET /api/auth/saml/{tenant_id}/metadata/ — SP Metadata XML

**Authentication:** None (public — consumed by IdP)

**Response 200 (Content-Type: application/xml):**

Returns SAML 2.0 SP metadata XML generated by `python3-saml`.

### 11.4 POST /api/auth/saml/logout/ — SAML Single Logout

**Authentication:** JWT required

**Request:**

```json
{
  "tenant_id": "uuid"
}
```

**Response 200:**

```json
{
  "redirect_url": "https://idp/saml/slo?SAMLRequest=..."
}
```

**Notes:**
- Sends a SAML LogoutRequest to the configured IdP SLO URL
- If no SLO URL is configured, falls back to local logout (invalidate JWT on client side)

### Management Endpoints (settings page CRUD)

All require `manage_team` or `__admin__` permission.

| Method | Path | Description |
|---|---|---|
| GET | `/api/auth/saml/providers/` | List SAML providers for current tenant |
| POST | `/api/auth/saml/providers/` | Create SAML provider |
| GET | `/api/auth/saml/providers/{id}/` | Get provider details |
| PATCH | `/api/auth/saml/providers/{id}/` | Update provider |
| DELETE | `/api/auth/saml/providers/{id}/` | Delete provider |
| POST | `/api/auth/saml/providers/{id}/test/` | Test SAML connection (sends test AuthnRequest) |

**POST /api/auth/saml/providers/ — Request:**

```json
{
  "idp_entity_id": "http://www.okta.com/exk...",
  "idp_sso_url": "https://company.okta.com/app/frontiercrm/...",
  "idp_slo_url": "https://company.okta.com/app/frontiercrm/slo/...",
  "idp_x509_cert": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
  "attribute_mapping": {
    "email": "email",
    "first_name": "firstName",
    "last_name": "lastName",
    "avatar_url": "photo"
  },
  "default_role_id": "uuid-optional",
  "auto_create_users": true,
  "allowed_domains": ["company.com"]
}
```

---

## 12. Just-In-Time User Provisioning

### Provisioning Logic

```python
from django.contrib.auth import get_user_model
import uuid

UserModel = get_user_model()


def provision_user_from_saml(
    provider: "SamlProvider",
    attributes: dict[str, str],
) -> "User":
    """
    Find or create a user from SAML attributes.
    Returns (user, created: bool).
    """
    email = attributes.get("email", "")
    if not email:
        raise ValueError("SAML response must include an email attribute")

    # Look up by email
    try:
        user = UserModel.objects.get(email=email)
        return user, False
    except UserModel.DoesNotExist:
        pass

    # Create new user (JIT provisioning)
    if not provider.auto_create_users:
        raise PermissionError("Auto-provisioning is disabled for this provider")

    username = email.split("@")[0]
    # Ensure unique username
    base_username = username
    suffix = 1
    while UserModel.objects.filter(username=username).exists():
        username = f"{base_username}{suffix}"
        suffix += 1

    user = UserModel.objects.create(
        tenant_id=provider.tenant_id,
        email=email,
        username=username,
        first_name=attributes.get("first_name", ""),
        last_name=attributes.get("last_name", ""),
        avatar_url=attributes.get("avatar_url", ""),
        email_verified=True,
    )

    # Assign default role
    if provider.default_role_id:
        from apps.teams.models import Membership, Team

        default_team = Team.objects.filter(
            tenant_id=provider.tenant_id, name="Everyone"
        ).first()

        Membership.objects.create(
            user=user,
            tenant_id=provider.tenant_id,
            role_id=provider.default_role_id,
            team=default_team,
            is_active=True,
        )

    return user, True
```

### JIT Notes

- Users are always scoped to the tenant identified by the `SamlProvider`
- `email_verified` is set to `True` (the IdP has already verified the email)
- If `auto_create_users` is `False` and the user doesn't exist, login returns a 403 error: "No account found. Contact your administrator."
- If the user exists but belongs to a different tenant (e.g., migrated), login returns a 403: "Account exists under a different organization. Contact support."
- The `Membership` creation creates a link to the tenant with the default role. If the user already has a membership (existing user logging in via SAML for the first time), it's updated rather than duplicated.

---

## 13. Frontend: IdP Config Page in Settings

### Page: `/settings/security/saml`

Located under Settings → Security → SAML / SSO.

### Component Tree

```
SamlSettingsPage
├── Header: "Single Sign-On (SAML)"
├── StatusBanner (not configured / active / error)
│
├── [Not Configured]
│   └── "Configure SAML" button → ConfigForm (inline or modal)
│
├── [Configured]
│   ├── ProviderInfoCard
│   │   ├── IdP name / entity ID
│   │   ├── SSO URL
│   │   ├── Last used timestamp
│   │   ├── Status badge (active/inactive)
│   │   └── Download SP Metadata button (XML)
│   ├── DomainList (allowed domains with add/remove)
│   ├── AttributeMappingEditor
│   │   └── Key-value pairs: SAML attribute → User field
│   ├── DefaultRolePicker (dropdown of tenant roles)
│   ├── AutoCreateUsersToggle
│   └── Actions
│       ├── Edit button → ConfigForm (pre-filled)
│       ├── Test Connection button
│       ├── Disable / Enable toggle
│       └── Delete button (with confirmation)
│
└── ConfigForm
    ├── Field: IdP Entity ID (text)
    ├── Field: SSO URL (url)
    ├── Field: SLO URL (url, optional)
    ├── Field: X.509 Certificate (textarea/paste zone)
    ├── SP Metadata Section (generated, read-only)
    │   ├── ACS URL (copyable)
    │   ├── Entity ID (copyable)
    │   └── Download Metadata XML button
    └── Submit / Cancel
```

### Login Page Modification

The login page already shows Google and Microsoft SSO buttons. Add a third button:

```
"Continue with SSO"  ──click──> email input prompt
                                    │
                                    │ submit
                                    ▼
                              GET /auth/saml/domain-check/
                                    │
                             ──has SAML──> Redirect to IdP
                             ──no SAML──> Show error: "No SSO configured for this domain"
```

Alternatively, the login page can auto-detect: user types email, the SSO button appears if the domain is associated with a SAML provider. This is the pattern used by Vercel, Linear, etc.

### Router Changes

Add to `router/index.tsx`:

```tsx
// Auth routes
{ path: 'auth/saml/callback', element: <SamlCallbackPage /> }
// Settings routes
{ path: 'settings/security/saml', element: <SamlSettingsPage /> }
```

---

## 14. Implementation Order

Phase 5 has a natural dependency order:

### Phase 5a — 2FA (P2, the priority)

| Step | Task | Est. Effort |
|---|---|---|
| 1 | Add `pyotp` dependency, add User model fields (`totp_secret`, `totp_enabled`, `totp_created_at`, `recovery_codes`) | 0.5d |
| 2 | Implement `TwoFactorToken` JWT class in `apps/accounts/auth.py` | 0.5d |
| 3 | Modify `login_view` to return `2fa_token` when user has 2FA enabled | 1d |
| 4 | Implement `2fa_setup`, `2fa_confirm`, `2fa_verify`, `2fa_disable`, `2fa_status` endpoints | 2d |
| 5 | Implement recovery code generation, verification, regeneration | 1d |
| 6 | Rate limiting on verify endpoint | 0.5d |
| 7 | Tenant-level `require_2fa` enforcement in permission middleware | 0.5d |
| 8 | Admin reset endpoint + activity logging | 0.5d |
| 9 | Frontend: Settings security page with QR code, verify, recovery codes | 2d |
| 10 | Frontend: 2FA challenge component in login flow | 1d |
| 11 | Frontend: Zustand store changes for `awaiting2FA` state | 0.5d |
| 12 | Tests: backend unit tests + frontend component tests | 2d |
| | **Total 2FA** | **12d** |

### Phase 5b — SSO/SAML (P3, lower priority)

| Step | Task | Est. Effort |
|---|---|---|
| 1 | Add `python3-saml` dependency, `SAML_BASE_URL` setting | 0.5d |
| 2 | Implement `SamlProvider` model + migration | 0.5d |
| 3 | Implement `SamlProvider` CRUD management endpoints | 1d |
| 4 | Implement SAML AuthnRequest generation (SP-initiated login) | 1d |
| 5 | Implement ACS endpoint (SAMLResponse processing) | 2d |
| 6 | Implement IdP-initiated login (unsolicited response handling) | 1d |
| 7 | Implement SP metadata XML endpoint | 0.5d |
| 8 | Implement JIT provisioning logic | 1d |
| 9 | Implement domain-check endpoint | 0.5d |
| 10 | Implement SAML Single Logout | 1d |
| 11 | Frontend: SAML settings page (IdP config form, metadata display) | 2d |
| 12 | Frontend: Login page SSO button + domain detection | 1d |
| 13 | Frontend: SAML callback page (hash fragment token handling) | 0.5d |
| 14 | Tests: backend unit + mock SAML responses + frontend | 2d |
| | **Total SSO/SAML** | **13d** |

---

## 15. Acceptance Criteria

### 2FA

1. User with 2FA disabled logs in normally (no change to existing flow)
2. User enables 2FA from Settings → Security
   - QR code is displayed and scannable by Google Authenticator/Authy/1Password
   - Confirming a valid code enables 2FA and returns 10 recovery codes
3. User with 2FA enabled logs in:
   - Password accepted → `2fa_required: true` + `2fa_token` returned
   - Valid TOTP code → JWT issued
   - Invalid TOTP code → error, retry up to 5 times
   - After 5 failures → token revoked, must re-enter password
4. Recovery code works as a one-time bypass
   - Each recovery code used exactly once
   - After all codes used, recovery is unavailable (admin reset required)
5. Tenant admin can set `require_2fa: true` — users without 2FA get 428 Precondition Required
6. User can disable 2FA with password + TOTP code
7. Admin can forcibly reset another user's 2FA (logged as activity)
8. Rate limiting: 5 TOTP attempts/min, 1 2FA setup/hour, 3 disable/hour

### SSO/SAML

1. Tenant admin creates a `SamlProvider` from the settings page
   - IdP entity ID, SSO URL, x509 cert required
   - Attribute mapping configurable (email, first_name, last_name)
   - Allowed domains configurable
2. SP metadata XML is downloadable and consumable by Okta/Azure AD/OneLogin
3. SP-initiated login:
   - User enters email on login page → redirected to IdP
   - User authenticates at IdP → redirected back to ACS endpoint
   - New user created via JIT provisioning (if `auto_create_users: true`)
   - Existing user logged in (role unchanged)
   - JWT tokens returned
4. IdP-initiated login:
   - IdP sends unsolicited SAMLResponse → user redirected to app with tokens
5. Domain detection: login page detects SAML-configured domain and shows SSO button
6. Test connection: sends test AuthnRequest and reports success/failure
7. Deleting/deactivating the provider prevents any SAML login
8. Rate limiting: 10 SAML requests per minute per IP

---

## 16. Open Questions / Spike Items

### 2FA

1. **Email-based 2FA fallback.** Should we offer email OTP as a secondary 2FA method (in addition to TOTP)? This would increase adoption for users without smartphones. **Recommendation:** defer to Phase 6. TOTP-only keeps the initial scope small, and email-based OTP has its own security considerations (email compromise = MFA bypass).

2. **WebAuthn / Passkeys.** Passkeys (platform authenticators, security keys) are a stronger 2FA mechanism than TOTP. **Recommendation:** spike for Phase 6 — WebAuthn requires a different data model (public key storage, challenge-response) and browser API integration.

3. **SMS 2FA.** TOTP via authenticator app is preferred over SMS (NIST no longer recommends SMS as an out-of-band verifier). **Recommendation:** do not implement SMS 2FA. If phone-based 2FA is needed, spike Authy TOTP push.

### SSO/SAML

1. **Certificate rotation.** IdP certificates change over time. The current model stores a single cert. **Spike:** support multiple certs (array of x509 certs) and auto-detect which one signed the response.

2. **SAML logout propagation.** When a user logs out of FrontierCRM, should we propagate SLO to the IdP (logging them out of all apps)? This requires the IdP to support SLO and adds complexity. **Recommendation:** implement SLO as an optional feature. If the IdP doesn't provide an SLO URL, do local logout only.

3. **SCIM integration.** For enterprise customers, SCIM (System for Cross-domain Identity Management) is often paired with SAML for automated user provisioning and deprovisioning. **Recommendation:** spike for Phase 6 — SCIM is a separate protocol (REST API called by the IdP) with its own data model and endpoints.

4. **Portal/customer-facing SSO.** The current design covers internal CRM users. Future customer-facing portals may need SAML too, but that's a separate deployment scenario. **Recommendation:** no changes needed to the model; customer portals would create their own `SamlProvider` records under a different tenant scope logic.

---

*End of Phase 5 Auth Security Specification*