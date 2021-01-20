from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import *
from properties.models import *


@login_required
def tenant_bills(request, u_uid):
    tenant = Tenant.objects.get(uuid=u_uid)
    invoice = InvoiceItems.objects.filter(invoice__invoice_for=tenant.profile.user)
    context = {
        'bills': invoice,
        'u_uid': u_uid,
        'user': request.user,
    }
    return render(request, 'bills/tenant_bills.html', context)

@login_required
def invoice_tenant(request, u_uid):
    if request.method == "POST":
        print(request.POST)
        name = request.POST.getlist('inv_name')
        amt = request.POST.getlist('inv_amount')
        remarks = request.POST.getlist('remarks')

        inv = Invoice.objects.all()
    tenant = Tenant.objects.get(uuid=u_uid)
    invoice = InvoiceItems.objects.filter(invoice__invoice_for=tenant.profile.user)
    context = {
        'bills': invoice,
        'u_uid': u_uid,
        'user': request.user,
    }
    return render(request, 'bills/add_invoice.html', context)
