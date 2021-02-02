from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('property/units/tenant/bill/<uuid:u_uid>', views.tenant_bills, name='bills-tenant'),
    path('property/units/tenant/bill/personal', views.personal_bills, name='tenant_bill-personal'),
    path('bills/invoices/all', views.all_invoices, name='all-invoices'),
    path('bills/invoice/more/<uuid:i_id>', views.invoice_info, name='more-info'),
    path('bills/invoice/<uuid:i_id>', views.invoice, name='invoice'),
    path('bills/rinvoice/<uuid:i_id>', views.rent_invoice, name='rinvoice'),
    path('bills/record/payment-request/<uuid:i_id>', views.record_payment_request, name='record-payment'),
    path('bills/payment/trans/<uuid:uuid>', views.individual_trans, name='individual-payments'),
    path('bills/approve/payment', views.approve_request, name='approve-payment'),
    # path('property/units/tenant/invoice/add/<uuid:u_uid>', views.invoice_tenant, name='invoice-tenant'),

]
