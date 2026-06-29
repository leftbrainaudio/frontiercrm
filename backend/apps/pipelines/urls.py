from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DealViewSet, PipelineViewSet, StageViewSet

router = DefaultRouter()
router.register("pipelines", PipelineViewSet)
router.register("stages", StageViewSet)
router.register("deals", DealViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
