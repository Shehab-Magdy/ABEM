from django.contrib import admin

from .models import BuildingPlan, Plan, PlanPayment, PlatformSettings

admin.site.register(Plan)
admin.site.register(PlatformSettings)
admin.site.register(BuildingPlan)
admin.site.register(PlanPayment)
