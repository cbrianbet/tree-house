import uuid as u_id

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from authapp.managers import CustomUserManager


class AccTypes(models.Model):
    acc_type = models.CharField(max_length=15)

    def __str__(self):
        return self.acc_type

    class Meta:
        db_table = "Acc_Type"


class Users(AbstractUser):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(_('email address'), unique=False)
    acc_type = models.ForeignKey(AccTypes, on_delete=models.CASCADE)

    USERNAME_FIELD = 'username'

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = "User"


class Profile(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    msisdn = models.CharField(max_length=15, null=True)
    terms_accepted = models.BooleanField(null=True)

    class Meta:
        db_table = "Profile"
