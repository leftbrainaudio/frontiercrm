"""URL configuration for reports app."""

from __future__ import annotations

from django.urls import path

from .views import DashboardReportView, StaleDealsView

urlpatterns = [
    path("dashboard/", DashboardReportView.as_view(), name="reports-dashboard"),
    path("stale-deals/", StaleDealsView.as_view(), name="reports-stale-deals"),
]