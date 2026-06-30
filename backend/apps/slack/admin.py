"""Django admin registration for SlackWebhook."""

from django.contrib import admin

from apps.slack.models import SlackWebhook


@admin.register(SlackWebhook)
class SlackWebhookAdmin(admin.ModelAdmin):
    list_display = ("display_name", "tenant_id", "is_active", "failure_count", "last_triggered_at")
    list_filter = ("is_active", "tenant_id")
    search_fields = ("display_name", "webhook_url")