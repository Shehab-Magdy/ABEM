"""Authentication and user management serializers."""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .validators import validate_password_complexity

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "phone", "profile_picture", "role", "is_active",
            "must_change_password",
            "messaging_blocked", "individual_messaging_blocked",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class RegisterUserSerializer(serializers.ModelSerializer):
    """Used by Admin to create new users."""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password_complexity],
    )

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "role", "password"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return value.lower()

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Admin can update profile fields and role."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "role"]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Users can update their own profile (no role change)."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "profile_picture"]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password_complexity],
    )
    confirm_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": _("New passwords do not match.")}
            )
        return data


class SelfRegisterSerializer(serializers.ModelSerializer):
    """Public self-registration — caller chooses role (admin or owner)."""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password_complexity],
    )
    confirm_password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["admin", "owner"], default="owner")

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "role", "password", "confirm_password"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return value.lower()

    def validate(self, data):
        if data["password"] != data.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": _("Passwords do not match.")})
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ForceChangePasswordSerializer(serializers.Serializer):
    """Used when must_change_password is True — no current password required."""

    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password_complexity],
    )
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": _("New passwords do not match.")}
            )
        return data


class AdminResetPasswordSerializer(serializers.Serializer):
    """Admin-initiated password reset — no current password required."""

    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password_complexity],
    )
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": _("Passwords do not match.")}
            )
        return data
