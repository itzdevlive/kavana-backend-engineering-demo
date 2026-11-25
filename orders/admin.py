from django.contrib import admin
from .models import Order, WebhookEvent
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_email", "amount_paise", "currency", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("customer_email",)
@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "event_type", "processed_at")
    search_fields = ("event_id",)
