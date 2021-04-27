from .models import *
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers


class RentInvoiceSerializer(serializers.ModelSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = RentInvoice
        fields = '__all__'


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = Invoice
        fields = '__all__'


class RentTransSerializer(serializers.ModelSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = RentItemTransaction
        fields = '__all__'


class InvTransSerializer(serializers.ModelSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = InvoiceItemsTransaction
        fields = '__all__'

