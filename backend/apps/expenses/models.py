"""Expense domain models – category, expense, split, recurring config, media."""
import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.buildings.models import Building
from apps.apartments.models import Apartment


class ExpenseCategory(models.Model):
    """Configurable expense categories per building."""
    objects: models.Manager["ExpenseCategory"]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="expense_categories")
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=100, blank=True, default="category",
                            help_text=_("Material icon name (used by web and mobile)"))
    color = models.CharField(max_length=7, blank=True, default="#2563EB",
                             help_text=_("Hex color for the category badge"))
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("building", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.building.name} – {self.name}"


class SplitType(models.TextChoices):
    EQUAL_ALL = "equal_all", _("Equal – All Units")
    EQUAL_APARTMENTS = "equal_apartments", _("Equal – Apartments Only")
    EQUAL_STORES = "equal_stores", _("Equal – Stores Only")
    CUSTOM = "custom", _("Custom Subset")


class RecurringFrequency(models.TextChoices):
    MONTHLY = "monthly", _("Monthly")
    QUARTERLY = "quarterly", _("Quarterly")
    ANNUAL = "annual", _("Annual")


class ExpenseKind(models.TextChoices):
    COST = "cost", _("Cost")                  # money the building spent; counts against the treasury
    SUBSCRIPTION = "subscription", _("Monthly subscription")  # a charge to units; money comes in as payments
    LATE_FEE = "late_fee", _("Late fee")      # a charge to one unit


class Expense(models.Model):
    objects: models.Manager["Expense"]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="expenses")
    category = models.ForeignKey(
        ExpenseCategory, on_delete=models.PROTECT, related_name="expenses"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)

    # Only "cost" rows are money the building spent. Subscriptions and late fees are charges to units,
    # so treasury, statement and dashboard totals leave them out.
    kind = models.CharField(max_length=12, choices=ExpenseKind.choices, default=ExpenseKind.COST)
    split_type = models.CharField(max_length=20, choices=SplitType.choices, default=SplitType.EQUAL_ALL)
    is_recurring = models.BooleanField(default=False)
    is_manually_paid = models.BooleanField(default=False)

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_expenses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-expense_date"]
        indexes = [
            models.Index(fields=["building"]),
            models.Index(fields=["expense_date"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.building.name}) – {self.amount}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class RecurringConfig(models.Model):
    """Recurring schedule for an expense."""
    objects: models.Manager["RecurringConfig"]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense = models.OneToOneField(Expense, on_delete=models.CASCADE, related_name="recurring_config")
    frequency = models.CharField(max_length=10, choices=RecurringFrequency.choices)
    next_due = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.expense.title} – {self.frequency}"


class ApartmentExpense(models.Model):
    """Individual share of an expense assigned to one apartment."""
    objects: models.Manager["ApartmentExpense"]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name="apartment_expenses")
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="apartment_expenses")
    share_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("apartment", "expense")
        indexes = [
            models.Index(fields=["apartment"]),
            models.Index(fields=["expense"]),
        ]

    def __str__(self):
        return f"{self.apartment} | {self.expense.title} | {self.share_amount}"


class MediaFile(models.Model):
    """Central registry for bill images and other media."""
    objects: models.Manager["MediaFile"]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Polymorphic: entity_type = 'expense', entity_id = expense UUID
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    url = models.URLField(max_length=500)
    mime_type = models.CharField(max_length=50)
    file_size_bytes = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_files",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["entity_type", "entity_id"])]

    def __str__(self):
        return f"{self.entity_type}:{self.entity_id} – {self.mime_type}"


class SubscriptionPlan(models.Model):
    """The fixed monthly amount each unit of a building pays (الاشتراك الشهري)."""
    objects: models.Manager["SubscriptionPlan"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.OneToOneField(Building, on_delete=models.CASCADE, related_name="subscription_plan")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_day = models.PositiveSmallIntegerField(default=1, help_text="Day of the month units are billed (1-28)")
    due_days = models.PositiveSmallIntegerField(default=10, help_text="Days after billing that payment is due")
    starts_on = models.DateField(help_text="First month to bill")
    is_active = models.BooleanField(default=True)
    # Optional late fee, added once to a subscription share that is still unpaid after due date + grace days
    late_fee_type = models.CharField(
        max_length=8, choices=[("none", "None"), ("fixed", "Fixed amount"), ("percent", "Percent of what is owed")], default="none"
    )
    late_fee_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    grace_days = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.building.name}: {self.amount}/month"


class SubscriptionRun(models.Model):
    """One billed month of a plan; the unique constraint makes billing safe to repeat."""
    objects: models.Manager["SubscriptionRun"]

    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name="runs")
    month = models.DateField(help_text="First day of the month billed")
    expense = models.OneToOneField(Expense, on_delete=models.CASCADE, related_name="subscription_run")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["plan", "month"], name="one_run_per_plan_and_month")]


class LateFee(models.Model):
    """A late fee charged on one overdue subscription share; an admin may waive it with a reason."""
    objects: models.Manager["LateFee"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    share = models.OneToOneField(ApartmentExpense, on_delete=models.CASCADE, related_name="late_fee")
    expense = models.OneToOneField(Expense, on_delete=models.CASCADE, related_name="late_fee_record")
    waived_at = models.DateTimeField(null=True, blank=True)
    waived_reason = models.CharField(max_length=200, blank=True)
    waived_by = models.ForeignKey("authentication.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
