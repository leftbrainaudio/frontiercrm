#!/usr/bin/env python3
"""Patch DealExportView in pipelines/export_views.py"""
content = open("backend/apps/pipelines/export_views.py").read()

old = 'class DealExportView(APIView):\n    """Streaming CSV export of deals, respecting tenant scope and filters.\n\n    GET /api/deals/export/csv/?search=&status=open&pipeline=&...\n    """\n\n    permission_classes = [IsAuthenticated]'

new = 'class DealExportView(APIView):\n    """Streaming CSV export of deals, respecting tenant scope and filters.\n\n    GET /api/deals/export/csv/?search=&status=open&pipeline=&...\n    """\n\n    permission_classes = [TenantAwarePermission, RolePermission]\n    required_permission = "deals.export"'

assert content.count(old) == 1, f"Found {content.count(old)} matches"
content = content.replace(old, new, 1)
open("backend/apps/pipelines/export_views.py", "w").write(content)
print("DealExportView patched")

# Also patch the 3 views in export/views.py
content = open("backend/apps/export/views.py").read()

# ExportContactsView
c1 = content.count('class ExportContactsView(APIView):\n    """Streaming CSV export of contacts, respecting tenant scope.\n\n    GET /api/export/contacts/?format=csv\n    """\n\n    permission_classes = [IsAuthenticated]')
if c1 == 1:
    content = content.replace(
        'class ExportContactsView(APIView):\n    """Streaming CSV export of contacts, respecting tenant scope.\n\n    GET /api/export/contacts/?format=csv\n    """\n\n    permission_classes = [IsAuthenticated]',
        'class ExportContactsView(APIView):\n    """Streaming CSV export of contacts, respecting tenant scope.\n\n    GET /api/export/contacts/?format=csv\n    """\n\n    permission_classes = [TenantAwarePermission, RolePermission]\n    required_permission = "contacts.export"',
        1
    )
    print("ExportContactsView patched")
else:
    print(f"ExportContactsView: {c1} matches")

# ExportDealsView
content = content.replace(
    'class ExportDealsView(APIView):\n    """Streaming CSV export of deals, respecting tenant scope and filters.\n\n    GET /api/export/deals/?format=csv\n    """\n\n    permission_classes = [IsAuthenticated]',
    'class ExportDealsView(APIView):\n    """Streaming CSV export of deals, respecting tenant scope and filters.\n\n    GET /api/export/deals/?format=csv\n    """\n\n    permission_classes = [TenantAwarePermission, RolePermission]\n    required_permission = "deals.export"',
    1
)
print("ExportDealsView patched")

# ExportForecastView
content = content.replace(
    'class ExportForecastView(APIView):\n    """Streaming CSV export of forecast data.\n\n    permission_classes = [IsAuthenticated]',
    'class ExportForecastView(APIView):\n    """Streaming CSV export of forecast data.\n\n    permission_classes = [TenantAwarePermission, RolePermission]\n    required_permission = "forecast.view"',
    1
)
print("ExportForecastView patched")

open("backend/apps/export/views.py", "w").write(content)
print("All export views patched")
