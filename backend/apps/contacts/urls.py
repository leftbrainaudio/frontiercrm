from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, ContactViewSet

router = DefaultRouter()
router.register("accounts", AccountViewSet)
router.register("contacts", ContactViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
