"""Building and related domain models."""
import uuid
from django.db import models
from django.conf import settings


class Building(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # tenant_id IS the building UUID (each building is a tenant)
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    num_floors = models.PositiveSmallIntegerField(default=1)
    num_apartments = models.PositiveSmallIntegerField(default=0)
    num_stores = models.PositiveSmallIntegerField(default=0)
    photo = models.ImageField(upload_to="buildings/photos/", null=True, blank=True)

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="administered_buildings",
    )
    # Many-to-many: which users can access this building
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="UserBuilding",
        related_name="buildings",
        blank=True,
    )
    # Multiple admins support — co-admins in addition to the primary admin FK
    co_admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="BuildingCoAdmin",
        related_name="co_administered_buildings",
        blank=True,
    )

    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["admin"])]

    def __str__(self):
        return self.name


class UserBuilding(models.Model):
    """Explicit junction table for User ↔ Building M2M."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "building")
        verbose_name = "User Building Access"


class BuildingCoAdmin(models.Model):
    """Explicit junction table for additional building admins."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "building")
        verbose_name = "Building Co-Admin"
