from datetime import datetime
from itertools import chain

import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from uuid import uuid4

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authapp.decorators import unsubscribed_user
from authapp.models import AuthTokens
from authapp.views import refreshToken, hapokashcreate, wallet_trans
from tree_house.settings import EMAIL_HOST_USER
from .models import *
from properties.models import *
from .serializer import InvTransSerializer, RentTransSerializer, TransSerializer, WallPaySerializer, \
    ConfInvPaySerializer, PayInvPaySerializer, WalletWithdrawSerializer, WalletTopupSerializer, WalletBalanceSerializer


@login_required
@unsubscribed_user
def tenant_bills(request, u_uid):
    tenant = Tenant.objects.get(uuid=u_uid)
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
        if inv.status:
            status = "CLOSED"
        else:
            status = "OPEN"

        a.append({
            'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
            'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
            'created_at': inv.created_at, 'paid': paid, "status": status
        })
    context = {
        'bills': a,
        'u_uid': u_uid,
        'user': request.user,
    }
    return render(request, 'bills/tenant_bills.html', context)


@login_required
@unsubscribed_user
def all_invoices(request):
    if request.user.acc_type.id == 4:
        return redirect('tenant_bill-personal')
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
@unsubscribed_user
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
        waiver = request.POST.getlist('waiver')

        if waiver == '':
            waiver = 0

        if term == 'on':
            close = not close

        for i in range(len(uuid)):
            if amount[i] != '':
                print(uuid)
                w = 0
                if waiver[i] == '':
                    w = 0
                else:
                    w = waiver[i]
                try:
                    pay_item = InvoiceItemsTransaction.objects.create(
                        created_by=request.user, invoice_item=InvoiceItems.objects.get(uuid=uuid[i]),
                        transaction_code=trans[i], waiver=w, amount_paid=float(amount[i]), payment_mode=payment[i],
                        remarks=remar[i], date_paid=datepaid[i]
                    )

                    pay_item.save()
                except InvoiceItems.DoesNotExist:
                    pay_item = RentItemTransaction.objects.create(
                        created_by=request.user, invoice_item=RentItems.objects.get(uuid=uuid[i]),
                        transaction_code=trans[i], waiver=waiver, amount_paid=float(amount[i]), payment_mode=payment[i],
                        remarks=remar[i], date_paid=datepaid[i]
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
        return redirect('all-invoices')

    context = {
        'user': request.user,
        'bills': inv_items,
        'invoice': invoice,
    }
    return render(request, 'bills/add_payments.html', context)


@login_required
@unsubscribed_user
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

        a = []
        try:
            for i in range(len(uuid)):
                if not receipt == '':
                    r = receipt[i]
                else:
                    r = ''
                if amount[i] != '':
                    pay_item = InvoiceItemsRequest.objects.create(
                        created_by=request.user, invoice_item=InvoiceItems.objects.get(uuid=uuid[i]),
                        transaction_code=trans[i], amount_paid=amount[i], payment_mode=payment[i], remarks=remar[i],
                        date_paid=datepaid[i], receipt=r
                    )

                    pay_item.save()
                    a.append(pay_item)
            if not a == []:
                cmp = CompanyProfile.objects.filter(company=a[0].invoice_item.invoice.unit.property.company).filter(
                    Q(user__acc_type_id=2) | Q(user__acc_type_id=3))[0]
                prof = Profile.objects.get(user=cmp.user)
                tenant = Tenant.objects.get(profile__user=request.user).unit
                inform_agent_payment(cmp.user.username, prof.first_name, cmp.user.email, tenant.property.property_name,
                                     tenant.unit_name)

            return redirect('invoice', i_id=i_id)
        except InvoiceItems.DoesNotExist:
            for i in range(len(uuid)):
                if not receipt == '':
                    r = receipt[i]
                else:
                    r = ''
                if amount[i] != '':
                    pay_item = RentInvItemsRequest.objects.create(
                        created_by=request.user, invoice_item=RentItems.objects.get(uuid=uuid[i]),
                        transaction_code=trans[i],
                        amount_paid=amount[i], payment_mode=payment[i], remarks=remar[i], date_paid=datepaid[i],
                        receipt=r
                    )

                    pay_item.save()
                    a.append(pay_item)
            if not a == []:
                cmp = CompanyProfile.objects.filter(company=a[0].invoice_item.invoice.unit.property.company).filter(
                    Q(user__acc_type_id=2) | Q(user__acc_type_id=3))[0]
                prof = Profile.objects.get(user=cmp.user)
                tenant = Tenant.objects.get(profile__user=request.user).unit
                inform_agent_payment(cmp.user.username, prof.first_name, cmp.user.email, tenant.property.property_name,
                                     tenant.unit_name)

            return redirect('rinvoice', i_id=i_id)

    context = {
        'user': request.user,
        'bills': inv_items,
        'invoice': invoice,
    }
    return render(request, 'bills/add_payment_request.html', context)


def inform_agent_payment(u, n, e, p, un):
    subject = "New Payment Request"
    message = '''
    Dear {}, 
    This email is to let you know that a payment request has been received from property {} unit {}. 
    Login to your portal at	mnestafrica.com for more details. Your username is {} incase you had forgotten'''.format(
        n, p, un, u)
    try:
        send_mail(subject, message, EMAIL_HOST_USER, [e], fail_silently=False)
    except:
        print('failed')


@login_required
@unsubscribed_user
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
@unsubscribed_user
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
            'invoice_item': b.invoice_item, 'description': b.description, 'amount': b.amount, 'paid': paid,
            'penalty': b.delay_penalties})

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
@unsubscribed_user
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
            total = total + i.amount + i.delay_penalties
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
@unsubscribed_user
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
        u = Users.objects.get(id=pay.invoice_item.invoice.invoice_for.id)
        inform_apprved(u.username, Profile.objects.get(user=u).first_name, pay.invoice_item.invoice.invoice_no, u.email)
        return redirect('req-payment-list')


