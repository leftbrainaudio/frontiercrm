"""URL configuration for the sync engine."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SyncConnectionViewSet, SyncStateViewSet

router = DefaultRouter()
router.register("connections", SyncConnectionViewSet)
router.register("states", SyncStateViewSet)

urlpatterns = [
    path("", include(router.urls)),
]