"""API URL routing for core models."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views_api import CustomFieldDefViewSet

router = DefaultRouter()
router.register(r"custom-fields", CustomFieldDefViewSet, basename="custom-field")

urlpatterns = [
    path("", include(router.urls)),
]