def inform_apprved(u, n, prop, e):
    subject = "Payment for invoice {} Approved".format(prop)
    message = '''
    Dear {}, 
    This email is to let you know that Your payment request has been received and Approved. 
    Login to your portal at	mnestafrica.com to view the transaction. Your username is  {} incase you had forgotten'''.format(
        n, u)
    try:
        send_mail(subject, message, EMAIL_HOST_USER, [e], fail_silently=False)
    except:
        print('failed')


@login_required
@unsubscribed_user
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
        u = Users.objects.get(id=pay.invoice_item.invoice.invoice_for.id)
        inform_apprved(u.username, Profile.objects.get(user=u).first_name, pay.invoice_item.invoice.invoice_no, u.email)

        return redirect('req-payment-list')


def inform_rej(u, n, prop, e):
    subject = "Payment for Request invoice {} Rejected".format(prop)
    message = '''
    Dear {}, 
    This email is to let you know that Your payment request has been received and Rejected. Get in touch with your agent/Landlord for more details. 
    Login to your portal at	mnestafrica.com to post another. Your username is  {} incase you had forgotten'''.format(
        n, u)
    try:
        send_mail(subject, message, EMAIL_HOST_USER, [e], fail_silently=False)
    except:
        print('failed')


@unsubscribed_user
@login_required
def list_request(request):
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        comp = CompanyProfile.objects.get(user=request.user).company
        prop = Properties.objects.filter(company=comp).values_list('id', flat=True)
        rent_req = RentInvItemsRequest.objects.filter(invoice_item__invoice__unit__property__in=prop).exclude(
            status=True).exclude(status=False)
        req = InvoiceItemsRequest.objects.filter(invoice_item__invoice__unit__property__in=prop).exclude(
            status=True).exclude(status=False)
        rent_req_past = RentInvItemsRequest.objects.filter(invoice_item__invoice__unit__property__in=prop).exclude(
            status=None).exclude(status='')
        req_past = InvoiceItemsRequest.objects.filter(invoice_item__invoice__unit__property__in=prop).exclude(
            status=None).exclude(status='')
    elif request.user.acc_type.id == 4:
        rent_req = RentInvItemsRequest.objects.filter(invoice_item__invoice__invoice_for=request.user).exclude(
            status=True).exclude(status=False)
        req = InvoiceItemsRequest.objects.filter(invoice_item__invoice__invoice_for=request.user).exclude(
            status=True).exclude(status=False)
        rent_req_past = RentInvItemsRequest.objects.filter(invoice_item__invoice__invoice_for=request.user).exclude(
            status=None).exclude(status='')
        req_past = InvoiceItemsRequest.objects.filter(invoice_item__invoice__invoice_for=request.user).exclude(
            status=None).exclude(status='')

    else:
        raise PermissionDenied

    context = {
        'user': request.user,
        'req': chain(req, rent_req),
        'req_past': chain(rent_req_past, req_past)
    }
    return render(request, 'bills/all_requests.html', context)


@login_required
@unsubscribed_user
def individual_trans(request, uuid):
    rentrec = []
    invrec = []
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        comp = CompanyProfile.objects.get(user=request.user).company
        prop = Properties.objects.filter(company=comp).values_list('id', flat=True)
        rentrec = RentItemTransaction.objects.filter(invoice_item__invoice__uuid=uuid).order_by('created_by')
        invrec = InvoiceItemsTransaction.objects.filter(invoice_item__invoice__uuid=uuid).order_by('created_by')
    if request.user.acc_type.id == 4:
        rentrec = RentItemTransaction.objects.filter(invoice_item__invoice__uuid=uuid).order_by('created_by')
        invrec = InvoiceItemsTransaction.objects.filter(invoice_item__invoice__uuid=uuid).order_by('created_by')

    context = {
        'user': request.user,
        'req': rentrec,
        'rreq': invrec,
    }
    return render(request, 'bills/trans.html', context)


