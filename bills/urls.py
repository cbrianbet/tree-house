from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('property/units/tenant/bill/<uuid:u_uid>', views.tenant_bills, name='bills-tenant'),
    path('property/units/tenant/invoice/add/<uuid:u_uid>', views.invoice_tenant, name='invoice-tenant'),

]
