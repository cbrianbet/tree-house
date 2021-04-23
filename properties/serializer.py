from .models import *
from rest_framework import serializers


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update({'property': Properties.objects.get(id=data['property']).property_name})
        return data


class TenantHistorySerializer(serializers.ModelSerializer):
    curr_unit = UnitSerializer(read_only=True)
    class Meta:
        model = TenantHistory
        fields = "__all__"


class PropertiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Properties
        fields = "__all__"


class VacantUnitSerializer(serializers.ModelSerializer):
    property = PropertiesSerializer(read_only=True)
    class Meta:
        model = Unit
        fields = "__all__"
