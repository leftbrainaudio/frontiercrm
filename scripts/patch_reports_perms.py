#!/usr/bin/env python3
"""Patch remaining IsAuthenticated -> RolePermission in reports/views.py"""
content = open("backend/apps/reports/views.py").read()

# ForecastView
content = content.replace(
    '    GET /api/reports/forecast/\n      ?pipeline_id=<uuid>\n      &quarter=2026-Q3\n      &range=quarter|half-year|year\n      &scenario_stage=Negotiation\n      &scenario_close_rate=0.80\n      &confidence_level=conservative|medium|optimistic\n    """\n\n    permission_classes = [IsAuthenticated]',
    '    GET /api/reports/forecast/\n      ?pipeline_id=<uuid>\n      &quarter=2026-Q3\n      &range=quarter|half-year|year\n      &scenario_stage=Negotiation\n      &scenario_close_rate=0.80\n      &confidence_level=conservative|medium|optimistic\n    """\n\n    permission_classes = [TenantAwarePermission, RolePermission]\n    required_permission = "forecast.view"',
    1
)

# StaleDealsView
content = content.replace(
    '    GET /api/reports/stale-deals/\n      ?days_since_activity=14\n      &past_close_date=true\n      &limit=20\n    """\n\n    permission_classes = [IsAuthenticated]',
    '    GET /api/reports/stale-deals/\n      ?days_since_activity=14\n      &past_close_date=true\n      &limit=20\n    """\n\n    permission_classes = [TenantAwarePermission, RolePermission]\n    required_permission = "reports.view"',
    1
)

# ReportExportView
content = content.replace(
    'GET /api/reports/export/html/ \xe2\x80\x94 printable HTML page of report data\n    """\n\n    permission_classes = [IsAuthenticated]',
    'GET /api/reports/export/html/ \xe2\x80\x94 printable HTML page of report data\n    """\n\n    permission_classes = [TenantAwarePermission, RolePermission]\n    required_permission = "reports.export"',
    1
)

open("backend/apps/reports/views.py", "w").write(content)
print("OK - 3 views patched")
