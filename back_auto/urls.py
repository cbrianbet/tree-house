from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('send_invoice', views.send_invoice, name='auto-send-invoice'),
]
