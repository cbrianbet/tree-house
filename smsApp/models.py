from django.db import models
import uuid as u_id
from authapp.models import Users

class SmsTransactions(models.Model):
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)
    refNumber = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    transType = models.CharField(max_length=15)
    balance = models.CharField(max_length=50)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CompanySms(models.Model):
    transaction = models.ForeignKey(SmsTransactions, on_delete=models.CASCADE)
    commission_pc = models.PositiveIntegerField()
    commission = models.PositiveIntegerField()


class SmsLog(models.Model):
    text = models.CharField(max_length=1500, null=True)
    msisdn = models.CharField(max_length=1500)
    sender = models.CharField(max_length=15, default="DEPTHSMS")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SenderRequests(models.Model):
    status = models.BooleanField(null=True)
    sender = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

