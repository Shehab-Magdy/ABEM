"""Apartment / unit models."""
import secrets
import string
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.buildings.models import Building


class UnitType(models.TextChoices):
    APARTMENT = "apartment", _("Apartment")
    STORE = "store", _("Store")


class ApartmentStatus(models.TextChoices):
    OCCUPIED = "occupied", _("Occupied")
    VACANT = "vacant", _("Vacant")
    MAINTENANCE = "maintenance", _("Under Maintenance")


class Apartment(models.Model):
    objects: models.Manager["Apartment"]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="apartments")
    # Primary owner (kept for backward compatibility and single-owner fast queries)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_apartments",
    )
    # Multiple owners support — all owners including the primary one
    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="co_owned_apartments",
        blank=True,
    )

    # A paused unit (e.g. vacant or under renovation) is skipped by monthly subscription billing
    billing_paused = models.BooleanField(default=False)
    billing_pause_reason = models.CharField(max_length=200, blank=True)

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


class UnitInvitation(models.Model):
    """One-time invite token linking an email to a specific unit."""
    objects: models.Manager["UnitInvitation"]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name="invitations")
    invited_email = models.EmailField(blank=True)
    # What the person becomes in the unit: its owner, or a renter linked by the owner/admin
    invited_role = models.CharField(max_length=10, choices=[("owner", "Owner"), ("renter", "Renter")], default="owner")
    registration_code = models.CharField(max_length=8, unique=True, editable=False)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["token"]), models.Index(fields=["apartment"])]

    def __str__(self):
        return f"Invite {self.invited_email} → {self.apartment}"

    def save(self, *args, **kwargs):
        if not self.registration_code:
            while True:
                code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
                if not UnitInvitation.objects.filter(registration_code=code).exists():
                    self.registration_code = code
                    break
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()


class ClaimStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class UnitClaimRequest(models.Model):
    """A resident asks to become the owner of a unit; the building's admin approves or rejects."""
    objects: models.Manager["UnitClaimRequest"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name="claim_requests")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="unit_claim_requests")
    status = models.CharField(max_length=10, choices=ClaimStatus.choices, default=ClaimStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["apartment", "user"],
                condition=models.Q(status="pending"),
                name="one_pending_claim_per_user_and_unit",
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.apartment} ({self.status})"
