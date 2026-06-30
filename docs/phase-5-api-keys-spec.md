# API Keys — Machine-to-Machine Auth Spec

**Status:** Draft (for ADR review)
**Author:** allstars-atlas
**Date:** 2026-06-30
**Phase:** 5 (Post-MVP)
**Priority:** P3

---

## Table of Contents

1. [Context & Constraints](#1-context--constraints)
2. [ADR-027: API Keys Auth Strategy](#2-adr-027-api-keys-auth-strategy)
3. [Data Model](#3-data-model)
4. [Auth Backend Integration](#4-auth-backend-integration)
5. [API Endpoints](#5-api-endpoints)
6. [Permission & Scope Binding](#6-permission--scope-binding)
7. [Rate Limiting & Security](#7-rate-limiting--security)
8. [Frontend Management Page](#8-frontend-management-page)
9. [Implementation Steps](#9-implementation-steps)
10. [Open Questions](#10-open-questions)

---

## 1. Context & Constraints

### Why API Keys?

FrontierCRM needs programmatic access for:
- Third-party integrations that can't use OAuth (custom scripts, CI/CD, ETL pipelines)
- Server-to-server communication with partner platforms
- Internal automation scripts (bulk import, data export, reporting)
- SDK / API client access for paying customers

### Constraints

| Constraint | Value |
|---|---|
| **Existing auth** | JWT (Bearer token) via SimpleJWT, valid 30min |
| **Multi-tenant** | Yes — every API key is scoped to a single tenant |
| **Permission system** | Role-based JSONField permissions (`PermissionRegistry`) |
| **Rate limiting** | 1000/hour/user via `UserRateThrottle` |
| **Team size** | Small team (2-3 devs) — keep complexity minimal |
| **Key storage** | Only hash stored; plaintext shown once at creation |
| **Expiration** | Optional — keys can have `expires_at` |
| **No REST Framework's Token model** | SimpleJWT and DRF Token both lack: tenant scoping, named keys, expiry, last-used tracking, granular permissions |

### What we're NOT building

This is not for:
- User-facing JWT replacement (users keep using Bearer JWTs)
- OAuth2 provider flow (that's a separate feature)
- Scoped API endpoints restricted only to keys (keys share the same API surface as JWT users)

---

## 2. ADR-027: API Keys Auth Strategy

```
# ADR-027: API Keys — Hash-Based Static Key Auth
Status: Proposed
Date: 2026-06-30
Author: allstars-atlas

## Context
We need machine-to-machine auth that outlives JWT 30-min windows.
Third parties cannot refresh tokens; they need a static credential.

## Options Considered

### Option A — DRF Authtoken (rest_framework.authtoken)
- Pros: Built-in, simple, DRF ecosystem
- Cons: No tenant_id on model, no expiry, no named keys,
         no last_used_at, single token per user, no scope
- Verdict: Too rigid for our multi-tenant, multi-key needs

### Option B — Custom APIKey model + DRF auth backend
- Pros: Full control, fits tenant model, supports naming & expiry,
         can bind to existing RolePermission system, multiple keys per user
- Cons: Must write auth backend, must handle key generation/hashing

### Option C — JWT-as-API-Key (long-lived signed JWTs)
- Pros: Uses existing SimpleJWT validation, no new auth backend
- Cons: Revocation is hard (token still valid until expiry),
         can't rotate without re-issue, no last-used tracking
- Verdict: Revocation nightmare

### Option D — Hashed API Key (Option B refined)
- Same as Option B but explicitly:
  * Use secrets.token_urlsafe for key generation (like GitHub)
  * Store only sha-256 hash (like Django password hashing pattern)
  * Return plaintext once on creation (never again)
- Pros: Security best practice, revocable, auditable

## Decision
Adopt Option D — Custom APIKey model with hashed key storage.

Key generation follows the GitHub/GitLab pattern:
  `fcrm_<tenant_short_id>_<random_64_chars_base64>`

The prefix `fcrm_` makes keys recognisable in logs and configs.
The tenant short ID allows quick filtering by tenant.
The random suffix provides 256 bits of entropy (secrets.token_urlsafe(48)).

Only the SHA-256 hash is stored. The plaintext is returned exactly once
in the creation response and cannot be retrieved again.

## Consequences
- Positive: Revocable, auditable, scoped to tenant + permissions
- Positive: Multiple keys per user (name, rotate)
- Positive: last_used_at enables inactivity-based cleanup
- Negative: Must write and maintain custom auth backend (~50 lines)
- Negative: API keys bypass tenant check differently than JWT
  (the key itself encodes the tenant, so TenantAwarePermission
   needs a bypass flag for API key requests)
```
### API Key Header Format

Clients send the API key via the standard `Authorization` header:

```
Authorization: Bearer fcrm_abc123_<random>
```

This means the same `AUTH_HEADER_TYPES` dance as SimpleJWT — our custom auth backend checks the key against the DB if the key starts with `fcrm_`, otherwise falls through to SimpleJWT.

## 3. Data Model

### New App: `apps.apikeys`

Following the same pattern as `apps.webhooks` — a self-contained app with model + views + urls.

```python
# apps/apikeys/models.py

"""API key model for programmatic / third-party access."""

from __future__ import annotations

import hashlib
import secrets

from django.db import models

from apps.core.models import TenantScopedModel


class APIKey(TenantScopedModel):
    """A named API key for programmatic access to the FrontierCRM API.

    The plaintext key is shown exactly once at creation.
    Only the SHA-256 hash is stored.
    """

    name = models.CharField(max_length=255, help_text="Human-readable label e.g. 'CI Pipeline'")
    key_prefix = models.CharField(
        max_length=16,
        editable=False,
        help_text="First 16 chars of the key for display/identification",
    )
    key_hash = models.CharField(
        max_length=128,
        editable=False,
        unique=True,
        help_text="SHA-256 hash of the full API key",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text="User who created/owns this key",
    )
    permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Override permissions dict — merged on top of the user's role permissions. "
                  "Leave empty to inherit all the user's role permissions.",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If set, the key is rejected after this time",
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Updated on every authenticated request (best-effort, throttled)",
    )
    last_ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the last request using this key",
    )
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If set, the key was explicitly revoked",
    )

    class Meta:
        db_table = "apikeys_key"
        indexes = [
            models.Index(fields=["key_hash"]),
            models.Index(fields=["tenant_id", "is_active"]),
            models.Index(fields=["tenant_id", "user"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.key_prefix}...)"

    def is_expired(self) -> bool:
        """Check if key has passed its expiration date."""
        from django.utils import timezone
        if self.expires_at and self.expires_at < timezone.now():
            return True
        return False

    def is_revoked(self) -> bool:
        """Check if key was explicitly revoked."""
        return self.revoked_at is not None

    @classmethod
    def generate_key(cls) -> str:
        """Generate a new API key in the format: fcrm_<prefix>_<random>"""
        random_part = secrets.token_urlsafe(48)  # 64 chars base64, 384 bits
        return f"fcrm_{random_part}"

    @classmethod
    def hash_key(cls, raw_key: str) -> str:
        """Return SHA-256 hex digest of the raw key."""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def get_key_prefix(cls, raw_key: str) -> str:
        """Return first 16 chars for display purposes."""
        return raw_key[:16]
```

### Migration Notes

- No FK to existing models that requires existing data — clean migration
- `TenantScopedModel` provides `id` (UUID), `tenant_id` (UUID FK), `created_at`, `updated_at`, `deleted_at`
- Unique constraint on `key_hash` (SHA-256 will not collide)

### Key Generation Flow

```
1. User clicks "Generate API Key" in Settings > API Keys
2. Backend generates: fcrm_<secrets.token_urlsafe(48)>
3. Store: hash=SHA-256(key), prefix=key[:16]
4. Return: { id, name, prefix, key: "<full plaintext>", ... }
5. User MUST copy the key now — it's never shown again
```

## 4. Auth Backend Integration

### 4.1 Custom DRF Authentication Class

Create `apps/apikeys/auth.py`:

```python
"""DRF authentication backend for API key authentication."""

from __future__ import annotations

import hashlib
from typing import Any

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from apps.accounts.models import User


class APIKeyAuthentication(BaseAuthentication):
    """Authenticate requests using an API key in the Authorization header.

    Header format: Authorization: Bearer fcrm_<random>

    If the token doesn't start with 'fcrm_', we skip authentication
    (allowing SimpleJWT to handle it via the fallback chain).
    """

    keyword = "Bearer"

    def authenticate(self, request: Request) -> tuple[User, dict] | None:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer fcrm_"):
            return None  # Let SimpleJWT handle it

        raw_key = auth_header.removeprefix("Bearer ").strip()

        # Hash and look up
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        from .models import APIKey

        try:
            api_key = APIKey.objects.select_related("user").get(
                key_hash=key_hash,
                is_active=True,
                revoked_at__isnull=True,
            )
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key.")

        # Check expiry
        if api_key.is_expired():
            raise AuthenticationFailed("API key has expired.")

        # Update last_used_at (best-effort, avoid write on every request)
        now = timezone.now()
        if api_key.last_used_at is None or (now - api_key.last_used_at).total_seconds() > 300:
            api_key.last_used_at = now
            api_key.last_ip_address = request.META.get("REMOTE_ADDR")
            api_key.save(update_fields=["last_used_at", "last_ip_address"])

        user = api_key.user

        # Tag the user so downstream code can distinguish API key auth from JWT auth
        user._api_key_auth = True
        user._api_key_permissions = api_key.permissions
        user._api_key_id = str(api_key.id)

        return (user, {"auth_type": "api_key", "api_key_id": str(api_key.id)})
```

### 4.2 Register in Settings

Add to `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES`:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.apikeys.auth.APIKeyAuthentication",      # NEW — checked first
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    # ... rest unchanged
}
```

**Why APIKeyAuthentication first:** If the header starts with `fcrm_`, we handle it. If not, we return `None` and DRF tries SimpleJWT. Zero overhead for normal JWT requests.

### 4.3 TenantAwarePermission Changes

The existing `TenantAwarePermission` checks `request.user.tenant_id`. For API key auth, the user already has `tenant_id` set (from their membership). No changes needed — the user object is the same User model.

However, API key auth sets `user._api_key_auth = True`. Views that want to restrict certain operations to interactive sessions only (e.g., password change, MFA enrollment) can check this flag.

### 4.4 Permission Merging

API keys have their own `permissions` JSONField. The resolution order is:

```
effective_permission = key.permissions (if non-empty)
                     | user.role.resolved_permissions (fallback)
```

If the key has explicit permissions defined, those override the user's role permissions. If empty, the key inherits the full role permissions of the owning user.

This is implemented in the auth backend or a helper:

```python
def get_api_key_effective_permissions(api_key, user):
    if api_key.permissions and isinstance(api_key.permissions, dict) and len(api_key.permissions) > 0:
        return {**user.permissions, **api_key.permissions}
    return user.permissions
```

### 4.5 User.has_permission override via _api_key_permissions

The `User.has_permission()` method (in `apps/accounts/models.py`) checks `self.permissions.get(key, False)`. We modify `User.permissions` (the `cached_property`) to fold in `_api_key_permissions` when set:

```python
@cached_property
def permissions(self) -> dict:
    base = self._base_permissions()  # existing logic
    if hasattr(self, '_api_key_permissions') and self._api_key_permissions:
        # API key scoped permissions override role permissions
        return {**base, **self._api_key_permissions}
    return base
```

This keeps the permission check in `User.has_permission()` unchanged — no views need modification.

## 5. API Endpoints

All endpoints live under `/api/accounts/api-keys/` (grouped with accounts since they belong to a user/tenant).

### 5.1 List API Keys

```
GET /api/accounts/api-keys/

Response 200:
{
  "count": 3,
  "results": [
    {
      "id": "uuid",
      "name": "CI Pipeline",
      "key_prefix": "fcrm_abc123def456",
      "permissions": {},
      "expires_at": null,
      "last_used_at": "2026-06-29T15:30:00Z",
      "last_ip_address": "203.0.113.42",
      "is_active": true,
      "created_at": "2026-06-01T10:00:00Z"
    }
  ]
}
```

Note: The full key is NEVER returned from the list endpoint — only `key_prefix`.

### 5.2 Create API Key

```
POST /api/accounts/api-keys/

Request:
{
  "name": "CI Pipeline Deployment",
  "permissions": {},            // optional — override permissions
  "expires_at": "2027-01-01T00:00:00Z"  // optional
}

Response 201:
{
  "id": "uuid",
  "name": "CI Pipeline Deployment",
  "key": "fcrm_<64_random_chars>",  // ⚠️ SHOWN ONCE
  "key_prefix": "fcrm_abc123def456",
  "permissions": {},
  "expires_at": "2027-01-01T00:00:00Z",
  "is_active": true,
  "created_at": "2026-06-30T12:00:00Z"
}
```

The response includes the full plaintext `key` — this is the ONLY time it's returned. Store it before dismissing.

### 5.3 Revoke API Key

```
POST /api/accounts/api-keys/{id}/revoke/

Request: (empty body)

Response 200:
{
  "id": "uuid",
  "name": "CI Pipeline",
  "is_active": false,
  "revoked_at": "2026-06-30T14:00:00Z"
}
```

### 5.4 Delete API Key

```
DELETE /api/accounts/api-keys/{id}/

Response 204: No Content
```

### 5.5 Update API Key

```
PATCH /api/accounts/api-keys/{id}/

Request (partial):
{
  "name": "CI Pipeline v2",
  "permissions": {"deals.view": true},
  "expires_at": "2027-06-01T00:00:00Z"
}

Response 200:
{
  "id": "uuid",
  "name": "CI Pipeline v2",
  "key_prefix": "fcrm_abc123def456",
  "permissions": {"deals.view": true},
  "expires_at": "2027-06-01T00:00:00Z",
  "is_active": true,
  "created_at": "2026-06-01T10:00:00Z"
}
```

### 5.6 Permission Checks

| Endpoint | Required Permission | Notes |
|---|---|---|
| `GET /api/accounts/api-keys/` | `settings.view` | List own tenant's keys |
| `POST /api/accounts/api-keys/` | `settings.manage` | Create a key (needs admin-level) |
| `PATCH /api/accounts/api-keys/{id}/` | `settings.manage` | Update key name/permissions |
| `POST .../{id}/revoke/` | `settings.manage` | Revoke a key |
| `DELETE /api/accounts/api-keys/{id}/` | `settings.manage` | Delete a key |

### 5.7 URL Configuration

```python
# apps/apikeys/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("api-keys/", views.APIKeyListCreateView.as_view(), name="apikeys-list-create"),
    path("api-keys/<uuid:pk>/", views.APIKeyDetailView.as_view(), name="apikeys-detail"),
    path("api-keys/<uuid:pk>/revoke/", views.APIKeyRevokeView.as_view(), name="apikeys-revoke"),
]
```

Registered in `config/urls.py`:

```python
path("accounts/", include("apps.apikeys.urls")),  # after existing accounts include
```

### 5.8 Views & Serializers

```python
# apps/apikeys/views.py

from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.core.permissions import TenantAwarePermission, RolePermission
from .models import APIKey


class APIKeySerializer(serializers.ModelSerializer):
    key = serializers.CharField(read_only=True)  # populated on create only

    class Meta:
        model = APIKey
        fields = (
            "id", "name", "key", "key_prefix", "permissions",
            "expires_at", "last_used_at", "last_ip_address",
            "is_active", "revoked_at", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "key", "key_prefix", "last_used_at",
            "last_ip_address", "is_active", "revoked_at",
            "created_at", "updated_at",
        )

    def create(self, validated_data):
        user = self.context["request"].user
        raw_key = APIKey.generate_key()
        instance = APIKey.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            name=validated_data["name"],
            key_prefix=APIKey.get_key_prefix(raw_key),
            key_hash=APIKey.hash_key(raw_key),
            permissions=validated_data.get("permissions", {}),
            expires_at=validated_data.get("expires_at"),
        )
        # Attach the plaintext key so the serializer can include it
        instance._plaintext_key = raw_key
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Inject plaintext key on create response only
        if hasattr(instance, "_plaintext_key"):
            data["key"] = instance._plaintext_key
        else:
            data.pop("key", None)  # never show on read/list
        return data


class APIKeyListCreateView(generics.ListCreateAPIView):
    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated, TenantAwarePermission, RolePermission]

    def get_queryset(self):
        return APIKey.objects.filter(tenant_id=self.request.user.tenant_id)

    def get_required_permission(self):
        if self.request.method == "POST":
            return "settings.manage"
        return "settings.view"  # list requires settings.view

    def perform_create(self, serializer):
        serializer.save()


class APIKeyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated, TenantAwarePermission, RolePermission]

    def get_required_permission(self):
        if self.request.method in ("PATCH", "PUT"):
            return "settings.manage"
        if self.request.method == "DELETE":
            return "settings.manage"
        return "settings.view"

    def get_queryset(self):
        return APIKey.objects.filter(tenant_id=self.request.user.tenant_id)


class APIKeyRevokeView(generics.UpdateAPIView):
    """Revoke an API key without deleting it."""
    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated, TenantAwarePermission, RolePermission]

    def get_required_permission(self):
        return "settings.manage"

    def get_queryset(self):
        return APIKey.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_update(self, serializer):
        from django.utils import timezone
        serializer.save(is_active=False, revoked_at=timezone.now())
```

## 6. Permission & Scope Binding

### 6.1 How API key permissions work

The `APIKey.permissions` JSONField uses the same key format as `Role.permissions`:

```json
{
  "contacts.view": true,
  "contacts.create": true,
  "contacts.edit": true,
  "deals.view": true,
  "deals.read": false
}
```

**Resolution rules:**
1. If `permissions` is empty `{}` — the key inherits **all** the owning user's role permissions
2. If `permissions` has entries — those are **merged on top** of the user's role permissions (key-scoped entries win)
3. Setting a permission to `false` in the key's permissions explicitly denies it, even if the user's role grants it

### 6.2 No new PermissionRegistry entries needed

The existing `PermissionRegistry` entries (in `apps/core/permission_registry.py`) cover everything an API key needs. No new permissions to register.

### 6.3 Admin-only creation via RolePermission

API key creation requires `settings.manage` which maps to the existing `SETTINGS_MANAGE` permission. By default only Admin and Manager roles have this — sales reps and viewers cannot create API keys.

### 6.4 Audit trail

Every API key request is logged via the existing activity system:
- `key_created` — actor, key name, timestamp
- `key_revoked` — actor, key name, timestamp
- `key_deleted` — actor, key name, timestamp

The `actor_id` is the owning user, and `metadata` includes the key name and ID.

## 7. Rate Limiting & Security

### 7.1 Rate Limiting

API key requests go through the same DRF throttle classes:

| Scope | Limit | Applies To |
|---|---|---|
| `user` | 1000/hour (configurable) | Authenticated requests |
| `anon` | 100/hour | Unauthenticated requests |

API key auth sets `request.user`, so `UserRateThrottle` applies. API key requests are subject to the same per-user rate limit as JWT requests.

**Future consideration:** A separate `api_key` rate limit scope if power users hit the 1000/hour ceiling.

### 7.2 Security Considerations

| Concern | Mitigation |
|---|---|
| Key leakage | Only hash stored; plaintext shown once |
| Brute force | 256-bit entropy (`secrets.token_urlsafe(48)` = 384 bits base64) — infeasible |
| Replay | API keys are static credentials — no replay protection beyond TLS. Future: request signing (HMAC) for P0 integrations |
| Revocation | Immediate: `revoked_at` check on every request; `is_active=False` |
| Expiry | Key-level `expires_at` — enforce rotation |
| Tenant isolation | `tenant_id` on APIKey model; `get_queryset` always filters by tenant |
| Rate limit bypass | Same throttle classes as JWT; no separate key-only throttle (yet) |
| Logging | Never log the full key; only prefix (`fcrm_abc1...`) |

### 7.3 Security-adjacent: `has_permission` override helper

The `User.has_permission()` method must fold in `_api_key_permissions`. The implementation change is in `apps/accounts/models.py`:

```python
def permissions(self) -> dict:  # replacing existing cached_property
    """Get resolved permissions dict for current tenant/API key."""
    base = self.role.resolved_permissions if self.role else {}
    if self.role and self.role.is_admin:
        from apps.core.permission_registry import PermissionRegistry
        base = {k: True for k in PermissionRegistry.all_keys()}
    # API key scope overrides
    if hasattr(self, '_api_key_permissions') and self._api_key_permissions:
        return {**base, **self._api_key_permissions}
    return base
```

## 8. Frontend Management Page

### 8.1 Location

New page: `frontend/src/pages/settings/api-keys-page.tsx`

Router entry in `frontend/src/router/index.tsx`:
```tsx
import { ApiKeysPage } from '../pages/settings/api-keys-page';
// ...
{ path: 'settings/api-keys', element: <ApiKeysPage /> },
```

Navigation: Settings → Integrations tab → "API Keys" integration card, OR a dedicated tab within Settings.

**Recommendation:** Add "API Keys" as a new tab in the Settings page alongside Profile, Team, and Integrations. This follows the existing UX pattern.

### 8.2 Component Structure

```
SettingsPage (existing)
├── ProfileTab (existing)
├── TeamTab (existing)
├── IntegrationsTab (existing)
└── ApiKeysTab (NEW)           ← new tab in the settings nav
```

### 8.3 ApiKeysTab Component

```
function ApiKeysTab()
│
├── Header: "API Keys" + "Generate New Key" button
│
├── EmptyState (when no keys exist)
│   └── "No API keys created yet. Generate one to get started."
│
├── KeyList (keys.length > 0)
│   ├── KeyCard (one per key)
│   │   ├── Name + key_prefix (fcrm_abc1...)
│   │   ├── Status badge: Active / Expired / Revoked
│   │   ├── Last used (relative time)
│   │   ├── Created date
│   │   └── Actions: Revoke, Delete
│   │
│   └── KeyCard (key detail expanded)
│       ├── Permissions summary (scope badge)
│       ├── Expiration date
│       ├── Last IP address
│       └── Edit name/permissions
│
└── CreateKeyModal (triggered by "Generate New Key")
    ├── Name input (required)
    ├── Expiration picker (optional)
    ├── Permission overrides (optional — advanced expandable section)
    └── "Generate" button
    │
    └── Success slide:
        └── ⚠️ Full key display + copy button + "Copy and store safely" warning
            └── "I've saved my key" acknowledgement button to close
```

### 8.4 API Service Hook

```typescript
// frontend/src/api/apikeys.ts (NEW)

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';

export interface APIKey {
  id: string;
  name: string;
  key?: string;          // Only present on creation
  key_prefix: string;
  permissions: Record<string, boolean>;
  expires_at: string | null;
  last_used_at: string | null;
  last_ip_address: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateAPIKeyPayload {
  name: string;
  permissions?: Record<string, boolean>;
  expires_at?: string;
}

export function useAPIKeys() {
  return useQuery({
    queryKey: ['api-keys'],
    queryFn: () =>
      apiClient.get<{ results: APIKey[] }>('/accounts/api-keys/')
        .then((r) => r.data.results),
  });
}

export function useCreateAPIKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateAPIKeyPayload) =>
      apiClient.post<APIKey>('/accounts/api-keys/', data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
}

export function useRevokeAPIKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.post(`/accounts/api-keys/${id}/revoke/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
}

export function useDeleteAPIKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.delete(`/accounts/api-keys/${id}/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
}

export function useUpdateAPIKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; name?: string; permissions?: Record<string, boolean>; expires_at?: string | null }) =>
      apiClient.patch<APIKey>(`/accounts/api-keys/${id}/`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
}
```

### 8.5 Frontend Types

Add to `frontend/src/types/index.ts`:

```typescript
export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  permissions: Record<string, boolean>;
  expires_at: string | null;
  last_used_at: string | null;
  last_ip_address: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

Warning: The `key` field is only present in the create response and should NOT be in the generic `APIKey` type. Use a separate `CreatedAPIKey extends APIKey { key: string }` for the create mutation result.

### 8.6 Key Creation UX Flow

1. User clicks "Generate New Key" → modal opens
2. User enters name, optionally sets expiry and permission overrides
3. Clicks "Generate" → POST to backend
4. Modal transitions to "Key Created" panel showing:
   - The full key in a monospace `<code>` block
   - A "Copy to Clipboard" button
   - A large warning banner: "Copy this key now. You won't be able to see it again."
   - "I've saved my key" acknowledgement button
5. User acknowledges → modal closes, key list refreshes showing the new entry

### 8.7 RoleGate Integration

API key management (create, revoke, delete) should be wrapped in `<RoleGate permission="settings.manage">` so non-admin users see the list but cannot create or modify keys.

## 9. Implementation Steps

### Backend (Builder)

| Step | File | What |
|------|------|------|
| 1 | `backend/apps/apikeys/__init__.py` | Create new app package |
| 2 | `backend/apps/apikeys/apps.py` | AppConfig with `default_auto_field` |
| 3 | `backend/apps/apikeys/models.py` | `APIKey` model (TenantScopedModel) |
| 4 | `backend/apps/apikeys/migrations/0001_initial.py` | `python manage.py makemigrations` |
| 5 | `backend/apps/apikeys/auth.py` | `APIKeyAuthentication` DRF auth backend |
| 6 | `backend/config/settings/base.py` | Add `APIKeyAuthentication` to `DEFAULT_AUTHENTICATION_CLASSES` (first in tuple) |
| 7 | `backend/apps/accounts/models.py` | Modify `permissions` cached_property to fold in `_api_key_permissions` |
| 8 | `backend/apps/apikeys/serializers.py` | `APIKeySerializer` with create-time plaintext key injection |
| 9 | `backend/apps/apikeys/views.py` | ListCreate, Detail, Revoke views |
| 10 | `backend/apps/apikeys/urls.py` | URL patterns |
| 11 | `backend/config/urls.py` | Register `apps.apikeys.urls` under `accounts/` |
| 12 | `backend/config/settings/base.py` | Add `apps.apikeys` to `INSTALLED_APPS` |
| 13 | `backend/apps/core/permission_registry.py` | Add `API_KEYS_MANAGE` permission if needed (likely not — `settings.manage` covers it) |
| 14 | Run migrations | `python manage.py makemigrations apikeys && python manage.py migrate` |
| 15 | Add admin registration | `apps/apikeys/admin.py` for Django admin |

### Frontend (Builder)

| Step | File | What |
|------|------|------|
| 1 | `frontend/src/types/index.ts` | Add `APIKey` and `CreatedAPIKey` types |
| 2 | `frontend/src/api/apikeys.ts` | API hooks (useAPIKeys, useCreateAPIKey, useRevokeAPIKey, useDeleteAPIKey, useUpdateAPIKey) |
| 3 | `frontend/src/pages/settings/api-keys-page.tsx` | Full API Keys management component |
| 4 | `frontend/src/pages/settings/settings-page.tsx` | Add "API Keys" tab to tabs array + ApiKeysTab rendering |
| 5 | `frontend/src/router/index.tsx` | Add `/settings/api-keys` route (optional — could be tab-only) |

### Tests (Prober)

| # | Test | Description |
|---|------|-------------|
| 1 | Test API key generation | POST returns 201 with full key |
| 2 | Test key hash storage | Verify hash stored, plaintext NOT retrievable via GET |
| 3 | Test auth via API key | GET with valid key returns 200, invalid returns 401 |
| 4 | Test key expiry | Expired key returns 401 |
| 5 | Test key revocation | Revoked key returns 401 |
| 6 | Test tenant isolation | Key from tenant A cannot access tenant B resources |
| 7 | Test permissions isolation | Key with only `deals.view` cannot create deals |
| 8 | Test key deletion | DELETE returns 204, key cannot authenticate |
| 9 | Test last_used_at updates | `last_used_at` is updated on auth (after 5-min cooldown) |
| 10 | Test list returns no full key | GET list response does not contain `key` field |
| 11 | Test admin-only creation | Non-admin users get 403 on POST |

## 10. Open Questions

| Question | Status | Resolution |
|----------|--------|------------|
| Should API keys have a separate throttle rate? | Deferred | Start with existing `UserRateThrottle`; add `APIKeyRateThrottle` if needed |
| Should we log every API key request to activity timeline? | Deferred | Only create/revoke/delete events; individual request logging is excessive |
| Should API keys support IP whitelisting? | No | Adds complexity that SMB audience won't use; revisit for Enterprise tier |
| Should API keys support CORS restrict-to-origin? | No | Same as IP whitelisting — Enterprise feature |
| Should the key prefix encode the tenant ID? | Skipped | `tenant_id` is already in the DB row and the auth backend filters by key_hash directly; encoding tenant in the key adds complexity without benefit since we don't shard by prefix |
| Should we add an `apikeys:manage` permission to `PermissionRegistry`? | No | `settings.manage` already covers this; API key management is a tenant-level setting |
| Should we use `rest_framework_api_key` library instead? | No | It's an external dependency with its own versioning; our custom solution is ~150 lines total and tightly integrated with our multi-tenant pattern |

---

*End of spec. Hand off to builder for implementation.*
