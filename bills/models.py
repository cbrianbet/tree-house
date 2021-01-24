import uuid as u_id

from django.db import models
from authapp.models import Users
from properties.models import Unit


class Invoice(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    invoice_no = models.CharField(max_length=50, null=True)
    status = models.BooleanField(default=False)
    invoice_for = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='user_invoiced')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="i_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="i_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Invoice"


class InvoiceItems(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    invoice_item = models.CharField(max_length=50, default="Default")
    description = models.CharField(max_length=150, null=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)

    class Meta:
        db_table = "Invoice Items"


class InvoiceItemsTransaction(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    invoice_item = models.ForeignKey(InvoiceItems, on_delete=models.CASCADE)
    transaction_code = models.CharField(max_length=150, null=True)
    payment_mode = models.CharField(max_length=50, null=True)
    remarks = models.CharField(max_length=150, null=True)
    amount_paid = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="it_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="it_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "Invoice Items Transaction"

