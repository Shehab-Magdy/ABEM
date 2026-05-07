from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        \"apartment\",
        \"amount_paid\",
        \"payment_method\",
        \"payment_date\",
        \"balance_before\",
        \"balance_after\",
        \"recorded_by\",
    )
    list_filter = ("payment_method", "payment_date")
    search_fields = ("apartment__unit_number", "apartment__building__name")
