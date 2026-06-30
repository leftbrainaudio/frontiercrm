"""
Canonical permission registry for role-based access control.

Every permission in the system is defined here as a PermissionDef.
The UI uses this to render checkboxes; the backend uses it for
is_admin short-circuit and validation.
"""

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