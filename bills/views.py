from itertools import chain

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from uuid import uuid4

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
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        invoice = Invoice.objects.filter(
            unit__property__company=CompanyProfile.objects.get(user=request.user).company).order_by('invoice_no')
    if request.user.acc_type.id == 5:
        prop = PropertyStaff.objects.filter(user=request.user).values_list('property', flat=True)
        invoice = Invoice.objects.filter(unit__property__in=prop,
                                         unit__property__company=CompanyProfile.objects.get(
                                             user=request.user).company).order_by('invoice_no')
    a = []
    for inv in invoice:
        total = 0
        paid = 0
        inv_items = InvoiceItems.objects.filter(invoice=inv)
        for i in inv_items:
            total = total + i.amount
            trans = InvoiceItemsTransaction.objects.filter(invoice_item=i)
            for ab in trans:
                paid = ab.amount_paid + paid

        a.append({
            'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
            'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
            'created_at': inv.created_at, 'paid': paid, "status": inv.status
        })
    r_invoice = RentInvoice.objects.filter(
        unit__property__company=CompanyProfile.objects.get(user=request.user).company).order_by('invoice_no')
    r = []
    for inv in r_invoice:
        total = 0
        paid = 0
        inv_items = RentItems.objects.filter(invoice=inv)
        for i in inv_items:
            total = total + i.amount
            trans = RentItemTransaction.objects.filter(invoice_item=i)
            for ab in trans:
                paid = ab.amount_paid + paid

        r.append({
            'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
            'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
            'created_at': inv.created_at, 'paid': paid, "status": inv.status
        })
    context = {
        'user': request.user,
        'bills': a,
        'rent': r,
        'invoice': invoice,
    }
    return render(request, 'bills/all_invoices.html', context)


@login_required
def invoice_info(request, i_id):
    try:
        invoice = Invoice.objects.get(uuid=i_id)
        inv_items = InvoiceItems.objects.filter(invoice=invoice)
    except Invoice.DoesNotExist:
        invoice = RentInvoice.objects.get(uuid=i_id)
        inv_items = RentItems.objects.filter(invoice=invoice)
    a = []
    if request.method == "POST":
        print(request.POST)
        uuid = request.POST.getlist('uuid')
        payment = request.POST.getlist('payment_mode')
        amount = request.POST.getlist('amount')
        trans = request.POST.getlist('trans')
        remar = request.POST.getlist('remarks')
        datepaid = request.POST.getlist('datepaid')
        term = request.POST.get('term')
        close = False

        if term == 'on':
            close = not close

        for i in range(len(uuid)):
            if amount[i] != '':
                try:
                    pay_item = InvoiceItemsTransaction.objects.create(
                        created_by=request.user, invoice_item=InvoiceItems.objects.get(uuid=uuid[i]),
                        transaction_code=trans[i],
                        amount_paid=float(amount[i]), payment_mode=payment[i], remarks=remar[i], date_paid=datepaid[i]
                    )

                    pay_item.save()
                except:
                    pay_item = RentItemTransaction.objects.create(
                        created_by=request.user, invoice_item=RentItems.objects.get(uuid=uuid[i]),
                        transaction_code=trans[i],
                        amount_paid=float(amount[i]), payment_mode=payment[i], remarks=remar[i], date_paid=datepaid[i]
                    )

                    pay_item.save()

        if close:
            try:
                invoice = Invoice.objects.get(uuid=InvoiceItems.objects.get(uuid=uuid[0]).invoice.uuid)
                invoice.status = close
                invoice.save()
                return redirect('all-invoices')
            except:
                invoice = RentInvoice.objects.get(uuid=RentItems.objects.get(uuid=uuid[0]).invoice.uuid)
                invoice.status = close
                invoice.save()
                return redirect('all-invoices')

    context = {
        'user': request.user,
        'bills': inv_items,
        'invoice': invoice,
    }
    return render(request, 'bills/add_payments.html', context)


