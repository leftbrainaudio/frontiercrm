from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ActivityViewSet, TimelineView

router = DefaultRouter()
router.register("", ActivityViewSet)

urlpatterns = [
    path("timeline/", TimelineView.as_view(), name="activity-timeline"),
    path("", include(router.urls)),
]
