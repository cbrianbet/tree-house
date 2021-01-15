import uuid as u_id
from datetime import date

from django.db import models
from django.utils import timezone

from authapp.models import Users


class Companies(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    no_of_emp = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=40, blank=True, null=True)

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
    long = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    location_desc = models.CharField(max_length=50, null=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)


    class Meta:
        db_table = "Properties"


class Unit(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    unit_name = models.CharField(max_length=40)
    type_of_units = models.CharField(max_length=40)
    value = models.CharField(max_length=40)
    unit_status = models.CharField(max_length=40)
    area = models.CharField(max_length=40)
    service_charge = models.CharField(max_length=40)
    parking_assigned = models.PositiveIntegerField(default=0)
    property = models.ForeignKey(Properties, on_delete=models.CASCADE)

    class Meta:
        db_table = "Units"


class Tenant(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    unit_name = models.CharField(max_length=40)
    type_of_units = models.CharField(max_length=40)
    value = models.CharField(max_length=40)
    unit_status = models.CharField(max_length=40)
    area = models.CharField(max_length=40)
    service_charge = models.CharField(max_length=40)
    parking_assigned = models.PositiveIntegerField(default=0)
    property = models.ForeignKey(Properties, on_delete=models.CASCADE)

    class Meta:
        db_table = "Tenant"

