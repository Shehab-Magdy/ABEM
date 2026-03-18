"""Payment / ledger models."""
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.apartments.models import Apartment
from apps.expenses.models import Expense


class PaymentMethod(models.TextChoices):
    CASH = "cash", _("Cash")
    BANK_TRANSFER = "bank_transfer", _("Bank Transfer")
    CHEQUE = "cheque", _("Cheque")
    OTHER = "other", _("Other")


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name="payments")
    expenses = models.ManyToManyField(Expense, blank=True, related_name="payments")

    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    payment_date = models.DateField()
    notes = models.TextField(blank=True)

    # Balance snapshot at the time of recording
    balance_before = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    balance_after = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    recorded_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="recorded_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-payment_date", "-created_at"]
        indexes = [
            models.Index(fields=["apartment"]),
            models.Index(fields=["payment_date"]),
        ]

    def __str__(self):
        return f"{self.apartment} | {self.amount_paid} on {self.payment_date}"


class AssetType(models.TextChoices):
    VEHICLE = "vehicle", _("Vehicle")
    EQUIPMENT = "equipment", _("Equipment")
    FURNITURE = "furniture", _("Furniture")
    ELECTRONICS = "electronics", _("Electronics")
    PROPERTY = "property", _("Property")
    OTHER = "other", _("Other")


class BuildingAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(
        "buildings.Building", on_delete=models.CASCADE, related_name="assets"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    asset_type = models.CharField(max_length=20, choices=AssetType.choices, default=AssetType.OTHER)
    acquisition_date = models.DateField(null=True, blank=True)
    acquisition_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_sold = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_assets"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.building.name} – {self.name}"


class AssetSale(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.OneToOneField(BuildingAsset, on_delete=models.CASCADE, related_name="sale")
    sale_date = models.DateField()
    sale_price = models.DecimalField(max_digits=12, decimal_places=2)
    buyer_name = models.CharField(max_length=255, blank=True)
    buyer_contact = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="recorded_sales"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sale_date"]

    def __str__(self):
        return f"Sale of {self.asset.name} – {self.sale_price}"
