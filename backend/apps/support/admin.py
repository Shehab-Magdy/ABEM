from django.contrib import admin

from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "status", "page", "message")
    list_filter = ("status",)
    search_fields = ("message", "user__email")
    readonly_fields = ("user", "message", "screenshot", "page", "created_at")
