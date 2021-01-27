from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import *
from properties.models import *


@login_required
def tenant_bills(request, u_uid):
    tenant = Tenant.objects.get(uuid=u_uid)
    invoice = Invoice.objects.filter(invoice_for=tenant.profile.user)

    for inv in invoice:
        total = 0
        inv_items = InvoiceItems.objects.filter(invoice=inv)
        a = []
        for i in inv_items:
            total = total + i.amount

        a.append({
            'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
            'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
            'created_at': inv.created_at, 'paid': 0, "status": inv.status
        })
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
            'created_at': inv.created_at, 'paid': 0, "status": inv.status
        })
    context = {
        'user': request.user,
        'bills': a,
        'invoice': invoice,
    }
    return render(request, 'bills/all_invoices.html', context)


@login_required
def invoice_info(request, i_id):
    invoice = Invoice.objects.get(uuid=i_id)
    inv_items = InvoiceItems.objects.filter(invoice=invoice)
    a = []
    if request.method == "POST":
        print(request.POST)
        uuid = request.POST.getlist('uuid')
        payment = request.POST.getlist('payment_mode')
        amount = request.POST.getlist('amount')
        trans = request.POST.getlist('trans')
        remar = request.POST.getlist('remarks')
        datepaid = request.POST.getlist('datepaid')
        term = request.POST.getlist('term')
        close = False

        if term[0] == 'on':
            close = not close

        for i in range(len(uuid)):
            if amount[i] != '':
                pay_item = InvoiceItemsTransaction.objects.create(
                    created_by=request.user, invoice_item=InvoiceItems.objects.get(uuid=uuid[i]), transaction_code=trans[i],
                    amount_paid=amount[i], payment_mode=payment[i], remarks=remar[i], date_paid=datepaid[i]
                )

                pay_item.save()
        if close:
            invoice = Invoice.objects.get(uuid=InvoiceItems.objects.get(uuid=uuid[0]).invoice.uuid)
            invoice.status = close
            invoice.save()

    context = {
        'user': request.user,
        'bills': inv_items,
        'invoice': invoice,
    }
    return render(request, 'bills/add_payments.html', context)


@login_required
def invoice(request, i_id):
    invoice = Invoice.objects.get(uuid=i_id)
    inv_items = InvoiceItems.objects.filter(invoice=invoice)
    prop = Properties.objects.get(id=invoice.unit.property.id)
    if prop.rent_collection == 'Occ_date':
        pass
        # TODO code to pull next date
    else:
        pass
        # TODO code to pull date and check month

    if request.user.acc_type.id == 4:
        ten = Tenant.objects.get(profile__user=request.user).unit.property.company

        company = Companies.objects.get(id=ten.id)
        owner = CompanyProfile.objects.get(company=company).user
        profile = Profile.objects.get(user=owner)
    else:
        company = Companies.objects.get(id=CompanyProfile.objects.get(user=request.user).company.id)
        profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        print(request.POST)
        trans = request.POST.getlist('term')
        trans = request.POST.getlist('code')
        trans = request.POST.getlist('code')
        trans = request.POST.getlist('code')
    context = {
        'user': request.user,
        'bills': inv_items,
        'invoice': invoice,
        'company': company,
        'profile': profile,
        'prop': prop.rent_collection
    }
    return render(request, 'bills/invoice.html', context)


@login_required
def personal_bills(request):
    tenant = Tenant.objects.get(profile__user=request.user)
    invoice = Invoice.objects.filter(invoice_for=tenant.profile.user)
    a=[]
    for inv in invoice:
        total = 0
        inv_items = InvoiceItems.objects.filter(invoice=inv)
        for i in inv_items:
            total = total + i.amount

        a.append({
            'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
            'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
            'created_at': inv.created_at, 'paid': 0, "status": inv.status
        })
    context = {
        'bills': a,
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
