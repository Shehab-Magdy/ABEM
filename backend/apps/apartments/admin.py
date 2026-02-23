from django.contrib import admin
from .models import Apartment


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ("unit_number", "building", "owner", "unit_type", "status", "balance", "floor")
    list_filter = ("unit_type", "status", "building")
    search_fields = ("unit_number", "building__name", "owner__email")
    readonly_fields = ("balance",)
