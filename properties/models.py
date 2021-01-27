import uuid as u_id
from datetime import date

from django.db import models
from django.utils import timezone

from authapp.models import Users, Profile


class Companies(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    no_of_emp = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=40, blank=True, null=True)
    logo = models.ImageField(upload_to='logo/%Y/%m/', null=True, blank=True)

    class Meta:
        db_table = "Companies"


class CompanyProfile(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)


    class Meta:
        db_table = "Company_Profile"


class Properties(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    property_name = models.CharField(max_length=50)
    owner = models.CharField(max_length=50, null=True, blank=True)
    property_type = models.CharField(max_length=50)
    building_type = models.CharField(max_length=50, null=True, blank=True)
    property_value = models.CharField(max_length=20, null=True, blank=True)
    mngmt_start = models.DateField(default=timezone.now)
    no_of_units = models.PositiveIntegerField(default=1)
    no_of_floors = models.PositiveIntegerField(default=1)
    parking = models.PositiveIntegerField(default=0)
    electricity = models.CharField(max_length=20)
    water = models.CharField(max_length=20)
    pics = models.ImageField(upload_to='propPic/%Y/%m/', null=True, blank=True)
    long = models.DecimalField(max_digits=19, decimal_places=6, null=True)
    lat = models.DecimalField(max_digits=19, decimal_places=6, null=True)
    rent_collection = models.CharField(max_length=50, default="Spec_date")
    specific_day = models.CharField(max_length=5, blank=True, null=True)
    penalty_type = models.CharField(max_length=50, default="percent")
    penalty_value = models.CharField(max_length=50, default="20")
    location_desc = models.CharField(max_length=50, null=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="p_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="p_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "Properties"

    def delete(self, *args, **kwargs):
        self.pics.delete()
        super().delete(*args, **kwargs)


class Unit(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    unit_name = models.CharField(max_length=40)
    type_of_unit = models.CharField(max_length=40, null=True, blank=True)
    value = models.CharField(max_length=40)
    unit_status = models.CharField(max_length=40, default='Vacant')
    area = models.CharField(max_length=40, null=True, blank=True)
    service_charge = models.CharField(max_length=40, default="0")
    parking_assigned = models.PositiveIntegerField(default=0)
    property = models.ForeignKey(Properties, on_delete=models.CASCADE)
    floor = models.PositiveIntegerField()
    other_specify = models.CharField(max_length=30, null=True, blank=True)
    size = models.CharField(max_length=30, null=True, blank=True)
    security_deposit = models.CharField(max_length=20, default=0)
    discount_type = models.CharField(max_length=20, null=True, blank=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="u_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="u_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Units"


class Tenant(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    secondary_msisdn = models.CharField(max_length=40)
    date_occupied = models.DateTimeField()
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    discount_type = models.CharField(max_length=40, default="None")
    lease = models.FileField(upload_to='Lease/%Y/%m/')
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="t_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="t_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Tenant"
