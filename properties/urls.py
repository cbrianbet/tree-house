from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('property/list', views.properties_list, name='prop-list'),
    path('property/add', views.properties_add, name='add-list'),
    path('property/units/list/<uuid:u_uid>', views.list_units, name='unit-list'),
    path('property/units/add/<int:floor>/<uuid:u_uid>', views.add_units, name='unit-add'),
    path('property/units/tenant/add/<uuid:u_uid>', views.add_tenant, name='tenant-add'),
    path('property/units/tenant/<uuid:u_uid>', views.view_tenant, name='view-tenant'),
    path('property/units/tenant/swap/<uuid:u_uid>', views.swap_tenant, name='swap-tenant'),
    path('property/file/upload', views.prop_file_upload, name='file-prop'),
    path('property/file/template', views.prop_template, name='file-template'),
    path('property/tenant/file/upload', views.tenant_file_upload, name='file-tenant'),


]
