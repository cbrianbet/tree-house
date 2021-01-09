import uuid as uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from authapp.managers import CustomUserManager


class Users(AbstractUser):
    uuid = models.UUIDField(uuid.uuid4, editable=False, unique=True)
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(_('email address'), unique=False)

    USERNAME_FIELD = 'username'

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = "User"


class Profile(models.Model):
    uuid = models.UUIDField(uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    msisdn = models.CharField(max_length=15)
    terms_accepted = models.BooleanField(null=True)

    class Meta:
        db_table = "Profile"
