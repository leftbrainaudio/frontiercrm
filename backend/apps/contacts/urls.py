from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, ContactViewSet

from .export_views import AccountExportView, ContactExportView

router = DefaultRouter()
router.register("accounts", AccountViewSet)
router.register("contacts", ContactViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # Export endpoints
    path("export/csv/", ContactExportView.as_view(), name="contact-export-csv"),
    path("export/accounts/csv/", AccountExportView.as_view(), name="account-export-csv"),
]
