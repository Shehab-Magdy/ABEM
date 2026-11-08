"""Authentication and user management serializers."""

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

User = get_user_model()


class OTPRequestSerializer(serializers.Serializer):
    """POST /auth/otp/request/ {email}."""

    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    """
    POST /auth/otp/verify/ {email, code, accept_terms?}.

    `accept_terms` is only required when `email` has no account yet (a
    brand-new signup via the login page): the view rejects with
    `code: "terms_required"` until it's sent as `true`. It's ignored for an
    existing user's sign-in.
    """

    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    accept_terms = serializers.BooleanField(required=False, default=False)


class GoogleSignInSerializer(serializers.Serializer):
    """
    POST /auth/google/ {id_token, accept_terms?}.

    `accept_terms` is only required when the Google-verified email has no
    account yet; see `OTPVerifySerializer`.
    """

    id_token = serializers.CharField()
    accept_terms = serializers.BooleanField(required=False, default=False)


class UserSessionSerializer(serializers.Serializer):
    """
    GET /auth/sessions/ list item.

    `is_current` is computed against `context["current_session_id"]` (the
    session_id claim decoded from the calling request's own refresh-token
    cookie), not stored on the model.
    """

    id = serializers.IntegerField(read_only=True)
    device_label = serializers.CharField(read_only=True)
    ip_address = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    last_used_at = serializers.DateTimeField(read_only=True)
    is_current = serializers.SerializerMethodField()

    def get_is_current(self, obj):
        current_session_id = self.context.get("current_session_id")
        return bool(current_session_id) and str(obj.session_id) == str(
            current_session_id
        )


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)
    buildings = serializers.SerializerMethodField(read_only=True)
    apartment_ids = serializers.SerializerMethodField(read_only=True)
    is_platform_owner = serializers.BooleanField(source="is_superuser", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "is_platform_owner",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "profile_picture",
            "role",
            "is_active",
            "preferred_language",
            "preferred_theme",
            "notification_preferences",
            "messaging_blocked",
            "individual_messaging_blocked",
            "created_at",
            "updated_at",
            "buildings",
            "apartment_ids",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_buildings(self, obj):
        """Return building UUIDs where user is a co-admin."""
        from apps.buildings.models import BuildingCoAdmin

        return list(
            BuildingCoAdmin.objects.filter(user=obj).values_list(
                "building_id", flat=True
            )
        )

    def get_apartment_ids(self, obj):
        """Return apartment UUIDs where user is an owner (primary or co-owner)."""
        from apps.apartments.models import Apartment

        owned = set(Apartment.objects.filter(owner=obj).values_list("id", flat=True))
        co_owned = set(
            Apartment.objects.filter(owners=obj).values_list("id", flat=True)
        )
        return list(owned | co_owned)


class RegisterUserSerializer(serializers.ModelSerializer):
    """
    Used by Admin to create new users.

    No password: the account is created with set_unusable_password() (see
    UserManager.create_user) and the new user signs in via email OTP or
    Google — the frontend drives them through `otp/request` + `otp/verify`
    right after this call.
    """

    buildings = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
    )
    apartment_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "buildings",
            "apartment_ids",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value.lower()

    def validate(self, data):
        role = data.get("role", "owner")
        buildings = data.get("buildings")
        if role == "admin" and buildings is not None and len(buildings) == 0:
            raise serializers.ValidationError(
                {
                    "buildings": _(
                        "At least one building must be assigned to an admin user."
                    )
                }
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
        # Validate apartment_ids belong to buildings the admin manages
        apartment_ids = data.get("apartment_ids")
        if apartment_ids:
            from apps.apartments.models import Apartment
            from apps.buildings.models import Building

            request = self.context.get("request")
            if request:
                managed_building_ids = set(
                    Building.objects.filter(
                        Q(admin=request.user) | Q(co_admins=request.user)
                    ).values_list("id", flat=True)
                )
                apts = Apartment.objects.filter(id__in=apartment_ids)
                if apts.count() != len(apartment_ids):
                    raise serializers.ValidationError(
                        {"apartment_ids": _("One or more apartments do not exist.")}
                    )
                invalid_apts = apts.exclude(building_id__in=managed_building_ids)
                if invalid_apts.exists():
                    raise serializers.ValidationError(
                        {
                            "apartment_ids": _(
                                "You do not manage the building(s) for all selected apartments."
                            )
                        }
                    )
        return data

    def create(self, validated_data):
        buildings = validated_data.pop("buildings", [])
        apartment_ids = validated_data.pop("apartment_ids", [])
        user = User(**validated_data)
        user.set_unusable_password()
        # Track which admin created this user (FE-01)
        request = self.context.get("request")
        if request:
            user.created_by = request.user
        user.save()

        if buildings and user.role == "admin":
            from apps.audit.mixins import log_action
            from apps.buildings.models import (Building, BuildingCoAdmin,
                                               UserBuilding)

            building_objs = Building.objects.filter(id__in=buildings)
            for building in building_objs:
                BuildingCoAdmin.objects.get_or_create(user=user, building=building)
                UserBuilding.objects.get_or_create(user=user, building=building)

            if request:
                log_action(
                    user=request.user,
                    action="user.buildings_assigned",
                    entity="user",
                    entity_id=user.id,
                    changes={
                        "buildings": {
                            "before": [],
                            "after": [str(b) for b in buildings],
                        }
                    },
                    request=request,
                )

        # Assign owner to apartments (FE-02)
        if apartment_ids and user.role == "owner":
            from apps.apartments.models import Apartment
            from apps.audit.mixins import log_action
            from apps.buildings.models import UserBuilding

            apts = Apartment.objects.filter(id__in=apartment_ids)
            for apt in apts:
                apt.owners.add(user)
                if apt.owner is None:
                    apt.owner = user
                    apt.save(update_fields=["owner"])
                # Ensure user is a member of the building
                UserBuilding.objects.get_or_create(user=user, building=apt.building)

            if request:
                log_action(
                    user=request.user,
                    action="user.apartments_assigned",
                    entity="user",
                    entity_id=user.id,
                    changes={
                        "apartment_ids": {
                            "before": [],
                            "after": [str(a) for a in apartment_ids],
                        }
                    },
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
    apartment_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "role",
            "buildings",
            "apartment_ids",
        ]

    def _get_managed_building_ids(self):
        """Return the set of building IDs managed by the requesting admin."""
        from apps.buildings.models import Building

        request = self.context.get("request")
        if not request:
            return set()
        return set(
            Building.objects.filter(
                Q(admin=request.user) | Q(co_admins=request.user)
            ).values_list("id", flat=True)
        )

    def validate(self, data):
        # Determine final role: use incoming value or fall back to the instance's current role
        role = data.get("role", self.instance.role if self.instance else "owner")
        buildings = data.get("buildings")
        if role == "admin" and buildings is not None and len(buildings) == 0:
            raise serializers.ValidationError(
                {
                    "buildings": _(
                        "At least one building must be assigned to an admin user."
                    )
                }
            )
        # Validate that all building UUIDs belong to buildings the requesting admin manages
        if buildings:
            managed_ids = self._get_managed_building_ids()
            invalid = set(buildings) - managed_ids
            if invalid:
                raise serializers.ValidationError(
                    {"buildings": _("You do not manage all selected buildings.")}
                )
        # Validate apartment_ids belong to buildings the admin manages
        apartment_ids = data.get("apartment_ids")
        if apartment_ids is not None:
            from apps.apartments.models import Apartment

            managed_ids = self._get_managed_building_ids()
            apts = Apartment.objects.filter(id__in=apartment_ids)
            if apts.count() != len(set(apartment_ids)):
                raise serializers.ValidationError(
                    {"apartment_ids": _("One or more apartments do not exist.")}
                )
            invalid_apts = apts.exclude(building_id__in=managed_ids)
            if invalid_apts.exists():
                raise serializers.ValidationError(
                    {
                        "apartment_ids": _(
                            "You do not manage the building(s) for all selected apartments."
                        )
                    }
                )
        return data

    def update(self, instance, validated_data):
        buildings = validated_data.pop("buildings", None)
        apartment_ids = validated_data.pop("apartment_ids", None)
        instance = super().update(instance, validated_data)

        if buildings is not None and instance.role == "admin":
            from apps.audit.mixins import log_action
            from apps.buildings.models import (Building, BuildingCoAdmin,
                                               UserBuilding)

            # Get current building IDs for this co-admin
            old_ids = set(
                BuildingCoAdmin.objects.filter(user=instance).values_list(
                    "building_id", flat=True
                )
            )
            new_ids = set(buildings)

            to_add = new_ids - old_ids
            to_remove = old_ids - new_ids

            for bid in to_add:
                BuildingCoAdmin.objects.get_or_create(user=instance, building_id=bid)
                UserBuilding.objects.get_or_create(user=instance, building_id=bid)

            if to_remove:
                BuildingCoAdmin.objects.filter(
                    user=instance, building_id__in=to_remove
                ).delete()
                # Also remove UserBuilding entries for removed buildings
                UserBuilding.objects.filter(
                    user=instance, building_id__in=to_remove
                ).delete()

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

        # Handle apartment assignment for owners (FE-02)
        if apartment_ids is not None and instance.role == "owner":
            self._sync_owner_apartments(instance, apartment_ids)

        return instance

    def _sync_owner_apartments(self, instance, apartment_ids):
        """Sync the owner's apartment assignments to match the given apartment_ids list."""
        from apps.apartments.models import Apartment
        from apps.audit.mixins import log_action
        from apps.buildings.models import UserBuilding

        new_ids = set(apartment_ids)

        # Current apartments where user is in owners M2M
        old_ids = set(
            Apartment.objects.filter(owners=instance).values_list("id", flat=True)
        )
        # Also include apartments where user is primary owner but not in M2M
        old_primary = set(
            Apartment.objects.filter(owner=instance).values_list("id", flat=True)
        )
        old_ids = old_ids | old_primary

        to_add = new_ids - old_ids
        to_remove = old_ids - new_ids

        # Add user to new apartments
        for apt in Apartment.objects.filter(id__in=to_add):
            apt.owners.add(instance)
            if apt.owner is None:
                apt.owner = instance
                apt.save(update_fields=["owner"])
            UserBuilding.objects.get_or_create(user=instance, building=apt.building)

        # Remove user from old apartments
        for apt in Apartment.objects.filter(id__in=to_remove):
            apt.owners.remove(instance)
            if apt.owner == instance:
                # Reassign primary owner to the next co-owner, or None
                next_owner = apt.owners.first()
                apt.owner = next_owner
                apt.save(update_fields=["owner"])

        request = self.context.get("request")
        if request and (to_add or to_remove):
            log_action(
                user=request.user,
                action="user.apartments_assigned",
                entity="user",
                entity_id=instance.id,
                changes={
                    "apartment_ids": {
                        "before": [str(a) for a in old_ids],
                        "after": [str(a) for a in new_ids],
                    }
                },
                request=request,
            )


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Users can update their own profile (no role change)."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "profile_picture",
            "preferred_language",
            "preferred_theme",
            "notification_preferences",
        ]

    def validate_notification_preferences(self, value):
        """Only the known switches, each on or off; anything not listed stays on."""
        from apps.notifications.services import PREFERENCE_KEYS

        if not isinstance(value, dict) or any(
            k not in PREFERENCE_KEYS or not isinstance(v, bool)
            for k, v in value.items()
        ):
            raise serializers.ValidationError(
                _("Notification preferences must be on/off switches for: %(keys)s.")
                % {"keys": ", ".join(PREFERENCE_KEYS)}
            )
        return value


class SelfRegisterSerializer(serializers.ModelSerializer):
    """
    Public self-registration — caller chooses role (admin or owner).

    No password: the account is created with set_unusable_password(); the
    frontend immediately drives the user through `otp/request` + `otp/verify`
    (or Google Sign-In) to complete sign-in.
    """

    accept_terms = serializers.BooleanField(write_only=True)
    role = serializers.ChoiceField(
        choices=["admin", "owner", "renter"], default="owner"
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "preferred_language",
            "accept_terms",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value.lower()

    def validate_accept_terms(self, value):
        if value is not True:
            raise serializers.ValidationError(
                _("You must accept the Terms of Service and Privacy Policy.")
            )
        return value

    def create(self, validated_data):
        validated_data.pop("accept_terms", None)
        user = User(terms_accepted_at=timezone.now(), **validated_data)
        user.set_unusable_password()
        user.save()
        return user
