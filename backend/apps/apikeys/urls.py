"""URL configuration for the API Keys app."""

from django.urls import path

from . import views

urlpatterns = [
    path("api-keys/", views.APIKeyListCreateView.as_view(), name="apikeys-list-create"),
    path("api-keys/<uuid:pk>/", views.APIKeyDetailView.as_view(), name="apikeys-detail"),
    path("api-keys/<uuid:pk>/revoke/", views.APIKeyRevokeView.as_view(), name="apikeys-revoke"),
]
