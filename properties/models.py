import uuid as u_id
from django.db import models

from authapp.models import Users


class Companies(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=50)
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