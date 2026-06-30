# Phase 4 — Role-Based Access Control Specification

**Date:** 2026-06-30
**Author:** Atlas (allstars-atlas)
**Status:** Proposed
**Priority:** P3

---

## Table of Contents

1. [ADR-026: Flexible Role Model with Granular Permissions](#1-adr-026-flexible-role-model-with-granular-permissions)
2. [Data Model: Extending Role + Membership](#2-data-model-extending-role--membership)
3. [Permission Registry](#3-permission-registry)
4. [Backend Enforcement: RolePermission Class](#4-backend-enforcement-rolepermission-class)
5. [API Contracts](#5-api-contracts)
6. [Frontend Enforcement: useRole + RoleGate](#6-frontend-enforcement-userole--rolegate)
7. [Settings UI: User Management Page](#7-settings-ui-user-management-page)
8. [Seed Data & Migration](#8-seed-data--migration)
9. [Implementation Order](#9-implementation-order)
10. [Acceptance Criteria](#10-acceptance-criteria)
11. [Open Questions](#11-open-questions)

---

## 1. ADR-026: Flexible Role Model with Granular Permissions

**Status:** Proposed
**Date:** 2026-06-30

### Context

FrontierCRM needs to restrict what users can see and do based on their role within a tenant. The project already has:

- A `Role` model (`apps/teams/models.py`) with `tenant`, `name`, `description`, `permissions` JSONField, `is_admin` flag
- A `Membership` model linking `User -> Tenant` with a FK to `Role`
- `TenantAwarePermission` — the default DRF permission class that checks authentication + tenant membership
- Every ViewSet filters by `tenant_id` but no view checks role or permissions

The existing `Role.permissions` JSON field stores flat dicts like:
```json
{"manage_team": true, "manage_billing": true, "manage_settings": true, "export_data": true}
```

This is used at signup time but never enforced at the API layer.

### Options Considered

**Option A — Django's built-in `auth.Permission` model with `Group`**
Use Django's stock permission system. Define permissions via `Meta.permissions` on each model, assign them to groups that map to roles.

- Pros: No new models; works with DRF's `DjangoModelPermissions` out of the box; Django admin works immediately
- Cons: Multi-tenant isolation is painful (permissions are global, not scoped to a tenant); `Group` doesn't have a `tenant_id` FK; migrating existing user base requires syncing every tenant's set of groups/permissions; `content_type` FK is tenant-blind; each new feature needs `Meta.permissions` boilerplate across 15+ models; no hierarchical roles (can't say "manager inherits everything sales_rep has")
- **Rejected** — too much fighting Django's single-tenant assumption

**Option B — Existing JSONField Role Permissions (keep as-is, just enforce)**
The current `Role.permissions` JSON dict is already flexible and tenant-scoped. Define a canonical permission registry (a Python enum/set), let admin/owner users define custom roles via the UI, and add a DRF permission class that checks `request.user.membership.role.permissions` against the view's required permission key.

- Pros: Zero schema changes; already works with existing `Role` and `Membership`; tenant-scoped by design; admin users can create arbitrary role names with any permission combination
- Cons: JSONField means no referential integrity on permission keys (a typo in the UI silently grants nothing); no way to enumerate "all users with X permission" at the DB level without JSON key lookups; permission checks are string comparisons in Python, not DB joins
- **Accepted** — the flexibility of tenant-customizable roles outweighs the lack of referential integrity, and the permission registry provides a canonical source of truth for the UI (so typo-cases are caught at the form validation layer)

**Option C — Hybrid: Bitfield or integer bitmask**
Assign each permission a bit position; `Role.permissions` becomes a `BigIntegerField` bitmask.

- Pros: Fast DB-level checks (`permissions & 1 << 3`); compact storage
- Cons: Max 64 permissions (bitmask width); no named permissions without a lookup table; can't express "this role can only see own records" (object-level, not view-level); migration complexity for adding/removing bits
- **Rejected** — 64-permission ceiling is too tight as the feature set grows, and the bitmask is opaque without tooling

**Option D — Permission check via Membership.role directly on the User model**
Add a helper method on the User model (or a cached property) that returns the effective role and permission dict for the current tenant.

- Pros: Simplest API for frontend and backend — `request.user.permissions` returns a dict; no new model; natural extension of current pattern
- Cons: Does not address the `is_admin` short-circuit pattern, object-level ownership, or hierarchy ("manager" includes "sales_rep" permissions)
- **Accepted with enhancement** — combine with a `@dataclass` for the resolved permission set, and add an `inherits_from` field on Role for hierarchy

### Decision

**Hybrid of Option B + Option D: keep the existing `Role.permissions` JSONField, define a canonical Permission Registry (Python enum/set), and add backend enforcement via a custom DRF `RolePermission` class plus a User model helper.**

Rationale:
1. Zero schema migration — both `Role` and `Membership` already exist with the right shape
2. Tenant-scoped by design — `Role` has a `tenant` FK; `Membership` links user to tenant to role
3. Admin users can create custom role names with any permission combination via the settings UI
4. The Permission Registry serves as a single source of truth: the backend uses it for `@require_permission` decorators, the frontend uses it for `RoleGate` components, and the form validation uses it for dropdown options
5. Permission checks use simple dict membership (`"deals.create" in user.permissions`) — no joins, no cache invalidations, negligible latency
6. `is_admin` provides a short-circuit: admins bypass all permission checks (except tenant-scoping)

### Consequences

- No new database models
- New file: `apps/core/permission_registry.py` — canonical enum of all permission keys
- New/modified files in `apps/core/permissions.py` — `RolePermission` class
- New helper on `User` model: `user.permissions` and `user.role` cached properties
- Frontend: new `useRole()` hook and `<RoleGate>` component
- New settings page: User Management with role assignment
- Existing `seed_demo.py` must be updated to create proper roles (not just admin)

---

## 2. Data Model: Extending Role + Membership

**No new models.** The existing models are sufficient. This section documents the conventions and extensions.

### 2.1 Role Model (existing — `apps/teams/models.py`)

```
Role
├── id             UUIDField (PK, auto)
├── tenant         FK -> Tenant
├── name           CharField(100)       # e.g. "Admin", "Manager", "Sales Rep", "Viewer"
├── description    TextField            # Human-readable purpose
├── permissions    JSONField(default=dict)  # {"deals.create": true, "deals.view": true, ...}
├── is_admin       BooleanField(default=False)  # Short-circuit: admins have all permissions
├── inherits_from  FK -> Role (self, null=True, blank=True)  # NEW: role hierarchy
├── created_at     DateTimeField
└── updated_at     DateTimeField
```

**New field:** `inherits_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)`

When resolving a role's permissions, merge `inherits_from.permissions` first, then overlay the role's own permissions. This allows a "Manager" role to inherit all "Sales Rep" permissions and add a few more.

Permission resolution algorithm:
```python
@property
def resolved_permissions(self) -> dict:
    """Merge inherited + own permissions (own wins)."""
    base = {}
    if self.inherits_from:
        base = dict(self.inherits_from.resolved_permissions)
    base.update(self.permissions)
    return base
```

**Caveat:** `inherits_from` must be on the same tenant. Validate in `clean()` or at the serializer level.

### 2.2 Membership Model (existing — `apps/teams/models.py`)

```
Membership
├── id             UUIDField (PK)
├── user           FK -> User
├── tenant         FK -> Tenant
├── role           FK -> Role (nullable)
├── team           FK -> Team (nullable)
├── is_owner       BooleanField(default=False)  # Billing owner — separate from role
├── is_active      BooleanField(default=True)
└── joined_at      DateTimeField
```

**No changes needed.** The `role` FK already exists. The `is_owner` field is separate from permission checks — owners are not automatically admins (though they usually should be assigned the Admin role).

### 2.3 User Model Helper Methods (new — `apps/accounts/models.py`)

Add cached properties to `User`:

```python
from functools import cached_property

class User(AbstractUser):
    # ... existing fields ...

    @cached_property
    def membership(self) -> Membership | None:
        """Get active membership for current tenant."""
        return self.memberships.filter(tenant_id=self.tenant_id, is_active=True).first()

    @cached_property
    def role(self) -> Role | None:
        """Get effective role for current tenant."""
        m = self.membership
        return m.role if m else None

    @cached_property
    def permissions(self) -> dict:
        """Get resolved permissions dict for current tenant's role."""
        if not self.role:
            return {}
        if self.role.is_admin:
            return {k: True for k in PermissionRegistry.all_keys()}
        return self.role.resolved_permissions

    def has_permission(self, key: str) -> bool:
        """Check if user has a specific permission key."""
        return self.permissions.get(key, False)
```

**Important:** `cached_property` is per-request-safe in Django because each request creates a new `User` instance via the auth middleware. If the user's role changes mid-request (rare), the stale cache is acceptable.

### 2.4 Migration

A single new migration for `apps/teams`:
- Add `inherits_from` FK to `Role` (nullable, `SET_NULL` on delete)

---

## 3. Permission Registry

A canonical list of all permission keys in the system. Serves as:
- The single source of truth for what permissions exist
- The dropdown options in the "Create/Edit Role" form
- The set used by the `is_admin` short-circuit
- Documentation for what each permission controls

### 3.1 File: `apps/core/permission_registry.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class PermissionDef:
    key: str
    label: str
    description: str
    group: str  # e.g. "Deals", "Contacts", "Admin"


class PermissionRegistry:
    """Canonical set of all permissions in the system."""

    # ── Contacts ──────────────────────────────────────────────
    CONTACTS_VIEW = PermissionDef("contacts.view", "View Contacts", "See contact list and details", "Contacts")
    CONTACTS_CREATE = PermissionDef("contacts.create", "Create Contacts", "Add new contacts", "Contacts")
    CONTACTS_EDIT = PermissionDef("contacts.edit", "Edit Contacts", "Modify contact details", "Contacts")
    CONTACTS_DELETE = PermissionDef("contacts.delete", "Delete Contacts", "Remove contacts", "Contacts")
    CONTACTS_EXPORT = PermissionDef("contacts.export", "Export Contacts", "Download contacts as CSV/XLSX", "Contacts")
    CONTACTS_IMPORT = PermissionDef("contacts.import", "Import Contacts", "Bulk import contacts from CSV", "Contacts")

    # ── Deals ─────────────────────────────────────────────────
    DEALS_VIEW = PermissionDef("deals.view", "View Deals", "See deal list and details", "Deals")
    DEALS_CREATE = PermissionDef("deals.create", "Create Deals", "Add new deals", "Deals")
    DEALS_EDIT = PermissionDef("deals.edit", "Edit Deals", "Modify deal details and stage", "Deals")
    DEALS_DELETE = PermissionDef("deals.delete", "Delete Deals", "Remove deals", "Deals")
    DEALS_EXPORT = PermissionDef("deals.export", "Export Deals", "Download deals as CSV/XLSX", "Deals")

    # ── Pipelines ─────────────────────────────────────────────
    PIPELINES_VIEW = PermissionDef("pipelines.view", "View Pipelines", "See pipeline and stages", "Pipelines")
    PIPELINES_MANAGE = PermissionDef("pipelines.manage", "Manage Pipelines", "Create/edit/delete pipelines and stages", "Pipelines")

    # ── Activities ────────────────────────────────────────────
    ACTIVITIES_VIEW = PermissionDef("activities.view", "View Activities", "See activity timeline", "Activities")
    ACTIVITIES_CREATE = PermissionDef("activities.create", "Log Activities", "Add calls, emails, meetings to timeline", "Activities")
    ACTIVITIES_DELETE = PermissionDef("activities.delete", "Delete Activities", "Remove activity entries", "Activities")
    ACTIVITIES_EXPORT = PermissionDef("activities.export", "Export Activities", "Download activity log", "Activities")

    # ── Email ─────────────────────────────────────────────────
    EMAIL_VIEW = PermissionDef("email.view", "View Emails", "See synced emails", "Email")
    EMAIL_SEND = PermissionDef("email.send", "Send Emails", "Compose and send outbound emails", "Email")
    EMAIL_DELETE = PermissionDef("email.delete", "Delete Emails", "Remove email threads", "Email")

    # ── Notes ─────────────────────────────────────────────────
    NOTES_CREATE = PermissionDef("notes.create", "Create Notes", "Add notes to records", "Notes")
    NOTES_DELETE = PermissionDef("notes.delete", "Delete Notes", "Remove notes", "Notes")

    # ── Files ─────────────────────────────────────────────────
    FILES_UPLOAD = PermissionDef("files.upload", "Upload Files", "Attach files to records", "Files")
    FILES_DELETE = PermissionDef("files.delete", "Delete Files", "Remove uploaded files", "Files")

    # ── Reports & Forecasting ─────────────────────────────────
    REPORTS_VIEW = PermissionDef("reports.view", "View Reports", "See dashboards and reports", "Reports")
    REPORTS_EXPORT = PermissionDef("reports.export", "Export Reports", "Download report data", "Reports")
    FORECAST_VIEW = PermissionDef("forecast.view", "View Forecast", "See pipeline forecasting", "Forecast")
    FORECAST_MANAGE = PermissionDef("forecast.manage", "Manage Forecast", "Edit forecast scenarios and targets", "Forecast")

    # ── Team & Settings ───────────────────────────────────────
    TEAM_VIEW = PermissionDef("team.view", "View Team", "See team members list", "Admin")
    TEAM_INVITE = PermissionDef("team.invite", "Invite Members", "Send invitations to new users", "Admin")
    TEAM_MANAGE_ROLES = PermissionDef("team.manage_roles", "Manage Roles", "Create/edit roles and assign permissions", "Admin")
    TEAM_REMOVE = PermissionDef("team.remove", "Remove Members", "Remove users from tenant", "Admin")
    SETTINGS_VIEW = PermissionDef("settings.view", "View Settings", "See tenant settings", "Admin")
    SETTINGS_MANAGE = PermissionDef("settings.manage", "Manage Settings", "Modify tenant settings and integrations", "Admin")

    # ── Data ──────────────────────────────────────────────────
    EXPORT_ALL = PermissionDef("export.all", "Export All Data", "Bulk export of all CRM data", "Admin")
    IMPORT_DATA = PermissionDef("import.data", "Import Data", "Bulk import contacts, deals from CSV", "Admin")
    AUDIT_LOG = PermissionDef("audit.log", "View Audit Log", "See user activity and changes", "Admin")

    # ── All permissions list ──────────────────────────────────
    ALL: ClassVar[list[PermissionDef]] = []

    @classmethod
    def all_keys(cls) -> list[str]:
        return [p.key for p in cls.ALL]

    @classmethod
    def all_by_group(cls) -> dict[str, list[PermissionDef]]:
        groups: dict[str, list[PermissionDef]] = {}
        for p in cls.ALL:
            groups.setdefault(p.group, []).append(p)
        return groups


# Build ALL list from class attributes
PermissionRegistry.ALL = [
    v for v in PermissionRegistry.__dict__.values()
    if isinstance(v, PermissionDef)
]
```

### 3.2 Default Role Templates

The following role templates define the permission sets for each default role. These are the starting point — admins can customize them in the UI.

**Admin** (`is_admin=True`):
- Short-circuits all permission checks
- Has `manage_settings`, `manage_team`, `manage_roles`, `export`, `import`, `audit_log`

**Manager** (inherits from Sales Rep):
```
inherits_from: Sales Rep
extra: deals.create, deals.edit, deals.delete,
       pipelines.manage,
       team.view, team.invite,
       reports.view, reports.export,
       forecast.view, forecast.manage,
       activities.delete,
       contacts.delete
```

**Sales Rep** (base role):
```
contacts.view = true, contacts.create = true, contacts.edit = true
deals.view = true, deals.create = true, deals.edit = true
pipelines.view = true
activities.view = true, activities.create = true
email.view = true, email.send = true
notes.create = true
files.upload = true
reports.view = true
forecast.view = true
```

**Viewer** (read-only):
```
contacts.view = true
deals.view = true
pipelines.view = true
activities.view = true
email.view = true
reports.view = true
forecast.view = true
```

---

## 4. Backend Enforcement: RolePermission Class

### 4.1 File: `apps/core/permissions.py` (additions)

```python
from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class TenantAwarePermission(BasePermission):
    """Existing — authentication + tenant check."""
    # ... unchanged ...


class RolePermission(BasePermission):
    """
    Role-based permission check. View must declare a `required_permission` attribute
    or use the `@require_permission` decorator.

    Usage:
        class DealViewSet(viewsets.ModelViewSet):
            permission_classes = [TenantAwarePermission, RolePermission]
            required_permission = "deals.view"  # Base action, or dict per action:

            def get_required_permission(self):
                action_map = {
                    "list": "deals.view",
                    "retrieve": "deals.view",
                    "create": "deals.create",
                    "update": "deals.edit",
                    "partial_update": "deals.edit",
                    "destroy": "deals.delete",
                }
                return action_map.get(self.action, "deals.view")
    """

    def has_permission(self, request: Request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Resolve the required permission key from the view
        required = None
        if hasattr(view, "get_required_permission"):
            required = view.get_required_permission()
        elif hasattr(view, "required_permission"):
            required = view.required_permission

        if required is None:
            return True  # No permission required — allow through

        if required == "__admin__":
            return user.role.is_admin if user.role else False

        return user.has_permission(required)
```

### 4.2 View Usage Pattern

Each ViewSet declares what permission is needed. The recommended pattern is a `get_required_permission` method:

```python
class DealViewSet(viewsets.ModelViewSet):
    permission_classes = [TenantAwarePermission, RolePermission]
    queryset = Deal.objects.all()
    serializer_class = DealSerializer

    def get_required_permission(self) -> str | None:
        return {
            "list": "deals.view",
            "retrieve": "deals.view",
            "create": "deals.create",
            "update": "deals.edit",
            "partial_update": "deals.edit",
            "destroy": "deals.delete",
        }.get(self.action)
```

For custom `@action` endpoints:

```python
    @action(detail=True, methods=["post"])
    def stage_change(self, request, pk=None):
        if not request.user.has_permission("deals.edit"):
            return Response({"error": "Permission denied"}, status=403)
        # ... proceed ...
```

For function-based views using `@api_view`:

```python
from apps.core.permissions import require_permission

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def export_deals(request):
    # Use manual check if decorator pattern isn't appropriate
    if not request.user.has_permission("deals.export"):
        return Response({"error": "Permission denied"}, status=403)
    # ...
```

### 4.3 Object-Level Ownership (Future / P4)

For P3, permission checks are view-level (can you see deals at all?). P4 can add object-level ownership:

```python
class OwnRecordOnly(BasePermission):
    """User can only access records they own (assigned_to/owner)."""
    def has_object_permission(self, request, view, obj):
        owner_id = getattr(obj, "owner_id", None) or getattr(obj, "assigned_to_id", None)
        user_id = str(request.user.id)
        if owner_id and str(owner_id) != user_id:
            return request.user.has_permission("deals.view_all")  # Manager+ can see all
        return True
```

This is noted here but **not part of the P3 implementation**.

---

## 5. API Contracts

### 5.1 User Management Endpoints

**New endpoints under `/api/teams/`:**

#### `GET /api/teams/memberships/` — List team members with role info

Already exists via `MembershipViewSet`. Add `role_permissions` to the response:

**Response:**
```json
[
  {
    "id": "uuid",
    "user": "uuid",
    "user_email": "alice@example.com",
    "user_name": "Alice Wong",
    "role_id": "uuid",
    "role_name": "Sales Rep",
    "team_id": "uuid",
    "team_name": "Everyone",
    "is_owner": false,
    "is_active": true,
    "joined_at": "2026-01-15T10:00:00Z"
  }
]
```

**Changes needed:** Update `MembershipSerializer` to include `user_name` (first + last) and improve `role_name` default.

#### `PATCH /api/teams/memberships/{id}/` — Update role assignment

**Request:**
```json
{
  "role_id": "uuid-for-manager-role"
}
```

**Response:** Updated membership object.

**Authorization:** Requires `team.manage_roles` permission.

#### `POST /api/teams/memberships/invite/` — Invite user to tenant

Already exists. Update to require `team.invite` permission and use the Permission Registry for role validation.

**Request:**
```json
{
  "email": "newuser@example.com",
  "role_id": "uuid"
}
```

#### `DELETE /api/teams/memberships/{id}/` — Remove member

New action. Requires `team.remove` permission.

#### `GET /api/teams/memberships/me/` — Current user's membership info

New endpoint. Returns the current user's membership (role name, permissions) for the active tenant.

**Response:**
```json
{
  "id": "uuid",
  "role_id": "uuid",
  "role_name": "Sales Rep",
  "is_admin": false,
  "is_owner": false,
  "permissions": {
    "contacts.view": true,
    "contacts.create": true,
    "deals.view": true,
    ...
  }
}
```

This is the primary endpoint the frontend uses to determine what UI to show.

### 5.2 Role Management Endpoints

**New endpoints under `/api/teams/roles/`:**

#### `GET /api/teams/roles/` — List roles for tenant (existing)

Add `permissions` and `inherits_from` to the serialized response.

#### `POST /api/teams/roles/` — Create custom role

**Request:**
```json
{
  "name": "Junior Sales Rep",
  "description": "Limited-scope sales role",
  "permissions": {
    "contacts.view": true,
    "deals.view": true,
    "deals.create": true
  },
  "inherits_from_id": null
}
```

**Authorization:** Requires `team.manage_roles` permission.

#### `PATCH /api/teams/roles/{id}/` — Update role permissions

**Authorization:** Requires `team.manage_roles` permission.

#### `DELETE /api/teams/roles/{id}/` — Delete custom role

**Authorization:** Requires `team.manage_roles` permission. Guard against deleting default system roles.

### 5.3 Permission Registry Endpoint

#### `GET /api/teams/permissions/` — List all available permissions

New read-only endpoint. Returns the canonical permission registry.

**Response:**
```json
{
  "groups": {
    "Contacts": [
      {"key": "contacts.view", "label": "View Contacts", "description": "See contact list and details"},
      ...
    ],
    "Deals": [...],
    ...
  }
}
```

**Authorization:** Requires authentication. No special role needed — permissions are read-only documentation.

### 5.4 Summary: URL Changes

| Method | URL | Action | Permission Required |
|--------|-----|--------|-------------------|
| GET | `/api/teams/memberships/me/` | Current user's role + permissions | (auth) |
| GET | `/api/teams/memberships/` | List members | `team.view` |
| PATCH | `/api/teams/memberships/{id}/` | Update role | `team.manage_roles` |
| DELETE | `/api/teams/memberships/{id}/` | Remove member | `team.remove` |
| POST | `/api/teams/memberships/invite/` | Invite user | `team.invite` |
| GET | `/api/teams/roles/` | List roles | (auth) |
| POST | `/api/teams/roles/` | Create role | `team.manage_roles` |
| PATCH | `/api/teams/roles/{id}/` | Update role | `team.manage_roles` |
| DELETE | `/api/teams/roles/{id}/` | Delete role | `team.manage_roles` |
| GET | `/api/teams/permissions/` | List permissions | (auth) |

---

## 6. Frontend Enforcement: useRole + RoleGate

### 6.1 `useRole()` Hook

File: `frontend/src/hooks/useRole.ts`

```typescript
import { useMemo } from 'react';
import { useAuthStore } from '../store/auth';

interface RoleInfo {
  roleName: string | null;
  isAdmin: boolean;
  isOwner: boolean;
  permissions: Record<string, boolean>;
  hasPermission: (key: string) => boolean;
  hasAnyPermission: (keys: string[]) => boolean;
  hasAllPermissions: (keys: string[]) => boolean;
}

export function useRole(): RoleInfo {
  const { user, membership } = useAuthStore();

  return useMemo(() => {
    // membership is loaded from /api/teams/memberships/me/
    const perms = membership?.permissions ?? {};
    return {
      roleName: membership?.role_name ?? null,
      isAdmin: membership?.is_admin ?? false,
      isOwner: membership?.is_owner ?? false,
      permissions: perms,
      hasPermission: (key: string) =>
        membership?.is_admin ?? false ? true : !!perms[key],
      hasAnyPermission: (keys: string[]) =>
        keys.some(k => perms[k] === true) || (membership?.is_admin ?? false),
      hasAllPermissions: (keys: string[]) =>
        keys.every(k => perms[k] === true) || (membership?.is_admin ?? false),
    };
  }, [membership]);
}
```

### 6.2 `RoleGate` Component

File: `frontend/src/components/molecules/role-gate.tsx`

```typescript
import { ReactNode } from 'react';
import { useRole } from '../../hooks/useRole';

interface RoleGateProps {
  permission?: string;
  anyPermission?: string[];
  allPermissions?: string[];
  fallback?: ReactNode;
  children: ReactNode;
}

export function RoleGate({
  permission,
  anyPermission,
  allPermissions,
  fallback = null,
  children,
}: RoleGateProps) {
  const { hasPermission, hasAnyPermission, hasAllPermissions } = useRole();

  let allowed = false;

  if (permission) {
    allowed = hasPermission(permission);
  } else if (anyPermission) {
    allowed = hasAnyPermission(anyPermission);
  } else if (allPermissions) {
    allowed = hasAllPermissions(allPermissions);
  } else {
    allowed = true;
  }

  return <>{allowed ? children : fallback}</>;
}
```

### 6.3 Fetching Membership on Auth

The auth store needs to fetch the user's membership + permissions after login. Add to `fetchMe` or a new `fetchMembership`:

```typescript
// In auth.ts store, after fetchMe:
fetchMembership: async () => {
  try {
    const { data } = await apiClient.get('/teams/memberships/me/');
    set({ membership: data });
  } catch {
    // No membership = user has no tenant yet (signup flow)
    set({ membership: null });
  }
}
```

### 6.4 Usage Examples

**Conditional button:**
```tsx
import { RoleGate } from '../../components/molecules/role-gate';

<RoleGate permission="deals.create">
  <button onClick={handleNewDeal}>New Deal</button>
</RoleGate>
```

**Conditional tab/route:**
```tsx
<RoleGate permission="settings.view">
  <NavItem to="/settings" label="Settings" />
</RoleGate>
```

**Disabled with tooltip:**
```tsx
<RoleGate permission="contacts.delete" fallback={
  <button disabled className="opacity-50 cursor-not-allowed"
          title="You don't have permission to delete contacts">
    Delete
  </button>
}>
  <button onClick={handleDelete} className="text-red-500">Delete</button>
</RoleGate>
```

**Admin-only section:**
```tsx
<RoleGate permission="__admin__">
  <AdminPanel />
</RoleGate>
```

---

## 7. Settings UI: User Management Page

### 7.1 Page Structure

File: `frontend/src/pages/settings/users-page.tsx`

Route: `/settings/users`

**Layout:**
```
┌──────────────────────────────────────────────┐
│  [Back to Settings]                          │
│                                              │
│  User Management                              │
│  ─────────────────────────────────────────── │
│                                              │
│  ┌── Invite Member ──────────────────────┐   │
│  │  Email: [________________________]    │   │
│  │  Role:  [Sales Rep        ▼]         │   │
│  │  [Send Invitation]                   │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  Team Members (6)                            │
│                                              │
│  ┌── Member List ───────────────────────┐    │
│  │  Alice Wong    alice@...  Admin    ⋮  │    │
│  │  Bob Martinez  bob@...    Manager  ⋮  │    │
│  │  Carol Davis   carol@...  Sales    ⋮  │    │
│  │  ...                                    │    │
│  └──────────────────────────────────────┘   │
│                                              │
│  Role Templates                              │
│  ┌── Role Cards ───────────────────────┐    │
│  │  ┌──────┐ ┌──────┐ ┌──────┐       │    │
│  │  │Admin │ │Manager│ │Sales │       │    │
│  │  │ 1    │ │ 1     │ │ 4    │       │    │
│  │  └──────┘ └──────┘ └──────┘       │    │
│  │  [+ Create Role]                  │    │
│  └──────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

### 7.2 Key UX Patterns

1. **Invite flow:** Email input + role dropdown (populated from roles list). On submit, calls `POST /api/teams/memberships/invite/`.

2. **Member row actions:** Click the row to expand and change role via a dropdown. Admin can't demote themselves from admin without another admin present.

3. **Role creation modal:** Form with role name, description, and permission checkboxes grouped by category. Uses the Permission Registry endpoint to populate checkboxes.

4. **Edit role modal:** Same form but pre-filled. Protect against renaming/deleting built-in roles (Admin, Manager, Sales Rep, Viewer).

5. **Delete confirmation:** Warn if members are assigned to the role being deleted.

### 7.3 Route Guards

The Users page itself requires `team.manage_roles` or `team.view`:

```tsx
<Route
  path="/settings/users"
  element={
    <RoleGate permission="team.manage_roles" fallback={<Navigate to="/settings" />}>
      <UsersPage />
    </RoleGate>
  }
/>
```

---

## 8. Seed Data & Migration

### 8.1 Migration (apps/teams)

A single migration:
```
apps/teams/migrations/0002_role_inherits_from.py
```

Adds `inherits_from` FK to `Role`.

### 8.2 Default Role Seeding

The `SignupSerializer` in `apps/accounts/serializers.py` already creates an Admin role. This needs to be updated to also create the other three default roles, with their full permission sets.

File: `apps/accounts/serializers.py` (modify `SignupSerializer.create`)

```python
def create(self, validated_data):
    password = validated_data.pop("password")
    org_name = validated_data.pop("organization_name", None)

    email = validated_data.get("email", "user@unknown")
    tenant = Tenant.objects.create(name=org_name or f"{email.split('@')[0]}'s Organization")

    # Create default roles
    roles = {}
    for role_def in DEFAULT_ROLES:
        r = Role.objects.create(
            tenant=tenant,
            name=role_def["name"],
            description=role_def["description"],
            permissions=role_def["permissions"],
            is_admin=role_def.get("is_admin", False),
        )
        roles[role_def["name"]] = r

    # Set up inheritance (Manager -> Sales Rep)
    if "Manager" in roles and "Sales Rep" in roles:
        roles["Manager"].inherits_from = roles["Sales Rep"]
        roles["Manager"].save(update_fields=["inherits_from"])

    # Create default team
    default_team = Team.objects.create(tenant=tenant, name="Everyone", description="Default team — all members")

    # Create the user as admin
    user = UserModel(**validated_data, tenant_id=tenant.id)
    user.set_password(password)
    user.save()

    Membership.objects.create(
        user=user, tenant=tenant,
        role=roles["Admin"],
        team=default_team,
        is_owner=True,
    )

    return user
```

The `DEFAULT_ROLES` constant should live in a new file `apps/core/role_defaults.py`:

```python
DEFAULT_ROLES = [
    {
        "name": "Admin",
        "description": "Full administrative access — can do everything",
        "is_admin": True,
        "permissions": {},
    },
    {
        "name": "Manager",
        "description": "Team manager — can manage deals, view team, edit pipelines",
        "is_admin": False,
        "permissions": {
            "deals.create": True, "deals.edit": True, "deals.delete": True,
            "pipelines.manage": True,
            "team.view": True, "team.invite": True,
            "reports.view": True, "reports.export": True,
            "forecast.view": True, "forecast.manage": True,
            "activities.delete": True,
            "contacts.delete": True,
        },
    },
    {
        "name": "Sales Rep",
        "description": "Sales representative — manage own deals and contacts",
        "is_admin": False,
        "permissions": {
            "contacts.view": True, "contacts.create": True, "contacts.edit": True,
            "deals.view": True, "deals.create": True, "deals.edit": True,
            "pipelines.view": True,
            "activities.view": True, "activities.create": True,
            "email.view": True, "email.send": True,
            "notes.create": True,
            "files.upload": True,
            "reports.view": True,
            "forecast.view": True,
        },
    },
    {
        "name": "Viewer",
        "description": "Read-only access — can view but not create or edit",
        "is_admin": False,
        "permissions": {
            "contacts.view": True,
            "deals.view": True,
            "pipelines.view": True,
            "activities.view": True,
            "email.view": True,
            "reports.view": True,
            "forecast.view": True,
        },
    },
]
```

### 8.3 Update `seed_demo.py`

The demo seed command must also create the four default roles and assign them to users. Currently it creates a Membership with no role. Update to:

- Create all 4 default roles on the demo tenant
- Assign the demo user the Admin role
- The role-permission relationship should be clear in the demo data

---

## 9. Implementation Order

| Step | What | Files | Est. |
|------|------|-------|------|
| 1 | Create `PermissionRegistry` in `apps/core/permission_registry.py` | New file | 30 min |
| 2 | Create `role_defaults.py` with default role templates | New file | 15 min |
| 3 | Add `inherits_from` FK to Role, generate migration | `teams/models.py`, new migration | 15 min |
| 4 | Add `membership`, `role`, `permissions`, `has_permission` to User model | `accounts/models.py` | 30 min |
| 5 | Add `RolePermission` class + `resolve_permissions` helper | `core/permissions.py` | 30 min |
| 6 | Update `SignupSerializer` to create all default roles with inheritance | `accounts/serializers.py` | 30 min |
| 7 | Update `seed_demo.py` to create default roles | `seed_demo.py` | 15 min |
| 8 | Add `memberships/me/` endpoint + permission registry endpoint | `teams/views.py`, `teams/urls.py` | 45 min |
| 9 | Add role management endpoints (require `manage_roles`) | `teams/views.py` | 30 min |
| 10 | Gate existing ViewSets with `RolePermission` | All `views.py` files across apps | 2 hrs |
| 11 | Add `useRole` hook + `RoleGate` component + auth store updates | Frontend: 3 files | 1 hr |
| 12 | Build Users page with invite flow, role editor, member list | Frontend: new page + tests | 3 hrs |
| 13 | Gate frontend UI elements across existing pages | Various page components | 2 hrs |
| 14 | Tests: backend permission checks | `tests/` | 2 hrs |

**Total estimate:** ~12 hours engineering time.

**Parallelism:** Steps 1-4 (backend core) can run in parallel with step 11 (frontend hook). Steps 5-7 depend on 1-4. Steps 8-9 depend on 1-5. Step 10 is the largest — can be parallelized across team members by app.

---

## 10. Acceptance Criteria

### Backend

1. [ ] `PermissionRegistry` enumerates all permission keys with labels, descriptions, and groups
2. [ ] `Role.resolved_permissions` merges inherited permissions correctly
3. [ ] `User.has_permission(key)` returns True/false based on role's resolved permissions
4. [ ] `is_admin` users bypass all permission checks (except tenant-scoping)
5. [ ] `RolePermission` denies requests when the required permission is not present
6. [ ] All default ViewSets are gated: contacts, deals, pipelines, activities, email, notes, files, reports
7. [ ] `GET /api/teams/memberships/me/` returns current user's role, is_admin, and full permissions dict
8. [ ] `PATCH /api/teams/memberships/{id}/` updates role assignment (requires `manage_roles`)
9. [ ] `GET /api/teams/permissions/` returns the permission registry
10. [ ] `SignupSerializer` creates all 4 default roles with correct inheritance
11. [ ] Existing tests still pass
12. [ ] New tests cover: admin bypass, viewer denial, manager can edit but not delete (if configured), role inheritance, permission registry endpoint

### Frontend

13. [ ] `useRole()` hook returns correct `hasPermission`, `hasAnyPermission`, `hasAllPermissions`
14. [ ] `<RoleGate permission="...">` conditionally renders children
15. [ ] Auth store fetches membership after login
16. [ ] Users page lists all members with role dropdown (admin+ only)
17. [ ] Invite form works (admin+ only)
18. [ ] Role creation modal shows permission checkboxes from registry
19. [ ] UI elements across existing pages are gated (e.g. "New Deal" button hidden for viewers)
20. [ ] Viewer cannot see "New Deal" button or access `/deals/new` route
21. [ ] Admin can see and do everything

### Security

22. [ ] `RolePermission` cannot be bypassed by manipulating request parameters
23. [ ] Non-authenticated users receive 401 (not 403) from `TenantAwarePermission`
24. [ ] Users from different tenants cannot access each other's membership data
25. [ ] Deleting a role with active memberships either blocks or reassigns those members

---

## 11. Open Questions / Spike Items

1. **Role inheritance depth.** Is single-level inheritance (Manager -> Sales Rep) enough, or do we need multi-level (Director -> Manager -> Sales Rep)? Current design supports arbitrary depth via recursive `resolved_permissions`, but the UI only shows one level. This is fine for P3.

2. **Caching.** `cached_property` on `User` is per-request, which is fine. If permission checks become a bottleneck (unlikely — it's a dict lookup), add a short-lived cache (30s TTL) on the membership query. Spike not needed yet.

3. **Django admin.** Should Django admin (at `/admin/`) use the same RBAC system? Currently only Django superusers can access it. For P3, we leave `/admin/` as-is (superuser-only). A future P4 can add tenant-scoped admin access.

4. **Export view permissions.** The export system has its own permission logic. Need to verify it integrates with `RolePermission` rather than bypassing it. Initial review of `export/views.py` suggests it uses custom own permissions.

5. **Role editing audit trail.** Should role/permission changes be logged? The `Activity` model could capture these. Not part of P3 — create a separate ticket.

6. **Bulk role change.** Should an admin be able to change multiple users' roles at once (e.g. promote a team to Manager)? Not in P3 scope.

7. **Frontend loading state.** The `useRole()` hook depends on an async API call. What does the UI show before membership data arrives? Default to most restrictive (no actions visible) until loaded.