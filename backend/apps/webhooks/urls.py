from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WebhookDeadEventViewSet, WebhookEndpointViewSet, WebhookEventViewSet, webhook_receiver

router = DefaultRouter()
router.register("endpoints", WebhookEndpointViewSet)
router.register("events", WebhookEventViewSet)
router.register("dead-events", WebhookDeadEventViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("receive/", webhook_receiver, name="webhook-receive"),
]