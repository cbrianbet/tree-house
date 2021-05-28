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
    path('subs/edit/<uuid:uuid>', views.edit_subs, name='edit-subs'),
    path('report/tenant/list/<int:id>', views.tenant_list, name='tenant-list'),
    path('report/tenant/listings', views.tenant_listing, name='tenant-listing'),
    path('report/invoices/listings', views.invoice_report, name='invoice-report'),
    path('report/staff/listings', views.staffList, name='staff-report'),
    path('report/tenant/ledger/<uuid:uuid>', views.tenant_ledger, name='tenant-ledger'),
    path('report/tenants/ledger', views.tenants_ledge_listing, name='tenants-ledge-list'),
    path('pay/ledger/list/<uuid:uuid>', views.pay_ledger_list, name='ledger-list'),
]