def stkpush(request):
    user = Profile.objects.get(user=request.user)
    prop = Tenant.objects.get(profile=user).unit.property
    company = CompanyProfile.objects.get(company=prop.company, user__acc_type_id__in=[2,3]).user
    inv = RentInvoice.objects.get(uuid=request.POST.get('invoice'))
    print(company)

    landlord = Profile.objects.get(user=company)
    mo  = user.msisdn

    print(landlord.hapokash)
    if user.msisdn.startswith('0'):
        mobile ='254' + user.msisdn[1:]
    elif mo.startswith('1') or mo.startswith('7'):
        mobile = '254' + mo
    elif mo.startswith('+'):
        mobile = mo[1:]
    else:
        mobile = mo

    URL = "https://portal.hapokash.app/api/wallet/top_up"

    headers_dict = {"Accept": "application/json", "Content-Type": "application/json"}
    r = requests.post(url=URL, json={"msisdn": mobile, "amount": request.POST.get('amount'), "account_no": landlord.hapokash}, headers=headers_dict)
    wallet = r.text
    print(wallet)

    return redirect('dashboard')


def stkpushinv(request):
    user = Profile.objects.get(user=request.user)
    prop = Tenant.objects.get(profile=user).unit.property
    company = CompanyProfile.objects.get(company=prop.company, user__acc_type_id__in=[2,3]).user
    inv = Invoice.objects.get(uuid=request.POST.get('invoice'))
    landlord = Profile.objects.get(user=company)

    if user.msisdn.startswith('0'):
        mobile ='254' + user.msisdn[1:]
    else:
        mobile = user.msisdn

    URL = "https://portal.hapokash.app/api/wallet/top_up"

    headers_dict = {"Accept": "application/json", "Content-Type": "application/json"}
    r = requests.post(url=URL, json={"shortcode": "5061001", "msisdn": mobile, "amount": request.POST.get('amount'), "account_no": landlord.hapokash}, headers=headers_dict)
    wallet = r.json()
    print(wallet)
    return HttpResponse('success')


def stkpushtopup(request):
    user = Profile.objects.get(user=request.user)

    if request.POST.get('mobile').startswith('0'):
        mobile ='254' + request.POST.get('mobile')[1:]
    else:
        mobile = request.POST.get('mobile')

    URL = "https://portal.hapokash.app/api/wallet/top_up"
    print(mobile)

    headers_dict = {"Accept": "application/json", "Content-Type": "application/json"}
    r = requests.post(url=URL, json={"shortcode": "5061001", "msisdn": mobile, "amount": request.POST.get('amount'), "account_no": user.hapokash}, headers=headers_dict)
    wallet = r.json()
    print(wallet)
    return HttpResponse('success')


def hapowithdraw(request):
    user = Profile.objects.get(user=request.user)

    if request.POST.get('mobile').startswith('0'):
        mobile ='254' + request.POST.get('mobile')[1:]
    else:
        mobile = request.POST.get('mobile')

    URL = "https://portal.hapokash.app/api/wallet/withdraw"
    print(mobile)

    bod_data = {
        "wallet_id":user.hapokash,
        "amount": request.POST.get('amount'),
        "msisdn":mobile,
        "narration":"Withdrawal to {}".format(mobile)
    }

    headers_dict = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }
    r = requests.post(url=URL, json=bod_data, headers=headers_dict)
    wallet = r.json()
    if not wallet['success'] and wallet['message'] == "Unauthenticated.":
        refreshToken()
        bod_data = {
            "wallet_id": user.hapokash,
            "amount": request.POST.get('amount'),
            "msisdn": mobile,
            "narration": "Withdrawal to {}".format(mobile)
        }

        headers_dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }
        r = requests.post(url=URL, json=bod_data, headers=headers_dict)
        wallet = r.json()
    elif not wallet['success']:
        return HttpResponse(wallet['message'])

    print(wallet)
    return HttpResponse('success')


def stkpushreg(request):
    mobile = request.POST.get('mobile')

    if mobile.startswith('0'):
        mobile ='254' + mobile[1:]

    URL = "https://portal.hapokash.app/api/wallet/top_up"

    headers_dict = {"Accept": "application/json", "Content-Type": "application/json"}
    r = requests.post(url=URL, json={"shortcode": "5061001", "msisdn": mobile, "amount": request.POST.get('amount'), "account_no": 17}, headers=headers_dict)
    wallet = r.json()
    print(wallet)
    # if wallet['success']:
    #     return wallet['transactions']