@login_required
def record_payment_request(request, i_id):
    try:
        invoice = Invoice.objects.get(uuid=i_id)
        inv_items = InvoiceItems.objects.filter(invoice=invoice)
    except Invoice.DoesNotExist:
        invoice = RentInvoice.objects.get(uuid=i_id)
        inv_items = RentItems.objects.filter(invoice=invoice)

    if request.method == "POST":
        print(request.POST)
        uuid = request.POST.getlist('uuid')
        payment = request.POST.getlist('payment_mode')
        amount = request.POST.getlist('amount')
        trans = request.POST.getlist('trans')
        remar = request.POST.getlist('remarks')
        datepaid = request.POST.getlist('datepaid')

        if request.FILES:
            receipt = request.FILES.getlist('evidence')
        else:
            receipt = ''

        try:
            for i in range(len(uuid)):
                if amount[i] != '':
                        pay_item = InvoiceItemsRequest.objects.create(
                            created_by=request.user, invoice_item=InvoiceItems.objects.get(uuid=uuid[i]),
                            transaction_code=trans[i], amount_paid=amount[i], payment_mode=payment[i], remarks=remar[i],
                            date_paid=datepaid[i], receipt=receipt[i]
                        )

                        pay_item.save()

            return redirect('invoice', i_id=i_id)
        except InvoiceItems.DoesNotExist:
            for i in range(len(uuid)):
                if amount[i] != '':

                    pay_item = RentInvItemsRequest.objects.create(
                        created_by=request.user, invoice_item=RentItems.objects.get(uuid=uuid[i]),
                        transaction_code=trans[i],
                        amount_paid=amount[i], payment_mode=payment[i], remarks=remar[i], date_paid=datepaid[i],
                        receipt=receipt[i]
                    )

                    pay_item.save()

            return redirect('rinvoice', i_id=i_id)



    context = {
        'user': request.user,
        'bills': inv_items,
        'invoice': invoice,
    }
    return render(request, 'bills/add_payment_request.html', context)


@login_required
def invoice(request, i_id):
    invoice = Invoice.objects.get(uuid=i_id)
    inv_items = InvoiceItems.objects.filter(invoice=invoice)
    prop = Properties.objects.get(id=invoice.unit.property.id)
    bills = []
    for b in inv_items:
        try:
            paid = 0
            p = InvoiceItemsTransaction.objects.filter(invoice_item=b)
            for i in p:
                paid = paid + i.amount_paid
                print(p)

        except:
            paid = 0
        bills.append({
            'invoice_item': b.invoice_item, 'description': b.description, 'amount': b.amount, 'paid': paid})
    if prop.rent_collection == 'Occ_date':
        pass
        # TODO code to pull next date
    else:
        pass
        # TODO code to pull date and check month

    if request.user.acc_type.id == 4:
        ten = Tenant.objects.get(profile__user=request.user).unit.property.company

        company = Companies.objects.get(id=ten.id)
        owner = CompanyProfile.objects.filter(company=company).first().user
        profile = Profile.objects.get(user=owner)
    else:
        company = Companies.objects.get(id=CompanyProfile.objects.get(user=request.user).company.id)
        profile = Profile.objects.get(user=request.user)
    context = {
        'user': request.user,
        'bills': bills,
        'invoice': invoice,
        'company': company,
        'profile': profile,
        'prop': prop.rent_collection,
        'due_date': invoice.created_at.date(),
    }
    return render(request, 'bills/invoice.html', context)


@login_required
def rent_invoice(request, i_id):
    invoice = RentInvoice.objects.get(uuid=i_id)
    inv_items = RentItems.objects.filter(invoice=invoice)
    prop = Properties.objects.get(id=invoice.unit.property.id)
    bills = []
    for b in inv_items:

        paid = 0
        p = RentItemTransaction.objects.filter(invoice_item=b)
        for i in p:
            paid = paid + i.amount_paid
            print(p)

        bills.append({
            'invoice_item': b.invoice_item, 'description': b.description, 'amount': b.amount, 'paid': paid})

    if request.user.acc_type.id == 4:
        ten = Tenant.objects.get(profile__user=request.user).unit.property.company

        company = Companies.objects.get(id=ten.id)
        owner = CompanyProfile.objects.filter(company=company).first().user
        profile = Profile.objects.get(user=owner)
    else:
        company = Companies.objects.get(id=CompanyProfile.objects.get(user=request.user).company.id)
        profile = Profile.objects.get(user=request.user)
    context = {
        'user': request.user,
        'bills': bills,
        'invoice': invoice,
        'company': company,
        'profile': profile,
        'prop': prop.rent_collection,
        'due_date': invoice.date_due,
    }
    return render(request, 'bills/invoice.html', context)


