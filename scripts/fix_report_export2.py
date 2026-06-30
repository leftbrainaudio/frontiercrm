#!/usr/bin/env python3
"""Force-patch ReportExportView's permission_classes"""
content = open("backend/apps/reports/views.py").read()

# Find the exact span for ReportExportView's permission_classes
idx = content.find("class ReportExportView")
# Find next "    permission_classes = [IsAuthenticated]"
search_from = idx
perm_idx = content.find("    permission_classes = [IsAuthenticated]", search_from)
if perm_idx > 0 and perm_idx < idx + 300:
    # Replace this specific occurrence
    before = content[:perm_idx]
    # Check what comes after
    line_end = content.find("\n", perm_idx)
    after = content[line_end:]
    
    new_perms = "    permission_classes = [TenantAwarePermission, RolePermission]\n    required_permission = \"reports.export\""
    
    content = before + new_perms + after
    open("backend/apps/reports/views.py", "w").write(content)
    print(f"Patched ReportExportView at position {perm_idx}")
else:
    print(f"Could not find permission_classes near ReportExportView (idx={idx}, perm_idx={perm_idx})")
    
# Verify
v = open("backend/apps/reports/views.py").read()
if v.find("ReportExportView") > 0:
    snippet = v[v.find("ReportExportView"):v.find("ReportExportView")+300]
    print("After:")
    print(snippet[:200])
