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
    id_number = models.CharField(max_length=12, null=True, blank=True)
    msisdn = models.CharField(max_length=15, null=True, blank=True)
    terms_accepted = models.BooleanField(null=True)
    hapokash = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "Profile"


class Subscriptions(models.Model):
    uuid = models.UUIDField(default=u_id.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=350)
    duration = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    value = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="sub_created_by")
    updated_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="sub_updated_by", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = "Subscription"


class AuthTokens(models.Model):
    auth = models.CharField(max_length=1500)


    class Meta:
        db_table = "AuthTokens"