@login_required
def personal_bills(request):
    tenant = Tenant.objects.get(profile__user=request.user)
    invoice = Invoice.objects.filter(invoice_for=tenant.profile.user)
    a = []
    for inv in invoice:
        total = 0
        paid = 0
        inv_items = InvoiceItems.objects.filter(invoice=inv)
        for i in inv_items:
            total = total + i.amount
            trans = InvoiceItemsTransaction.objects.filter(invoice_item=i)
            for ab in trans:
                paid = ab.amount_paid + paid

        a.append({
            'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
            'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
            'created_at': inv.created_at, 'paid': paid, "status": inv.status
        })

    r_invoice = RentInvoice.objects.filter(invoice_for=tenant.profile.user)
    r = []
    for inv in r_invoice:
        total = 0
        paid = 0
        r_inv_items = RentItems.objects.filter(invoice=inv)
        for i in r_inv_items:
            total = total + i.amount
            trans = RentItemTransaction.objects.filter(invoice_item=i)
            for ab in trans:
                paid = ab.amount_paid + paid

        r.append({
            'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
            'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
            'created_at': inv.created_at, 'paid': paid, "status": inv.status
        })
    context = {
        'bills': a,
        'rent': r,
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


def increment_rent_invoice_number():
    last_invoice = RentInvoice.objects.all().order_by('id').last()
    if not last_invoice:
        return 'INV-REN-00001'
    invoice_no = last_invoice.invoice_no
    print()
    invoice_int = int(invoice_no.split('INV-REN-')[-1])
    new_invoice_int = invoice_int + 1
    new_invoice_no = 'INV-REN-' + str('%05d' % new_invoice_int)
    return new_invoice_no


@login_required
def approve_request(request, pid):
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        try:
            pay = InvoiceItemsRequest.objects.get(uuid=pid)
            trans = InvoiceItemsTransaction.objects.create(
                payment_mode=pay.payment_mode, invoice_item=pay.invoice_item, transaction_code=pay.transaction_code,
                amount_paid=pay.amount_paid, date_paid=pay.date_paid, created_by=request.user)

            trans.save()
            pay.status = True
            pay.save()
        except InvoiceItemsRequest.DoesNotExist:
            pay = RentInvItemsRequest.objects.get(uuid=pid)
            trans = RentItemTransaction.objects.create(
                payment_mode=pay.payment_mode, invoice_item=pay.invoice_item, transaction_code=pay.transaction_code,
                amount_paid=pay.amount_paid, date_paid=pay.date_paid, created_by=request.user)

            trans.save()
            pay.status = True
            pay.save()
        except Exception as e:
            raise e

        return redirect('req-payment-list')


@login_required
def reject_request(request, pid):
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        try:
            pay = InvoiceItemsRequest.objects.get(uuid=pid)

            pay.status = False
            pay.save()
        except InvoiceItemsRequest.DoesNotExist:
            pay = RentInvItemsRequest.objects.get(uuid=pid)

            pay.status = False
            pay.save()
        except Exception as e:
            raise e

        return redirect('req-payment-list')


@login_required
def list_request(request):
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        comp = CompanyProfile.objects.get(user=request.user).company
        prop = Properties.objects.filter(company=comp).values_list('id', flat=True)
        rent_req = RentInvItemsRequest.objects.filter(invoice_item__invoice__unit__property__in=prop).exclude(status=True).exclude(status=False)
        req = InvoiceItemsRequest.objects.filter(invoice_item__invoice__unit__property__in=prop).exclude(status=True).exclude(status=False)
        rent_req_past = RentInvItemsRequest.objects.filter(invoice_item__invoice__unit__property__in=prop).exclude(status=None).exclude(status='')
        req_past = InvoiceItemsRequest.objects.filter(invoice_item__invoice__unit__property__in=prop).exclude(status=None).exclude(status='')

    else:
        raise PermissionDenied

    context = {
        'user': request.user,
        'req': chain(req, rent_req),
        'req_past': chain(rent_req_past, req_past)
    }
    return render(request, 'bills/all_requests.html',context)


@login_required
def individual_trans(request, uuid):
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        comp = CompanyProfile.objects.get(user=request.user).company
        prop = Properties.objects.filter(company=comp).values_list('id', flat=True)
        rentrec = RentItemTransaction.objects.filter(invoice_item__invoice__uuid=uuid).order_by('created_by')
        invrec = InvoiceItemsTransaction.objects.filter(invoice_item__invoice__uuid=uuid).order_by('created_by')
        print(rentrec)
    if request.user.acc_type.id == 4:
        rentrec = RentItemTransaction.objects.filter(invoice_item__invoice__uuid=uuid).order_by('created_by')
        invrec = InvoiceItemsTransaction.objects.filter(invoice_item__invoice__uuid=uuid).order_by('created_by')


    context = {
        'user': request.user,
        'req': rentrec,
        'rreq': invrec,
    }
    return render(request, 'bills/trans.html',context)
