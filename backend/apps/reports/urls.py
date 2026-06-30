"""URL configuration for reports app."""

from __future__ import annotations

from django.urls import path

from .export_views import (
    ForecastExportView,
    PipelineReportExportView,
)
from .views import DashboardReportView, ForecastView, ReportExportView, StaleDealsView

urlpatterns = [
    path("dashboard/", DashboardReportView.as_view(), name="reports-dashboard"),
    path("forecast/", ForecastView.as_view(), name="reports-forecast"),
    path("stale-deals/", StaleDealsView.as_view(), name="reports-stale-deals"),
    path("export/pipeline/csv/", PipelineReportExportView.as_view(), name="reports-export-pipeline-csv"),
    path("export/pipeline/html/", ReportExportView.as_view(), name="reports-export-html"),
    path("export/forecast/csv/", ForecastExportView.as_view(), name="reports-export-forecast-csv"),
]
