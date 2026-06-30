#!/usr/bin/env python3
"""Patch ReportExportView's permission_classes"""
content = open("backend/apps/reports/views.py").read()

# The issue was early match failure - let me find the exact text
idx = content.find("ReportExportView")
chunk = content[idx:idx+250]
# Find the IsAuthenticated in this chunk
auth_idx = chunk.find("[IsAuthenticated]")
if auth_idx >= 0:
    line_start = chunk.rfind("\n", 0, auth_idx) + 1
    full_line = chunk[line_start:auth_idx + len("[IsAuthenticated]")]
    # Replace just the permission_classes line
    content = content.replace(
        'ReportExportView(APIView):\n    """Export report data as CSV or printable HTML.\n\n    GET /api/reports/export/csv/  \xe2\x80\x94 key-value CSV of dashboard metrics\n    GET /api/reports/export/html/ \xe2\x80\x94 printable HTML page of report data\n    """\n\n    permission_classes = [IsAuthenticated]',
        'ReportExportView(APIView):\n    """Export report data as CSV or printable HTML.\n\n    GET /api/reports/export/csv/  \xe2\x80\x94 key-value CSV of dashboard metrics\n    GET /api/reports/export/html/ \xe2\x80\x94 printable HTML page of report data\n    """\n\n    permission_classes = [TenantAwarePermission, RolePermission]\n    required_permission = "reports.export"',
        1
    )
    open("backend/apps/reports/views.py", "w").write(content)
    print("ReportExportView patched")
else:
    print("ReportExportView already patched")
