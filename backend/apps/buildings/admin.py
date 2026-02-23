from django.contrib import admin
from .models import Building, UserBuilding


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "city", "admin", "num_floors", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "address", "city")


@admin.register(UserBuilding)
class UserBuildingAdmin(admin.ModelAdmin):
    list_display = ("user", "building", "joined_at")
