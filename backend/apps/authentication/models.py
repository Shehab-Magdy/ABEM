"""Custom user model with role-based access control."""

import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    OWNER = "owner", "Owner"
    # Lives in a unit without owning it. ("renter", not "tenant": in this code a tenant is a building.)
    RENTER = "renter", "Renter"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Create a user for OTP/Google-only authentication by default.

        Most accounts never have a usable password — they sign in via email OTP
        or Google. Only pass `password` when a real password is required (the
        `create_superuser` path, kept for Django admin login).
        """
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        if not password:
            raise ValueError(
                "Superusers must have a password (used for /admin/ login)."
            )
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
    # When the user accepted the Terms of Service and Privacy Policy (set at self sign-up)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True
    )
    role = models.CharField(
        max_length=10, choices=UserRole.choices, default=UserRole.OWNER
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Language preference for i18n
    preferred_language = models.CharField(
        max_length=5,
        choices=[("en", "English"), ("ar", "العربية")],
        default="en",
    )

    # Colour theme preference, synced across devices
    preferred_theme = models.CharField(
        max_length=6,
        choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")],
        default="system",
    )

    # Messaging restrictions (set by admins)
    messaging_blocked = models.BooleanField(default=False)
    individual_messaging_blocked = models.BooleanField(default=False)

    # Notification preferences (JSON flags)
    notification_preferences = models.JSONField(default=dict, blank=True)

    # Track which admin created this user (FE-01 scoping)
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
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


class EmailOTP(models.Model):
    """A one-time passcode emailed to a user to sign in, replacing passwords."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_otps")
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Email OTP"
        verbose_name_plural = "Email OTPs"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"OTP for {self.user.email} (expires {self.expires_at})"

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()


class TrustedDevice(models.Model):
    """A device that may bypass the OTP step for a limited time after a successful sign-in."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="trusted_devices"
    )
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Trusted Device"
        verbose_name_plural = "Trusted Devices"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user"])]

    def __str__(self):
        return f"Trusted device for {self.user.email} (expires {self.expires_at})"

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()


class UserSession(models.Model):
    """
    A real signed-in session, for a "your devices" screen - distinct from
    `TrustedDevice` (the OTP-skip-bypass grant) and from simplejwt's
    OutstandingToken/BlacklistedToken (which get a fresh jti on every
    refresh-token rotation, so they can't represent one continuous session
    on their own).

    `session_id` is generated once at login and embedded in the refresh
    token's claims; it stays the same across rotations, while `current_jti`
    is overwritten on every rotation to track which OutstandingToken a
    revoke of this session must blacklist.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    device_label = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    current_jti = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        ordering = ["-last_used_at"]
        indexes = [
            models.Index(fields=["session_id"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"Session for {self.user.email} ({self.device_label})"