def confirm_inv_payment(request):
    trans = request.POST.get('trans')
    print(request.POST)
    uuid = request.POST.get('uuid')

    user = Profile.objects.get(user=request.user)
    prop = Tenant.objects.get(profile=user).unit.property
    company = CompanyProfile.objects.get(company=prop.company, user__acc_type_id__in=[2,3]).user
    landlord = Profile.objects.get(user=company)
    print(landlord.hapokash)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }

    URL = "https://portal.hapokash.app/api/wallet/transactions/{}".format(landlord.hapokash)
    r = requests.get(url=URL, headers=headers)
    past_trx =TransactionCodes.objects.filter(trx=trans)
    if past_trx.exists():
        return HttpResponse("exists")
    wallet = r.json()
    print(wallet)
    if wallet['success']:
        search = wallet['transactions']['data']
        # print(search)
        for a in search:
            print(a)
            if a['trx_id'] == trans:
                if add_trans(uuid, a['trx_id'], a['amount'], request.user):
                    past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                    past_trx.save()
                    return HttpResponse("invoice added")
                else:
                    return HttpResponse("wrong")
        if int(wallet['transactions']['last_page']) != 1:
            for i in range(int(trans['last_page']) - 1):
                URL = wallet['transactions']['next_page_url']
                r = requests.get(url=URL, headers=headers)
                wallet = r.json()
                if wallet['success']:
                    search = wallet['transactions']['data']
                    for a in search:
                        if a['trx_id'] == trans:
                            if add_trans(uuid, a['trx_id'], a['amount'], request.user):
                                past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                                past_trx.save()
                                return HttpResponse("invoice added")
                            else:
                                return HttpResponse("Cant save")
    else:
        refreshToken()
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }

        URL = "https://portal.hapokash.app/api/wallet/transactions/{}".format(landlord.hapokash)
        r = requests.get(url=URL, headers=headers)
        wallet = r.json()
        print(wallet)
        if wallet['success']:
            search = wallet['transactions']['data']
            # print(search)
            for a in search:
                print(a)
                if a['trx_id'] == trans:
                    if add_trans(uuid, a['trx_id'], a['amount'], request.user):
                        past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                        past_trx.save()
                        return HttpResponse("invoice added")
                    else:
                        return HttpResponse("Cant save")
            if int(wallet['transactions']['last_page']) != 1:
                for i in range(int(trans['last_page']) - 1):
                    URL = wallet['transactions']['next_page_url']
                    r = requests.get(url=URL, headers=headers)
                    wallet = r.json()
                    if wallet['success']:
                        search = wallet['transactions']['data']
                        for a in search:
                            if a['trx_id'] == trans:
                                if add_trans(uuid, a['trx_id'], a['amount'], request.user):
                                    past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                                    past_trx.save()
                                    return HttpResponse("invoice added")
                                else:
                                    return HttpResponse("wrong")

    return "Not Found"


def add_trans(uuid, trx, am, user):
    trans = InvoiceItemsTransaction.objects.filter(transaction_code=trx)
    trans2 = RentItemTransaction.objects.filter(transaction_code=trx)
    if trans.exists() or trans2.exists():
        return False
    else:
        try:
            inv = Invoice.objects.get(uuid=uuid)
            t = InvoiceItemsTransaction.objects.create(
                invoice_item=InvoiceItems.objects.get(invoice=inv), transaction_code=trx, payment_mode="MPESA", amount_paid=am,
                date_paid=date.today(), created_by=user, created_at=datetime.now()
            )
            t.save()
            return True
        except Invoice.DoesNotExist:
            try:
                inv = RentInvoice.objects.get(uuid=uuid)
                t = RentItemTransaction.objects.create(
                    invoice_item=RentItems.objects.get(invoice=inv), transaction_code=trx, payment_mode="MPESA", amount_paid=am,
                    date_paid=date.today(), created_by=user, created_at=datetime.now()
                )
                t.save()
                return True
            except RentInvoice.DoesNotExist:
                return False


def wallet_transfer(request):
    user = Profile.objects.get(user=request.user)

    URL = "https://portal.hapokash.app/api/wallet/transfer"
    PARAMS = {
        "debit_wallet_id": user.hapokash,
        "credit_wallet_id": request.POST.get('wallet'),
        "amount": request.POST.get('amount'),
        "narration": "Wallet Transfer"
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }
    ra = requests.post(url=URL, json=PARAMS, headers=headers).json()
    print(ra)
    if ra['success']:
        return HttpResponse('success')
    elif not ra['success'] and ra['message'] == "Unauthenticated.":
        refreshToken()
        URL = "https://portal.hapokash.app/api/wallet/transfer"
        PARAMS = {
            "debit_wallet_id": user.hapokash,
            "credit_wallet_id": request.POST.get('wallet'),
            "amount": request.POST.get('amount'),
            "narration": "Wallet Transfer"
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }
        ra = requests.post(url=URL, json=PARAMS, headers=headers).json()
        print(ra)
        if ra['success']:
            return HttpResponse('success')
    else:
        return HttpResponse(ra['message'])


