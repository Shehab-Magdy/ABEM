"""Authentication and user management serializers."""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from .validators import validate_password_complexity

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)
    buildings = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "phone", "profile_picture", "role", "is_active",
            "must_change_password", "preferred_language",
            "messaging_blocked", "individual_messaging_blocked",
            "created_at", "updated_at", "buildings",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_buildings(self, obj):
        """Return building UUIDs where user is a co-admin."""
        from apps.buildings.models import BuildingCoAdmin
        return list(
            BuildingCoAdmin.objects.filter(user=obj).values_list("building_id", flat=True)
        )


class RegisterUserSerializer(serializers.ModelSerializer):
    """Used by Admin to create new users."""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password_complexity],
    )
    buildings = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "role", "password", "buildings"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return value.lower()

    def validate(self, data):
        role = data.get("role", "owner")
        buildings = data.get("buildings")
        if role == "admin" and buildings is not None and len(buildings) == 0:
            raise serializers.ValidationError(
                {"buildings": _("At least one building must be assigned to an admin user.")}
            )
        # Validate that all building UUIDs belong to buildings the requesting admin manages
        if buildings:
            from apps.buildings.models import Building
            request = self.context.get("request")
            if request:
                managed_ids = set(
                    Building.objects.filter(
                        Q(admin=request.user) | Q(co_admins=request.user)
                    ).values_list("id", flat=True)
                )
                provided_ids = set(buildings)
                invalid = provided_ids - managed_ids
                if invalid:
                    raise serializers.ValidationError(
                        {"buildings": _("You do not manage all selected buildings.")}
                    )
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        buildings = validated_data.pop("buildings", [])
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if buildings and user.role == "admin":
            from apps.buildings.models import Building, BuildingCoAdmin, UserBuilding
            from apps.audit.mixins import log_action

            building_objs = Building.objects.filter(id__in=buildings)
            for building in building_objs:
                BuildingCoAdmin.objects.get_or_create(user=user, building=building)
                UserBuilding.objects.get_or_create(user=user, building=building)

            request = self.context.get("request")
            if request:
                log_action(
                    user=request.user,
                    action="user.buildings_assigned",
                    entity="user",
                    entity_id=user.id,
                    changes={"buildings": {"before": [], "after": [str(b) for b in buildings]}},
                    request=request,
                )

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Admin can update profile fields and role."""

    buildings = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "role", "buildings"]

    def validate(self, data):
        # Determine final role: use incoming value or fall back to the instance's current role
        role = data.get("role", self.instance.role if self.instance else "owner")
        buildings = data.get("buildings")
        if role == "admin" and buildings is not None and len(buildings) == 0:
            raise serializers.ValidationError(
                {"buildings": _("At least one building must be assigned to an admin user.")}
            )
        # Validate that all building UUIDs belong to buildings the requesting admin manages
        if buildings:
            from apps.buildings.models import Building
            request = self.context.get("request")
            if request:
                managed_ids = set(
                    Building.objects.filter(
                        Q(admin=request.user) | Q(co_admins=request.user)
                    ).values_list("id", flat=True)
                )
                provided_ids = set(buildings)
                invalid = provided_ids - managed_ids
                if invalid:
                    raise serializers.ValidationError(
                        {"buildings": _("You do not manage all selected buildings.")}
                    )
        return data

    def update(self, instance, validated_data):
        buildings = validated_data.pop("buildings", None)
        instance = super().update(instance, validated_data)

        if buildings is not None and instance.role == "admin":
            from apps.buildings.models import Building, BuildingCoAdmin, UserBuilding
            from apps.audit.mixins import log_action

            # Get current building IDs for this co-admin
            old_ids = set(
                BuildingCoAdmin.objects.filter(user=instance).values_list("building_id", flat=True)
            )
            new_ids = set(buildings)

            to_add = new_ids - old_ids
            to_remove = old_ids - new_ids

            for bid in to_add:
                BuildingCoAdmin.objects.get_or_create(user=instance, building_id=bid)
                UserBuilding.objects.get_or_create(user=instance, building_id=bid)

            if to_remove:
                BuildingCoAdmin.objects.filter(user=instance, building_id__in=to_remove).delete()
                # Also remove UserBuilding entries for removed buildings
                UserBuilding.objects.filter(user=instance, building_id__in=to_remove).delete()

            request = self.context.get("request")
            if request and (to_add or to_remove):
                log_action(
                    user=request.user,
                    action="user.buildings_assigned",
                    entity="user",
                    entity_id=instance.id,
                    changes={
                        "buildings": {
                            "before": [str(b) for b in old_ids],
                            "after": [str(b) for b in new_ids],
                        }
                    },
                    request=request,
                )
        elif buildings is not None and instance.role == "owner":
            # If switching to owner role, remove all co-admin entries
            from apps.buildings.models import BuildingCoAdmin
            BuildingCoAdmin.objects.filter(user=instance).delete()

        return instance


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Users can update their own profile (no role change)."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "profile_picture", "preferred_language"]


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
        fields = ["id", "email", "first_name", "last_name", "phone", "role", "password", "confirm_password", "preferred_language"]
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
