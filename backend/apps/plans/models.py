"""Plans and pricing for 3maracom itself (R-14) and the manual InstaPay billing flow (R-15)."""
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

FEATURES = ("annual_report", "subscriptions")  # what a plan can switch on; units are limited by max_units


class Plan(models.Model):
    """A tier a building can be on. Prices and limits are data, edited by the platform owners."""
    objects: models.Manager["Plan"]

    code = models.SlugField(primary_key=True, max_length=20)
    name_ar = models.CharField(max_length=60)
    name_en = models.CharField(max_length=60)
    price_monthly = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    max_units = models.PositiveIntegerField(null=True, blank=True, help_text=_("Empty = unlimited"))
    features = models.JSONField(default=list, blank=True, help_text=_("Any of: annual_report, subscriptions"))
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "price_monthly"]

    def __str__(self):
        return self.name_en


class PlatformSettings(models.Model):
    """One row: where buildings send the money for their plan."""
    objects: models.Manager["PlatformSettings"]

    instapay_address = models.CharField(max_length=120, blank=True)
    trial_days = models.PositiveSmallIntegerField(default=14)

    class Meta:
        verbose_name_plural = "Platform settings"

    @classmethod
    def load(cls):
        return cls.objects.first() or cls.objects.create()


class BuildingPlan(models.Model):
    """Which plan a building is on and until when it is paid. No row = free (or the trial, for new buildings)."""
    objects: models.Manager["BuildingPlan"]

    building = models.OneToOneField("buildings.Building", on_delete=models.CASCADE, related_name="plan_subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="+")
    paid_until = models.DateField()


class PeriodChoices(models.TextChoices):
    MONTHLY = "monthly", _("Monthly")
    YEARLY = "yearly", _("Yearly")


class PlanPaymentStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    CONFIRMED = "confirmed", _("Confirmed")
    REJECTED = "rejected", _("Rejected")


class PlanPayment(models.Model):
    """A building admin says they paid for a plan by InstaPay; a platform owner confirms it."""
    objects: models.Manager["PlanPayment"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey("buildings.Building", on_delete=models.CASCADE, related_name="plan_payments")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="+")
    period = models.CharField(max_length=8, choices=PeriodChoices.choices)
    amount = models.DecimalField(max_digits=9, decimal_places=2, help_text=_("The price when it was requested"))
    reference = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=PlanPaymentStatus.choices, default=PlanPaymentStatus.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
