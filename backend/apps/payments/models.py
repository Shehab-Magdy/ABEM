"""Payment / ledger models."""
import uuid
from decimal import Decimal
from django.db import models
from apps.apartments.models import Apartment
from apps.expenses.models import Expense


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    CHEQUE = "cheque", "Cheque"
    OTHER = "other", "Other"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name="payments")
    expense = models.ForeignKey(
        Expense, on_delete=models.CASCADE, related_name="payments", null=True, blank=True
    )

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
            models.Index(fields=["expense"]),
            models.Index(fields=["payment_date"]),
        ]

    def __str__(self):
        return f"{self.apartment} | {self.amount_paid} on {self.payment_date}"
