from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('users/all', views.all_users, name='all-users'),
    path('properties/all', views.all_props, name='all-props'),
    path('companies/all', views.all_comps, name='all-companies'),
    path('subs', views.all_subs, name='all-subs'),
    path('subs/delete/<uuid:uuid>', views.delete_subs, name='del-subs'),
    path('report/tenant/list/<int:id>', views.tenant_list, name='tenant-list'),
]
