from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FileUploadViewSet

router = DefaultRouter()
router.register("", FileUploadViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
