from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EmailTemplateViewSet, EmailViewSet, template_variables

router = DefaultRouter()
router.register("", EmailViewSet)

template_router = DefaultRouter()
template_router.register("email-templates", EmailTemplateViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("email-templates/variables/", template_variables, name="template-variables"),
    path("", include(template_router.urls)),
]