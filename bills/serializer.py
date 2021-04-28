from properties.models import TransactionCodes
from .models import *
from rest_framework import serializers


class RentInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentInvoice
        fields = '__all__'


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class RentTransSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentItemTransaction
        fields = '__all__'


class InvTransSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItemsTransaction
        fields = '__all__'


class TransSerializer(serializers.ModelSerializer):
    uuid = serializers.CharField(max_length=200)
    class Meta:
        model = RentItemTransaction
        fields = ['uuid']


class WallPaySerializer(serializers.ModelSerializer):
    inv_uuid = serializers.UUIDField()
    amount = serializers.CharField()
    class Meta:
        model = RentItemTransaction
        fields = ['inv_uuid', 'amount']


class ConfInvPaySerializer(serializers.ModelSerializer):
    inv_uuid = serializers.UUIDField()
    trans = serializers.CharField()
    class Meta:
        model = TransactionCodes
        fields = ['inv_uuid', 'trans']


class PayInvPaySerializer(serializers.ModelSerializer):
    amount = serializers.CharField()
    class Meta:
        model = TransactionCodes
        fields = ['amount']


class WalletTopupSerializer(serializers.ModelSerializer):
    amount = serializers.CharField()
    mobile = serializers.CharField(max_length=12)
    class Meta:
        model = TransactionCodes
        fields = ['amount', 'mobile']


class WalletWithdrawSerializer(serializers.ModelSerializer):
    amount = serializers.CharField()
    mobile = serializers.CharField(max_length=12)
    class Meta:
        model = TransactionCodes
        fields = ['amount', 'mobile']

