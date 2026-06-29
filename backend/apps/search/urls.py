from django.urls import path

from . import views

urlpatterns = [
    path("", views.search_view, name="search"),
    path("health/", views.search_health, name="search-health"),
]
