#!/usr/bin/env python3
"""Check what's around ReportExportView"""
content = open("backend/apps/reports/views.py").read()
idx = content.find("ReportExportView")
print(repr(content[idx:idx+200]))