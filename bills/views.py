from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import *
from properties.models import *


@login_required
def tenant_bills(request, u_uid):
    tenant = Tenant.objects.get(uuid=u_uid)
    invoice = Invoice.objects.filter(invoice_for=tenant.profile.user)
    context = {
        'bills': invoice,
        'u_uid': u_uid,
        'user': request.user,
    }
    return render(request, 'bills/tenant_bills.html', context)


@login_required
def all_invoices(request):
    invoice = Invoice.objects.filter(
        unit__property__company=CompanyProfile.objects.get(user=request.user).company).order_by('invoice_no')
    a = []
    for inv in invoice:
        total = 0
        inv_items = InvoiceItems.objects.filter(invoice=inv)
        for i in inv_items:
            total = total + i.amount

        a.append({
            'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
            'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
            'created_at': inv.created_at, 'paid': total, "status": inv.status
        })
    context = {
        'user': request.user,
        'bills': a,
        'invoice': invoice
    }
    return render(request, 'bills/all_invoices.html', context)


@login_required
def invoice_info(request, i_id):
    invoice = Invoice.objects.get(uuid=i_id)
    inv_items = InvoiceItems.objects.filter(invoice=invoice)
    a = []
    if request.method == "POST":
        print(request.POST)
        trans = request.POST.getlist('term')
        trans = request.POST.getlist('code')
        trans = request.POST.getlist('code')
        trans = request.POST.getlist('code')
    context = {
        'user': request.user,
        'bills': inv_items,
        'invoice': invoice
    }
    return render(request, 'bills/add_payments.html', context)


@login_required
def personal_bills(request):
    tenant = Tenant.objects.get(profile__user=request.user)
    invoice = Invoice.objects.filter(invoice_for=tenant.profile.user)
    for inv in invoice:
        total = 0
        inv_items = InvoiceItems.objects.filter(invoice=inv)
        for i in inv_items:
            total = total + i.amount
        print(total)
    context = {
        'bills': invoice,
        'user': request.user,
    }
    return render(request, 'bills/tenant_bills_personal.html', context)


@login_required
def invoice_tenant(request, u_uid):
    t = Tenant.objects.get(uuid=u_uid)
    if request.method == "POST":
        print(request.POST)
        name = request.POST.getlist('inv_name')
        amt = request.POST.getlist('inv_amnt')
        remarks = request.POST.getlist('remark')
        for i in amt:
            print(i)
        inv_no = increment_invoice_number()
        inv = Invoice.objects.create(created_by=request.user, invoice_no=inv_no, invoice_for=t.profile.user,
                                     unit=t.unit)
        inv.save()

        for i in range(len(name)):
            print(round(float(amt[i]), 2))
            inv_item = InvoiceItems.objects.create(invoice=inv, invoice_item=name[i], amount=round(float(amt[i]), 2),
                                                   description=remarks[i])
            inv_item.save()

        return redirect('bills-tenant', u_uid=u_uid)

    tenant = Tenant.objects.get(uuid=u_uid)
    invoice = InvoiceItems.objects.filter(invoice__invoice_for=tenant.profile.user)
    context = {
        'bills': invoice,
        'u_uid': u_uid,
        'user': request.user,
    }
    return render(request, 'bills/add_invoice.html', context)


def increment_invoice_number():
    last_invoice = Invoice.objects.all().order_by('id').last()
    if not last_invoice:
        return 'INV-00001'
    invoice_no = last_invoice.invoice_no
    invoice_int = int(invoice_no.split('INV-')[-1])
    new_invoice_int = invoice_int + 1
    new_invoice_no = 'INV-' + str('%05d' % new_invoice_int)
    return new_invoice_no
