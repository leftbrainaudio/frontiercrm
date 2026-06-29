"""URL configuration for the imports app."""

from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("", views.ImportViewSet.as_view({"get": "list"}), name="import-list"),
    path(
        "<uuid:pk>/",
        views.ImportViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="import-detail",
    ),
    path(
        "<uuid:pk>/confirm/",
        views.ImportViewSet.as_view({"post": "confirm"}),
        name="import-confirm",
    ),
    path(
        "<str:entity_type_raw>/preview/",
        views.ImportViewSet.as_view({"post": "preview"}),
        name="import-preview",
    ),
]