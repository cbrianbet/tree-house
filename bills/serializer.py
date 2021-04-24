from .models import *
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers


class RentInvoiceSerializer(serializers.ModelSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = RentInvoice
        fields = ['id', 'password', 'email', 'first_name', 'last_name', 'access_level', 'gender']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = Invoice
        fields = ['id', 'password', 'email', 'first_name', 'last_name', 'access_level', 'gender']

