from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('property/list', views.properties_list, name='prop-list'),
    path('property/add', views.properties_add, name='add-list'),
    path('property/units/list/<uuid:u_uid>', views.list_units, name='unit-list'),
    path('property/units/add/<int:floor>/<uuid:u_uid>', views.add_units, name='unit-add'),

]
