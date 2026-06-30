from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MembershipViewSet, PermissionViewSet, RoleViewSet, TeamViewSet, TenantViewSet

router = DefaultRouter()
router.register("tenants", TenantViewSet)
router.register("teams", TeamViewSet)
router.register("roles", RoleViewSet)
router.register("memberships", MembershipViewSet)
router.register("permissions", PermissionViewSet, basename="permissions")

urlpatterns = [
    path("", include(router.urls)),
]