#api
@swagger_auto_schema(method='post', request_body=WalletTopupSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stkpushtopup_api(request):
    user = Profile.objects.get(user=request.user)
    mobile = request.data['mobile']

    if mobile.startswith('0'):
        mobile = '254' + mobile[1:]
    elif mobile.startswith('1') or mobile.startswith('7'):
        mobile = '254' + mobile
    elif mobile.startswith('+'):
        mobile = mobile[1:]

    URL = "https://portal.hapokash.app/api/wallet/top_up"

    headers_dict = {"Accept": "application/json", "Content-Type": "application/json"}
    r = requests.post(url=URL, json={"shortcode": "5061001", "msisdn": mobile, "amount": request.data['amount'], "account_no": user.hapokash}, headers=headers_dict)
    wallet = r.json()
    print(wallet)
    return Response(wallet, status.HTTP_200_OK)


@swagger_auto_schema(method='post', request_body=WalletWithdrawSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hapowithdraw_api(request):
    user = Profile.objects.get(user=request.user)
    mobile = request.data['mobile']

    if mobile.startswith('0'):
        mobile = '254' + mobile[1:]
    elif mobile.startswith('1') or mobile.startswith('7'):
        mobile = '254' + mobile
    elif mobile.startswith('+'):
        mobile = mobile[1:]

    URL = "https://portal.hapokash.app/api/wallet/withdraw"
    print(mobile)

    bod_data = {
        "wallet_id":user.hapokash,
        "amount": request.data['amount'],
        "msisdn":mobile,
        "narration":"Withdrawal to {}".format(mobile)
    }

    headers_dict = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }
    r = requests.post(url=URL, json=bod_data, headers=headers_dict)
    wallet = r.json()
    if not wallet['success'] and wallet['message'] == "Unauthenticated.":
        refreshToken()
        bod_data = {
            "wallet_id": user.hapokash,
            "amount": request.POST.get('amount'),
            "msisdn": mobile,
            "narration": "Withdrawal to {}".format(mobile)
        }

        headers_dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }
        r = requests.post(url=URL, json=bod_data, headers=headers_dict)
        wallet = r.json()
    elif not wallet['success']:
        return HttpResponse(wallet['message'])

    print(wallet)
    return Response(wallet, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wall_trans_api(request):
    prof = Profile.objects.get(user=request.user)

    if prof.hapokash is None:
        wal_id = hapokashcreate()
        try:
            if wal_id['success']:
                prof.hapokash = wal_id['wallet']['id']
                prof.save()
            else:
                print('false')
        except:
            print(wal_id)

    URL = "https://portal.hapokash.app/api/wallet/details/{}".format(prof.hapokash)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }

    r = requests.get(url=URL, headers=headers)
    print(r.json())
    wallet = r.json()

    if wallet['success']:
        cur_balance = wallet['wallet']['current_balance']
        pre_balance = wallet['wallet']['previous_balance']
    elif not wallet['success'] and wallet['message'] == "Unauthenticated.":
        refreshToken()
        URL = "https://portal.hapokash.app/api/wallet/details/{}".format(prof.hapokash)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }

        r = requests.get(url=URL, headers=headers)
        wallet = r.json()

        if wallet['success']:
            cur_balance = wallet['wallet']['current_balance']
            pre_balance = wallet['wallet']['previous_balance']
        else:
            cur_balance = 0
            pre_balance = 0
    else:
        cur_balance = 0
        pre_balance = 0

    trans = wallet_trans(prof.hapokash)
    print(trans)
    if trans['last_page'] != 1:
        URL = trans['next_page_url']
        for i in range(trans['last_page'] - 1):
            print(trans['next_page_url'])
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
            }

            r = requests.get(url=URL, headers=headers)
            wallet = r.json()
            print(wallet)
            if wallet['success']:
                trans['data'] = trans['data'] + wallet['transactions']['data']
            elif not wallet['success'] and wallet['message'] == "Unauthenticated.":
                refreshToken()
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
                }

                r = requests.get(url=URL, headers=headers)
                wallet = r.json()
                print(wallet)
                if wallet['success']:
                    trans['data'] = trans['data'] + wallet['transactions']['data']
            URL = wallet['transactions']['next_page_url']

    for d in trans['data']:
        d.update((k, datetime.strptime(
            '{} {}'.format(v.split('T')[0], v.split('T')[1].split('.')[0]), '%Y-%m-%d %H:%M:%S'
        ).strftime('%d/%B/%Y, %H:%M:%S')) for k, v in d.items() if k == "created_at")

    context = {
        'success': True,
        'trans': trans['data']
    }
    return Response(context, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wall_details_api(request):
    prof = Profile.objects.get(user=request.user)

    if prof.hapokash is None:
        wal_id = hapokashcreate()
        try:
            if wal_id['success']:
                prof.hapokash = wal_id['wallet']['id']
                prof.save()
            else:
                print('false')
        except:
            print(wal_id)

    URL = "https://portal.hapokash.app/api/wallet/details/{}".format(prof.hapokash)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }

    r = requests.get(url=URL, headers=headers)
    print(r.json())
    wallet = r.json()

    if wallet['success']:
        cur_balance = wallet['wallet']['current_balance']
        pre_balance = wallet['wallet']['previous_balance']
    elif not wallet['success'] and wallet['message'] == "Unauthenticated.":
        refreshToken()
        URL = "https://portal.hapokash.app/api/wallet/details/{}".format(prof.hapokash)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }

        r = requests.get(url=URL, headers=headers)
        wallet = r.json()

        if wallet['success']:
            cur_balance = wallet['wallet']['current_balance']
            pre_balance = wallet['wallet']['previous_balance']
        else:
            cur_balance = 0
            pre_balance = 0
    else:
        cur_balance = 0
        pre_balance = 0

    context = {
        'cur_balance': cur_balance,
        'previous_balance': pre_balance
    }
    return Response(wallet, status.HTTP_200_OK)


