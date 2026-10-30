from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.buildings.models import Building

from .models import Majority, Poll, PollOption
from .results import poll_results


class PollSerializer(serializers.ModelSerializer):
    building_id = serializers.PrimaryKeyRelatedField(source="building", queryset=Building.objects.all())
    building_name = serializers.CharField(source="building.name", read_only=True)
    options = serializers.ListField(child=serializers.CharField(max_length=200), write_only=True, min_length=2, max_length=10)
    is_open = serializers.BooleanField(read_only=True)
    quorum_percent = serializers.IntegerField(min_value=0, max_value=100, required=False, default=0)
    majority = serializers.ChoiceField(choices=Majority.choices, required=False, default=Majority.SIMPLE)

    class Meta:
        model = Poll
        fields = [
            "id", "building_id", "building_name", "title", "description", "options", "closes_at", "closed_at",
            "quorum_percent", "majority", "is_open", "created_at",
        ]
        read_only_fields = ["id", "closed_at", "created_at"]

    def validate_closes_at(self, value):
        from django.utils import timezone

        if value <= timezone.now():
            raise serializers.ValidationError(_("The closing time must be in the future."))
        return value

    def create(self, validated_data):
        options = validated_data.pop("options")
        poll = Poll.objects.create(**validated_data)
        PollOption.objects.bulk_create([PollOption(poll=poll, text=t.strip(), order=i) for i, t in enumerate(options)])
        return poll

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = request.user if request else None
        is_admin = bool(user and user.role == "admin")
        data["options"] = [{"id": str(o.pk), "text": o.text} for o in instance.options.all()]
        # Residents see results only once the poll is closed; admins can follow along
        if is_admin or not instance.is_open:
            data["results"] = poll_results(instance)
        if user is not None:
            data["my_votes"] = [
                {"apartment_id": str(v.apartment_id), "option_id": str(v.option_id)}
                for v in instance.votes.filter(apartment__in=_my_units(user, instance.building))
            ]
            data["my_units"] = [{"id": str(a.pk), "unit_number": a.unit_number} for a in _my_units(user, instance.building)]
        return data


def _my_units(user, building):
    from django.db.models import Q

    from apps.apartments.models import Apartment

    if user.role == "renter":
        return Apartment.objects.none()
    return Apartment.objects.filter(building=building).filter(Q(owner=user) | Q(owners=user)).distinct()
