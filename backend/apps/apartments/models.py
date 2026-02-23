"""Apartment / unit models."""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.buildings.models import Building


class UnitType(models.TextChoices):
    APARTMENT = "apartment", "Apartment"
    STORE = "store", "Store"


class ApartmentStatus(models.TextChoices):
    OCCUPIED = "occupied", "Occupied"
    VACANT = "vacant", "Vacant"
    MAINTENANCE = "maintenance", "Under Maintenance"


class Apartment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="apartments")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_apartments",
    )

    unit_number = models.CharField(max_length=20)
    floor = models.SmallIntegerField(default=0)
    unit_type = models.CharField(max_length=15, choices=UnitType.choices, default=UnitType.APARTMENT)
    size_sqm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=15, choices=ApartmentStatus.choices, default=ApartmentStatus.OCCUPIED)

    # Running balance: positive = owes money, negative = credit
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("building", "unit_number")
        ordering = ["building", "floor", "unit_number"]
        indexes = [
            models.Index(fields=["building"]),
            models.Index(fields=["owner"]),
        ]

    def __str__(self):
        return f"{self.building.name} – Unit {self.unit_number}"
