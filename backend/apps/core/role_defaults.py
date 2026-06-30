"""
Default role templates for tenant creation.

Each tenant gets these four roles at signup.
"""

from __future__ import annotations

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