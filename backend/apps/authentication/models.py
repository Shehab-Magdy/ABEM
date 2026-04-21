"""Custom user model with role-based access control."""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    OWNER = "owner", "Owner"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)
    role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.OWNER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Account lockout tracking
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # Forced password change (set after admin resets password)
    must_change_password = models.BooleanField(default=False)

    # Language preference for i18n
    preferred_language = models.CharField(
        max_length=5,
        choices=[("en", "English"), ("ar", "العربية")],
        default="en",
    )

    # Theme preference for UI
    theme_preference = models.CharField(
        max_length=10,
        choices=[("light", "Light"), ("dark", "Dark")],
        default="light",
    )

    # Messaging restrictions (set by admins)
    messaging_blocked = models.BooleanField(default=False)
    individual_messaging_blocked = models.BooleanField(default=False)

    # Notification preferences (JSON flags)
    notification_preferences = models.JSONField(default=dict, blank=True)

    # Track which admin created this user (FE-01 scoping)
    created_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_users',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["email"]), models.Index(fields=["role"])]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
