from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MembershipViewSet, RoleViewSet, TeamViewSet, TenantViewSet

router = DefaultRouter()
router.register("tenants", TenantViewSet)
router.register("teams", TeamViewSet)
router.register("roles", RoleViewSet)
router.register("memberships", MembershipViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
