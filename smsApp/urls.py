from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('sms/metrics', views.index, name='sms-home'),
    #api
]
