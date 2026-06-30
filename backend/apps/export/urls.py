"""URL configuration for the export app."""

from django.urls import path

from .views import ExportContactsView, ExportDealsView, ExportPipelineReportView

urlpatterns = [
    path("contacts/", ExportContactsView.as_view(), name="export-contacts"),
    path("deals/", ExportDealsView.as_view(), name="export-deals"),
    path("reports/pipeline/", ExportPipelineReportView.as_view(), name="export-pipeline-report"),
]
