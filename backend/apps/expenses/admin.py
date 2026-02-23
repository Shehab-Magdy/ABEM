from django.contrib import admin
from .models import ExpenseCategory, Expense, RecurringConfig, ApartmentExpense, MediaFile


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "building", "is_active")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "building", "category", "amount", "expense_date", "is_recurring", "deleted_at")
    list_filter = ("building", "category", "is_recurring")
    search_fields = ("title",)


@admin.register(RecurringConfig)
class RecurringConfigAdmin(admin.ModelAdmin):
    list_display = ("expense", "frequency", "next_due", "is_active")


@admin.register(ApartmentExpense)
class ApartmentExpenseAdmin(admin.ModelAdmin):
    list_display = ("apartment", "expense", "share_amount")


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ("entity_type", "entity_id", "mime_type", "file_size_bytes", "uploaded_by")
