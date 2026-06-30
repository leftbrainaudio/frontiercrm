from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DealViewSet, PipelineViewSet, StageViewSet

from .export_views import DealExportView

router = DefaultRouter()
router.register("pipelines", PipelineViewSet)
router.register("stages", StageViewSet)
router.register("deals", DealViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # Export endpoints
    path("export/csv/", DealExportView.as_view(), name="deal-export-csv"),
]