@swagger_auto_schema(method='post', request_body=WalletBalanceSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def wall_details_api_test(request):
    prof = Profile.objects.get(user=request.user)

    if not check_password(request.data.get('password'), Users.objects.get(id=request.user.id).password):
        raise PermissionDenied

    if prof.hapokash is None:
        wal_id = hapokashcreate()
        try:
            if wal_id['success']:
                prof.hapokash = wal_id['wallet']['id']
                prof.save()
            else:
                print('false')
        except:
            print(wal_id)

    URL = "https://portal.hapokash.app/api/wallet/details/{}".format(prof.hapokash)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }

    r = requests.get(url=URL, headers=headers)
    print(r.json())
    wallet = r.json()

    if wallet['success']:
        cur_balance = wallet['wallet']['current_balance']
        pre_balance = wallet['wallet']['previous_balance']
    elif not wallet['success'] and wallet['message'] == "Unauthenticated.":
        refreshToken()
        URL = "https://portal.hapokash.app/api/wallet/details/{}".format(prof.hapokash)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }

        r = requests.get(url=URL, headers=headers)
        wallet = r.json()

        if wallet['success']:
            cur_balance = wallet['wallet']['current_balance']
            pre_balance = wallet['wallet']['previous_balance']
        else:
            cur_balance = 0
            pre_balance = 0
    else:
        cur_balance = 0
        pre_balance = 0

    context = {
        'cur_balance': cur_balance,
        'previous_balance': pre_balance
    }
    return Response(wallet, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def open_rent_bills_api(request):
    tenant = Tenant.objects.get(profile__user=request.user)
    r_invoice = RentInvoice.objects.filter(invoice_for=tenant.profile.user, status=False)

    r_inv_item = RentItems.objects.filter(invoice__in=r_invoice)
    r_inv_tran = RentItemTransaction.objects.filter(invoice_item__in=r_inv_item)


    r_bals = 0
    for due in r_inv_item:
        r_bals = due.amount + r_bals + due.delay_penalties

    for due in r_inv_tran:
        r_bals = r_bals - due.amount_paid

    r_bals = '{0:,}'.format(r_bals)

    r = []
    for inv in r_invoice:
        total = 0
        paid = 0
        pen = 0
        r_inv_items = RentItems.objects.filter(invoice=inv)
        for i in r_inv_items:
            total = total + i.amount + i.delay_penalties
            trans = RentItemTransaction.objects.filter(invoice_item=i)
            pen = i.delay_penalties
            for ab in trans:
                paid = ab.amount_paid + paid

        r.append({
            'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
            'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
            'created_at': inv.created_at, 'paid': paid, "status": inv.status, "penalties": pen
        })
    context = {
        'success':True,
        'data': r,
        'total_due': r_bals
    }
    return Response(context, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def closed_rent_bills_api(request):
    tenant = Tenant.objects.get(profile__user=request.user)
    r_invoice = RentInvoice.objects.filter(invoice_for=tenant.profile.user, status=True)
    r = []
    for inv in r_invoice:
        total = 0
        paid = 0
        r_inv_items = RentItems.objects.filter(invoice=inv)
        for i in r_inv_items:
            total = total + i.amount + i.delay_penalties
            trans = RentItemTransaction.objects.filter(invoice_item=i)
            for ab in trans:
                paid = ab.amount_paid + paid

        r.append({
            'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
            'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
            'created_at': inv.created_at, 'paid': paid, "status": inv.status
        })
    context = {
        'success':True,
        'data': r,
    }
    return Response(context, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def open_invoice_bills_api(request):
    tenant = Tenant.objects.get(profile__user=request.user)
    invoice = Invoice.objects.filter(invoice_for=tenant.profile.user, status=False)

    inv_item = InvoiceItems.objects.filter(invoice__in=invoice)
    inv_tran = InvoiceItemsTransaction.objects.filter(invoice_item__in=inv_item)


    bals = 0
    for due in inv_item:
        bals = due.amount + bals

    for due in inv_tran:
        bals = bals - due.amount_paid

    bals = '{0:,}'.format(bals)

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
    context = {
        "success": True,
        'data': a,
        'total_due': bals
    }
    return Response(context, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def closed_invoice_bills_api(request):
    tenant = Tenant.objects.get(profile__user=request.user)
    invoice = Invoice.objects.filter(invoice_for=tenant.profile.user, status=True)
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
    context = {
        "success": True,
        'data': a
    }
    return Response(context, status.HTTP_200_OK)


@swagger_auto_schema(method='post', request_body=PayInvPaySerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inv_payment_api(request):

    user = Profile.objects.get(user=request.user)
    prop = Tenant.objects.get(profile=user).unit.property
    company = CompanyProfile.objects.get(company=prop.company, user__acc_type_id__in=[2,3]).user
    landlord = Profile.objects.get(user=company)
    mobile = user.msisdn

    if mobile.startswith('0'):
        mobile = '254' + mobile[1:]
    elif mobile.startswith('1') or mobile.startswith('7'):
        mobile = '254' + mobile
    elif mobile.startswith('+'):
        mobile = mobile[1:]

    URL = "https://portal.hapokash.app/api/wallet/top_up"
    print(landlord.hapokash)

    headers_dict = {"Accept": "application/json", "Content-Type": "application/json"}
    r = requests.post(url=URL, json={"shortcode": "5061001", "msisdn": mobile, "amount": request.data['amount'], "account_no": landlord.hapokash}, headers=headers_dict)
    wallet = r.json()
    print(wallet)
    return Response(wallet)


@swagger_auto_schema(method='post', request_body=ConfInvPaySerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def conf_inv_pay_api(request):
    trans = request.data['trans']
    uuid = request.data['inv_uuid']

    user = Profile.objects.get(user=request.user)
    prop = Tenant.objects.get(profile=user).unit.property
    company = CompanyProfile.objects.get(company=prop.company, user__acc_type_id__in=[2,3]).user
    landlord = Profile.objects.get(user=company)
    print(landlord.hapokash)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }

    URL = "https://portal.hapokash.app/api/wallet/transactions/{}".format(landlord.hapokash)
    r = requests.get(url=URL, headers=headers)
    past_trx =TransactionCodes.objects.filter(trx=trans)
    if past_trx.exists():
        return Response({'success':False, 'message': "Transaction code already used"}, status.HTTP_401_UNAUTHORIZED)
    wallet = r.json()
    print(wallet)
    if wallet['success']:
        search = wallet['transactions']['data']
        # print(search)
        for a in search:
            print(a)
            if a['trx_id'] == trans:
                if add_trans(uuid, a['trx_id'], a['amount'], request.user):
                    past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                    past_trx.save()
                    return Response({'success':True, 'message': "Transaction successfully confirmed"}, status.HTTP_200_OK)
                else:
                    return Response({'success':False, 'message': "Try again"}, status.HTTP_400_BAD_REQUEST)
        if int(wallet['transactions']['last_page']) != 1:
            for i in range(int(trans['last_page']) - 1):
                URL = wallet['transactions']['next_page_url']
                r = requests.get(url=URL, headers=headers)
                wallet = r.json()
                if wallet['success']:
                    search = wallet['transactions']['data']
                    for a in search:
                        if a['trx_id'] == trans:
                            if add_trans(uuid, a['trx_id'], a['amount'], request.user):
                                past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                                past_trx.save()
                                return Response({'success':True, 'message': "Transaction successfully confirmed"}, status.HTTP_200_OK)
                            else:
                                return Response({'success':False, 'message': "Try again"}, status.HTTP_400_BAD_REQUEST)
    else:
        refreshToken()
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }

        URL = "https://portal.hapokash.app/api/wallet/transactions/{}".format(landlord.hapokash)
        r = requests.get(url=URL, headers=headers)
        wallet = r.json()
        print(wallet)
        if wallet['success']:
            search = wallet['transactions']['data']
            # print(search)
            for a in search:
                print(a)
                if a['trx_id'] == trans:
                    if add_trans(uuid, a['trx_id'], a['amount'], request.user):
                        past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                        past_trx.save()
                        return Response({'success':True, 'message': "Transaction successfully confirmed"}, status.HTTP_200_OK)
                    else:
                        return Response({'success':False, 'message': "Try again"}, status.HTTP_400_BAD_REQUEST)
            if int(wallet['transactions']['last_page']) != 1:
                for i in range(int(trans['last_page']) - 1):
                    URL = wallet['transactions']['next_page_url']
                    r = requests.get(url=URL, headers=headers)
                    wallet = r.json()
                    if wallet['success']:
                        search = wallet['transactions']['data']
                        for a in search:
                            if a['trx_id'] == trans:
                                if add_trans(uuid, a['trx_id'], a['amount'], request.user):
                                    past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                                    past_trx.save()
                                    return Response({'success':True, 'message': "Transaction successfully confirmed"}, status.HTTP_200_OK)
                                else:
                                    return Response({'success':False, 'message': "Try again"}, status.HTTP_400_BAD_REQUEST)

    return Response({'success':False, 'message': "Transaction Not Found"}, status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', request_body=WallPaySerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_inv_wallet_api(request):
    user = Profile.objects.get(user=request.user)
    try:
        invoice = Invoice.objects.get(uuid=request.data['inv_uuid'])
        prop = Tenant.objects.get(profile=user).unit.property
        company = CompanyProfile.objects.get(company=prop.company, user__acc_type_id__in=[2, 3]).user
        landlord = Profile.objects.get(user=company)

        URL = "https://portal.hapokash.app/api/wallet/transfer"
        PARAMS = {
            "debit_wallet_id": user.hapokash,
            "credit_wallet_id": landlord.hapokash,
            "amount": request.data['amount'],
            "narration": "Payment For Invoice From wallet"
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }
        r = requests.post(url=URL, json=PARAMS, headers=headers).json()

        if r['success']:
            pay = InvoiceItemsTransaction.objects.create(
                invoice_item=InvoiceItems.objects.get(invoice=invoice), amount_paid=request.data['amount'],
                payment_mode="Wallet Transfer",
                remarks="Payment For Invoice From wallet", date_paid=date.today(), created_by=request.user
            )
            pay.save()
            return Response({'success':True, 'message': "Transaction successful"}, status.HTTP_200_OK)
        elif not r['success'] and r['message'] == "Unauthenticated.":
            URL = "https://portal.hapokash.app/api/wallet/transfer"
            PARAMS = {
                "debit_wallet_id": user.hapokash,
                "credit_wallet_id": landlord.hapokash,
                "amount": request.data['amount'],
                "narration": "Payment For Invoice From wallet"
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
            }
            r = requests.post(url=URL, json=PARAMS, headers=headers).json()

            if r['success']:
                pay = InvoiceItemsTransaction.objects.create(
                    invoice_item=InvoiceItems.objects.get(invoice=invoice), amount_paid=request.data['amount'],
                    payment_mode="Wallet Transfer",
                    remarks="Payment For Invoice From wallet", date_paid=date.today(), created_by=request.user
                )
                pay.save()
                return Response({'success':True, 'message': "Transaction successful"}, status.HTTP_200_OK)
        else:
            return Response(r)

    except Invoice.DoesNotExist:
        invoice = RentInvoice.objects.get(uuid=request.data['inv_uuid'])

        prop = Tenant.objects.get(profile=user).unit.property
        company = CompanyProfile.objects.get(company=prop.company, user__acc_type_id__in=[2, 3]).user
        landlord = Profile.objects.get(user=company)

        URL = "https://portal.hapokash.app/api/wallet/transfer"
        PARAMS = {
            "debit_wallet_id": user.hapokash,
            "credit_wallet_id": landlord.hapokash,
            "amount": request.data['amount'],
            "narration": "Payment For Invoice From wallet"
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }
        r = requests.post(url=URL, json=PARAMS, headers=headers).json()

        if r['success']:
            pay = RentItemTransaction.objects.create(
                invoice_item=RentItems.objects.get(invoice=invoice), amount_paid=request.data['amount'],
                payment_mode="Wallet Transfer",
                remarks="Payment For Invoice From wallet", date_paid=date.today(), created_by=request.user
            )
            pay.save()
            return Response({'success':True, 'message': "Transaction successful"}, status.HTTP_200_OK)
        elif not r['success'] and r['message'] == "Unauthenticated.":
            URL = "https://portal.hapokash.app/api/wallet/transfer"
            PARAMS = {
                "debit_wallet_id": user.hapokash,
                "credit_wallet_id": landlord.hapokash,
                "amount": request.data['amount'],
                "narration": "Payment For Invoice From wallet"
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
            }
            r = requests.post(url=URL, json=PARAMS, headers=headers).json()

            if r['success']:
                pay = RentItemTransaction.objects.create(
                    invoice_item=RentItems.objects.get(invoice=invoice), amount_paid=request.data['amount'],
                    payment_mode="Wallet Transfer",
                    remarks="Payment For Invoice From wallet", date_paid=date.today(), created_by=request.user
                )
                pay.save()
                return Response({'success':True, 'message': "Transaction successful"}, status.HTTP_200_OK)
        else:
            return Response(r)
    except Exception as e:
        print(e)

    return Response({'success':False, 'message': "Something went wrong, Try again later"}, status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', request_body=TransSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inv_trans_api(request):
    uuid = request.data['uuid']
    rentrec = RentItemTransaction.objects.filter(invoice_item__invoice__uuid=uuid).order_by('created_by')
    invrec = InvoiceItemsTransaction.objects.filter(invoice_item__invoice__uuid=uuid).order_by('created_by')
    if invrec.exists():
        ser = InvTransSerializer(invrec, many=True)
        return Response({'success': True, 'data': ser.data}, status.HTTP_200_OK)
    elif rentrec.exists():
        ser = RentTransSerializer(rentrec, many=True)
        return Response({'success': True, 'data': ser.data}, status.HTTP_200_OK)
    else:
        return Response({'success': False, 'data': "No transactions found"}, status.HTTP_200_OK)

