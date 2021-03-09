import calendar
import datetime
import os
import uuid

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login as log_in, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail, BadHeaderError
from django.db.models import Count, Sum, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from psycopg2._psycopg import IntegrityError

from authapp.decorators import unsubscribed_user
from authapp.forms import LoginForm
from authapp.models import *
from bills.models import *
from properties.models import Companies, CompanyProfile, Tenant, SubscriptionsCompanies, Properties, BankAcc, \
    PaymentPaybill, PaymentTill, TransactionCodes
from tree_house import settings


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        print(form.is_valid())
        if form.is_valid():
            clean = form.cleaned_data
            user = authenticate(username=clean['username'], password=clean['password'])
            chus = Users.objects.get(username=clean['username'])
            if not chus.is_active:
                return HttpResponse('Account is Disabled')
            if chus.acc_type_id == 2 or chus.acc_type_id == 3:
                cp = CompanyProfile.objects.get(user=chus).company
            if user is not None:
                if user.is_active:
                    log_in(request, user)
                    return HttpResponse(reverse('dashboard'))
                else:
                    return HttpResponse('Account is Disabled')
            else:
                return HttpResponse("invalid credentials")
        else:
            return HttpResponse("form error")
    else:
        form = LoginForm()
    return render(request, "authapp/login-v3.html", {'form': form})


@login_required
@unsubscribed_user
def dashboard(request):
    user = request.user
    if user.acc_type.id == 4:
        prof = Profile.objects.get(user=user)

        term = open(os.path.join(settings.MEDIA_ROOT, 'terms.txt'), "r").read()
        privacy = open(os.path.join(settings.MEDIA_ROOT, 'privacy.txt'), "r").read()
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

        wallet = r.json()
        print(wallet)

        if wallet['success']:
            cur_balance = wallet['wallet']['current_balance']
        else:
            refreshToken()

            URL = "https://portal.hapokash.app/api/wallet/details/{}".format(prof.hapokash)
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
            }
            r = requests.get(url=URL, headers=headers)

            wallet = r.json()
            print(wallet)

            if wallet['success']:
                cur_balance = wallet['wallet']['current_balance']

            # return HttpResponse(wallet)

        tenant = Tenant.objects.get(profile=prof)
        bank_ac = BankAcc.objects.filter(prop__prop=tenant.unit.property)
        paybill_ac = PaymentPaybill.objects.filter(prop__prop=tenant.unit.property)
        till_ac = PaymentTill.objects.filter(prop__prop=tenant.unit.property)

        invoice = Invoice.objects.filter(invoice_for=user, status=False)
        inv_item = InvoiceItems.objects.filter(invoice__in=invoice)
        inv_tran = InvoiceItemsTransaction.objects.filter(invoice_item__in=inv_item)

        r_invoice = RentInvoice.objects.filter(invoice_for=user, status=False)
        r_inv_item = RentItems.objects.filter(invoice__in=r_invoice)
        r_inv_tran = RentItemTransaction.objects.filter(invoice_item__in=r_inv_item)

        bals = 0
        for due in inv_item:
            bals = due.amount + bals

        for due in inv_tran:
            bals = bals - due.amount_paid

        bals = '{0:,}'.format(bals)

        r_bals = 0
        for due in r_inv_item:
            r_bals = due.amount + r_bals + due.delay_penalties

        for due in r_inv_tran:
            r_bals = r_bals - due.amount_paid

        r_bals = '{0:,}'.format(r_bals)
        context = {
            'user': user,
            'prof': prof,
            'tenant': tenant,
            'bals': bals,
            'r_bals': r_bals,
            'inv': invoice.count() + r_invoice.count(),
            'bank': bank_ac,
            'paybills': paybill_ac,
            'tills': till_ac,
            'invoice': invoice,
            'rent_invoices': r_invoice,
            "cur_balance": cur_balance,
            'terms': term, 'privacy': privacy
        }
        return render(request, 'authapp/tenant_dash.html', context)

    elif user.acc_type.id == 1:
        sub = SubscriptionsCompanies.objects.values('subs__name').annotate(c=Count('subs__name')).order_by('-c')
        active_u = Users.objects.all()
        sub_c = SubscriptionsCompanies.objects.filter(date_end__gte=datetime.date.today()).distinct('company_id')
        context = {
            'user': user,
            'subs': sub,
            'land': active_u.filter(acc_type_id=2).count(),
            'ag': active_u.filter(acc_type_id=3).count(),
            'staff': active_u.filter(acc_type_id=5).count(),
            'tena': active_u.filter(acc_type_id=4).count(),
            'subcomp': sub_c,
        }
        return render(request, 'authapp/Super_analytics.html', context)

    elif user.acc_type.id == 2 or user.acc_type.id == 3:

        if request.POST.get('month') == None:
            month = datetime.date.today().month
            year = datetime.date.today().year
        else:
            year = request.POST.get('month').split('-')[0]
            month = request.POST.get('month').split('-')[1]

        prop = Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company)
        unit = Unit.objects.filter(property__in=prop)

        inv = RentInvoice.objects.filter(unit__in=unit, date_due__year=year, date_due__month=month)
        items = RentItems.objects.filter(invoice__in=inv)
        print(inv)
        print(request.POST.get('month'))
        print(month)
        invoice = RentInvoice.objects.filter(unit__in=unit, date_due__year=year, date_due__month=month)
        paid = RentItemTransaction.objects.filter(invoice_item__invoice__status=True,
                                                  invoice_item__invoice__in=invoice).aggregate(Sum('amount_paid'))
        unpaid1 = RentItemTransaction.objects.filter(invoice_item__invoice__status=False,
                                                     invoice_item__invoice__in=invoice).aggregate(Sum('amount_paid'))
        unpaid = RentItems.objects.filter(invoice__status=False, invoice__in=invoice).aggregate(Sum('amount'))

        print(unpaid)
        #
        pec1 = inv.filter(status=True)
        pec2 = inv.filter(status=False)
        unp = Unit.objects.filter(id__in=pec2.values_list('unit_id', flat=True))

        req = RentInvItemsRequest.objects.filter(invoice_item__in=items)
        oreq = InvoiceItemsRequest.objects.filter(invoice_item__in=InvoiceItems.objects.filter(invoice__unit__in=unit),
                                                  created_at__month=month, created_at__year=year)

        if paid['amount_paid__sum'] == None:
            paid['amount_paid__sum'] = 0
        if unpaid1['amount_paid__sum'] == None:
            unpaid1['amount_paid__sum'] = 0
        if unpaid['amount__sum'] == None:
            unpaid['amount__sum'] = 0

        context = {
            'user': user,
            'total_units': unit.count(),
            'vacant': unit.filter(unit_status="Vacant").count(),
            'occ': unit.filter(unit_status="Occupied").count(),
            'open': inv.filter(status=False).count(),
            'due': inv.filter(status=False).count(),
            'pec1': pec1.count(),
            'pec2': pec2.count(),
            'all_inv': inv.count(),
            'unpunits': unp.count(),
            'req': req.count(),
            'oreq': oreq.count(),
            'date_now': '{}-{}'.format(year, str('%02d' % int(month))),
            'paid': paid['amount_paid__sum'] + unpaid1['amount_paid__sum'],
            'due_to_pay': unpaid['amount__sum'] - unpaid1['amount_paid__sum'],
        }

        return render(request, 'authapp/analytics.html', context)
    elif user.acc_type.id == 5:
        prop = Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company)
        unit = Unit.objects.filter(property__in=prop)
        # print(unit)
        paid = 0
        inv = RentInvoice.objects.filter(unit__in=unit)
        items = RentItems.objects.filter(invoice__in=inv)
        print(inv)

        # to_pay = items.aggregate(Sum('amount'))['amount__sum'] + items.aggregate(Sum('amount'))['amount__sum']
        # for item in items:
        #     p = RentItemTransaction.objects.filter(invoice_item=item).aggregate(Sum('amount_paid'))
        #     print(p)
        #     paid = paid + p['amount_paid__sum']
        pec1 = inv.filter(status=True)
        pec2 = inv.filter(status=False)
        unp = Unit.objects.filter(id__in=pec2.values_list('unit_id', flat=True))

        req = RentInvItemsRequest.objects.filter(invoice_item__in=items)
        oreq = InvoiceItemsRequest.objects.filter(invoice_item__in=InvoiceItems.objects.filter(invoice__unit__in=unit))

        context = {
            'user': user,
            'total_units': unit.count(),
            'vacant': unit.filter(unit_status="Vacant").count(),
            'occ': unit.filter(unit_status="Occupied").count(),
            'open': inv.filter(status=False).count(),
            'due': inv.filter(status=False).count(),
            'pec1': pec1.count(),
            'pec2': pec2.count(),
            'all_inv': inv.count(),
            'unpunits': unp.count(),
            'req': req.count(),
            'oreq': oreq.count(),

        }

        return render(request, 'authapp/analytics.html', context)


@login_required
@unsubscribed_user
def suspend_user(request, uid):
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        user = Users.objects.get(id=uid)
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.save()
        return redirect('company_staff')

    if not request.user.acc_type.id == 1:
        raise PermissionDenied
    user = Users.objects.get(id=uid)
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    user.save()
    return redirect('all-users')


@csrf_exempt
def rent_hapo_pay(request):
    prof = Profile.objects.get(user=request.user)
    tenant = Tenant.objects.get(profile=prof)
    bank_ac = BankAcc.objects.filter(prop__prop=tenant.unit.property)
    paybill_ac = PaymentPaybill.objects.filter(prop__prop=tenant.unit.property)
    till_ac = PaymentTill.objects.filter(prop__prop=tenant.unit.property)
    cp = CompanyProfile.objects.get()

    invoice = Invoice.objects.filter(invoice_for=request, status=False)
    inv_item = InvoiceItems.objects.filter(invoice__in=invoice)
    inv_tran = InvoiceItemsTransaction.objects.filter(invoice_item__in=inv_item)
    return redirect('all-users')


@login_required
def delete_user(request, uid):
    if not request.user.acc_type.id == 1:
        raise PermissionDenied
    user = Users.objects.get(id=uid)
    user.delete()
    return redirect('all-users')


@login_required
def suspend_company(request, uid):
    if not request.user.acc_type.id == 1:
        raise PermissionDenied
    company = Companies.objects.get(id=uid)
    cp = CompanyProfile.objects.filter(company=company)
    for c in cp:
        user = Users.objects.get(id=c.user.id)
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.save()

    return redirect('all-companies')


@login_required
@csrf_exempt
def delete_company(request, uid):
    if not request.user.acc_type.id == 1:
        raise PermissionDenied
    company = Companies.objects.get(id=uid)
    cp = CompanyProfile.objects.filter(company=company)
    for c in cp:
        user = Users.objects.get(id=c.user.id)
        user.delete()
    company.delete()
    cp.delete()

    return redirect('all-companies')


@login_required
@unsubscribed_user
def profile(request):
    user = request.user
    if user.acc_type.id == 4:
        profile = Profile.objects.get(user=user)
        tenant = Tenant.objects.get(profile=profile)

        events = [
            {
                'time': tenant.date_occupied,
                'event': "unit occupied",
                'days': (datetime.date.today() - tenant.date_occupied.date()).days
            },
            {
                'time': tenant.created_at,
                'event': "unit assigned",
                'days': (datetime.date.today() - tenant.created_at.date()).days
            },
        ]
        inv = Invoice.objects.filter(invoice_for=user)
        for i in inv:
            events.insert(0, {
                'time': i.created_at,
                'event': 'invoice {} created'.format(i.invoice_no),
                'days': (datetime.date.today() - i.created_at.date()).days

            })
        if request.method == "POST":
            if not request.user.check_password(request.POST.get('password')):
                return HttpResponse("wrong password")
            profile.first_name = request.POST.get('f_name')
            profile.last_name = request.POST.get('l_name')
            profile.msisdn = request.POST.get('msisdn')
            profile.id_number = request.POST.get('id_no')

            tenant.secondary_msisdn = request.POST.get('sec_msisdn')

            profile.save()
            tenant.save()

        context = {
            'user': user,
            'profile': profile,
            'ten': tenant,
            'timeline': sorted(events, key=lambda i: (i['days'])),
        }

    elif user.acc_type.id == 1:
        context = {
            'user': user,
        }

    elif user.acc_type.id == 3 or user.acc_type.id == 2:
        profile = Profile.objects.get(user=user)
        comp = CompanyProfile.objects.get(user=profile.user)
        subs = SubscriptionsCompanies.objects.filter(company=comp.company).order_by('date_end')[0]

        if request.method == "POST":
            if not request.user.check_password(request.POST.get('password')):
                return HttpResponse("wrong password")
            profile.first_name = request.POST.get('f_name')
            profile.last_name = request.POST.get('l_name')

            profile.save()

        context = {
            'user': user,
            'profile': profile,
            'comp': comp,
            'subs': subs,
        }

        return render(request, 'authapp/companyprofile.html', context)

    else:
        context = {
            'user': user,
        }
        return render(request, 'authapp/companyprofile.html', context)

    return render(request, 'authapp/profile.html', context)


@csrf_exempt
def check_username(request):
    print(request.POST)
    username = request.POST.get('username')

    query = Users.objects.filter(username=username)

    response = "<span id='resp' style='color: green;'>Available.</span>"
    if query.count() > 0:
        response = "<span id='resp' style='color: red;'>Username Not Available.</span>"

    return HttpResponse(response)


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'authapp/change_pass.html', {
        'form': form
    })


def signup(request):
    sub = Subscriptions.objects.filter(is_active=True)
    term = open(os.path.join(settings.MEDIA_ROOT, 'terms.txt'), "r").read()
    privacy = open(os.path.join(settings.MEDIA_ROOT, 'privacy.txt'), "r").read()
    # privacy = open("../media/privacy.txt", "r")
    # print(term.readlines())
    if request.method == "POST":
        print(request.POST)
        username = request.POST.get('username')
        email = request.POST.get('email')
        pwrd = request.POST.get('password')
        f_name = request.POST.get('f_name')
        l_name = request.POST.get('l_name')
        terms = request.POST.get('terms')
        company_name = request.POST.get('company')
        no_of_units = request.POST.get('props_no')
        type = request.POST.get('acc_type')
        number = request.POST.get('id_no')
        location = request.POST.get('location')
        sub_picked = request.POST.get('sub_picked')
        if request.POST.get('mobile') == '':
            mobile = request.POST.get('mobile2')
        else:
            mobile = request.POST.get('mobile')

        if request.FILES:
            logo = request.FILES['logo']
        else:
            logo = ''
        try:
            if Users.objects.filter(username=username).exists():
                return HttpResponse("Username already exists")
            acc = AccTypes.objects.get(id=int(type))
            user = Users.objects.create_user(username=username, password=pwrd, email=email, acc_type=acc)
            user.save()

            if user.pk:
                profile = Profile.objects.create(first_name=f_name, last_name=l_name, msisdn=mobile, id_number=number,
                                                 terms_accepted=terms, user=user)
                profile.save()

                if int(type) == 3:
                    company = Companies.objects.create(name=company_name, no_of_emp=no_of_units, location=location,
                                                       logo=logo)
                    company.save()
                elif int(type) == 2:
                    company = Companies.objects.create(name=mobile)
                    company.save()

                cp = CompanyProfile.objects.create(user=user, company=company)
                cp.save()

                stkpushreg(mobile, Subscriptions.objects.get(uuid=sub_picked).value)

                wal_id = hapokashcreate()
                try:
                    if wal_id['success']:
                        profile.hapokash = wal_id['wallet']['id']
                        profile.save()
                    else:
                        print('false')
                except:
                    print(wal_id)

        except Exception  as e:
            raise e

        return redirect('web-login')
    return render(request, 'authapp/register.html', {'sub': sub, 'terms': term, 'privacy': privacy})


def hapokashcreate():
    URL = "https://portal.hapokash.app/api/wallet/create"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }
    PARAMS = {"currency": "KES"}
    r = requests.post(url=URL, data=PARAMS, headers=headers)
    if r.json()['success']:
        return r.json()
    else:
        refreshToken()
        URL = "https://portal.hapokash.app/api/wallet/create"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }
        PARAMS = {"currency": "KES"}
        r = requests.post(url=URL, data=PARAMS, headers=headers)
        if r.json()['success']:
            return r.json()


def refreshToken():
    url = "https://portal.hapokash.app/oauth/token"

    payload = "{\"grant_type\":\"client_credentials\",\"client_id\":\"3\",\"client_secret\":\"MpZsUna0SwG23iZS4dVVXQLdBcb1Y8KVplVz5Wri\"}"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload).json()
    at = AuthTokens.objects.get(id=1)
    at.auth = response['access_token']
    at.save()


def hapokash_wallet_transfer(request):
    user = Profile.objects.get(user=request.user)
    invoice = RentInvoice.objects.get(uuid=request.POST.get('invoice'))

    prop = Tenant.objects.get(profile=user).unit.property
    company = CompanyProfile.objects.get(company=prop.company, user__acc_type_id__in=[2, 3]).user
    landlord = Profile.objects.get(user=company)

    URL = "https://portal.hapokash.app/api/wallet/transfer"
    PARAMS = {
        "debit_wallet_id": user.hapokash,
        "credit_wallet_id": landlord.hapokash,
        "amount": request.POST.get('amount'),
        "narration": "Payment For Rent From wallet"
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }
    ra = requests.post(url=URL, json=PARAMS, headers=headers).json()
    print(ra)
    if ra['success']:
        pay = RentItemTransaction.objects.create(
            invoice_item=RentItems.objects.get(invoice=invoice), amount_paid=request.POST.get('amount'),
            payment_mode="Wallet Transfer",
            remarks="Payment For Rent From wallet", date_paid=datetime.date.today(), created_by=request.user
        )
        pay.save()
    elif not ra['success'] and ra['message'] == "Unauthenticated.":
        refreshToken()
        URL = "https://portal.hapokash.app/api/wallet/transfer"
        PARAMS = {
            "debit_wallet_id": user.hapokash,
            "credit_wallet_id": landlord.hapokash,
            "amount": request.POST.get('amount'),
            "narration": "Payment For Rent From wallet"
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }
        ra = requests.post(url=URL, json=PARAMS, headers=headers).json()
        print(ra)
        if ra['success']:
            pay = RentItemTransaction.objects.create(
                invoice_item=RentItems.objects.get(invoice=invoice), amount_paid=request.POST.get('amount'),
                payment_mode="Wallet Transfer",
                remarks="Payment For Rent From wallet", date_paid=datetime.date.today(), created_by=request.user
            )
            pay.save()
    return redirect('dashboard')


def hapokash_wallet_transfer_Inv(request):
    user = Profile.objects.get(user=request.user)
    invoice = Invoice.objects.get(uuid=request.POST.get('invoice'))

    prop = Tenant.objects.get(profile=user).unit.property
    company = CompanyProfile.objects.get(company=prop.company, user__acc_type_id__in=[2, 3]).user
    landlord = Profile.objects.get(user=company)

    URL = "https://portal.hapokash.app/api/wallet/transfer"
    PARAMS = {
        "debit_wallet_id": user.hapokash,
        "credit_wallet_id": landlord.hapokash,
        "amount": request.POST.get('amount'),
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
            invoice_item=InvoiceItems.objects.get(invoice=invoice), amount_paid=request.POST.get('amount'),
            payment_mode="Wallet Transfer",
            remarks="Payment For Invoice From wallet", date_paid=datetime.date.today(), created_by=request.user
        )
        pay.save()
    elif not r['success'] and r['message'] == "Unauthenticated.":
        URL = "https://portal.hapokash.app/api/wallet/transfer"
        PARAMS = {
            "debit_wallet_id": user.hapokash,
            "credit_wallet_id": landlord.hapokash,
            "amount": request.POST.get('amount'),
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
                invoice_item=InvoiceItems.objects.get(invoice=invoice), amount_paid=request.POST.get('amount'),
                payment_mode="Wallet Transfer",
                remarks="Payment For Invoice From wallet", date_paid=datetime.date.today(), created_by=request.user
            )
            pay.save()

    return redirect('dashboard')


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


@login_required
def logout_request(request):
    logout(request)
    return redirect('web-login')


def about(request):
    return render(request, 'authapp/about.html')


@login_required
def subsPick(request):
    if request.user.id == 4:
        return HttpResponse("Cannot continue, Agency subscription not paid")
    subs = Subscriptions.objects.filter(is_active=True)
    company_end = SubscriptionsCompanies.objects.get(company=CompanyProfile.objects.get(user=request.user).company)
    if request.method == "POST":
        prof = Profile.objects.get(user=request.user).msisdn
        subsc = Subscriptions.objects.get(uuid=request.POST.get('sub_picked'))

        if prof.startswith('0'):
            mobile = '254' + prof[1:]
        elif prof.startswith('1') or prof.startswith('7'):
            mobile = '254' + prof
        elif prof.startswith('+'):
            mobile = prof[1:]
        else:
            mobile = prof

        URL = "https://portal.hapokash.app/api/wallet/top_up"

        headers_dict = {"Accept": "application/json", "Content-Type": "application/json"}
        r = requests.post(url=URL, json={"msisdn": mobile, "amount": int(subsc.value), "account_no": 17},
                          headers=headers_dict)
        print(r.json())
    return render(request, 'authapp/subscriptions.html', {'subs': subs, 'user': request.user, 'comp': company_end})


@unsubscribed_user
@login_required
def wall_bal(request):
    if request.user.acc_type.id == 5:
        raise PermissionDenied

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
        for i in range(trans['last_page'] - 1):
            print(trans['next_page_url'])
            URL = trans['next_page_url']
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

    for d in trans['data']:
        d.update((k, datetime.datetime.strptime(
            '{} {}'.format(v.split('T')[0], v.split('T')[1].split('.')[0]), '%Y-%m-%d %H:%M:%S'
        ).strftime('%d/%B/%Y, %H:%M:%S')) for k, v in d.items() if k == "created_at")

    context = {
        'user': request.user,
        'cur_balance': cur_balance,
        'previous_balance': pre_balance,
        'trans': trans,
        'profile': Profile.objects.get(user=request.user)
    }
    return render(request, 'authapp/wallet.html', context)


def wallet_trans(wall_id):
    URL = "https://portal.hapokash.app/api/wallet/transactions/{}".format(wall_id)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }

    r = requests.get(url=URL, headers=headers)
    wallet = r.json()
    print(wallet)
    if wallet['success']:
        return wallet['transactions']
    elif not wallet['success'] and wallet['message'] == "Unauthenticated.":
        refreshToken()
        URL = "https://portal.hapokash.app/api/wallet/transactions/{}".format(wall_id)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }

        r = requests.get(url=URL, headers=headers)
        wallet = r.json()
        print(wallet)
        if wallet['success']:
            return wallet['transactions']


def confirm_payment(request):
    trans = request.POST.get('trans')
    print(request.POST)
    uuid = request.POST.get('uuid')
    u_name = request.POST.get('conf_uname')
    URL = "https://portal.hapokash.app/api/wallet/transactions/17"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }

    r = requests.get(url=URL, headers=headers)
    past_trx = TransactionCodes.objects.filter(trx=trans)
    if past_trx.exists():
        return HttpResponse("Exists")

    wallet = r.json()
    print(wallet)
    if wallet['success']:
        search = wallet['transactions']['data']
        # print(search)
        for a in search:
            print(a)
            if a['trx_id'] == trans:
                try:
                    sub = SubscriptionsCompanies.objects.create(
                        company=CompanyProfile.objects.get(user=Users.objects.get(username=u_name)).company,
                        date_started=date.today(), subs=Subscriptions.objects.get(uuid=uuid),
                        date_end=add_months(datetime.date.today(), Subscriptions.objects.get(uuid=uuid).duration)
                    )
                    sub.save()
                    past_trx = TransactionCodes.objects.create(trx=trans, created_by=Users.objects.get(id=1))
                    past_trx.save()
                except:
                    print("wrong")
                return HttpResponse(reverse('logout'))
        if int(wallet['transactions']['last_page']) != 1:
            for i in range(int(wallet['transactions']['last_page']) - 1):
                URL = wallet['transactions']['next_page_url']
                r = requests.get(url=URL, headers=headers)
                wallet = r.json()
                if wallet['success']:
                    search = wallet['transactions']['data']
                    for a in search:
                        if a['trx_id'] == trans:
                            try:
                                sub = SubscriptionsCompanies.objects.create(
                                    company=CompanyProfile.objects.get(user=Users.objects.get(username=u_name)).company,
                                    date_started=date.today(), subs=Subscriptions.objects.get(uuid=uuid),
                                    date_end=add_months(datetime.date.today(),
                                                        Subscriptions.objects.get(uuid=uuid).duration)
                                )
                                sub.save()
                                past_trx = TransactionCodes.objects.create(trx=trans,
                                                                           created_by=Users.objects.get(id=1))
                                past_trx.save()
                            except:
                                print("wrong")
                            return HttpResponse(reverse('logout'))

    elif not wallet['success'] and wallet['message'] == "Unauthenticated.":
        refreshToken()
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }

        r = requests.get(url=URL, headers=headers)

        wallet = r.json()
        if wallet['success']:
            search = wallet['transactions']['data']
            # print(search)
            for a in search:
                print(a)
                if a['trx_id'] == trans:
                    try:
                        sub = SubscriptionsCompanies.objects.create(
                            company=CompanyProfile.objects.get(user=Users.objects.get(username=u_name)).company,
                            date_started=date.today(), subs=Subscriptions.objects.get(uuid=uuid),
                            date_end=add_months(datetime.date.today(), Subscriptions.objects.get(uuid=uuid).duration)
                        )
                        sub.save()
                        past_trx = TransactionCodes.objects.create(trx=trans, created_by=Users.objects.get(id=1))
                        past_trx.save()
                    except:
                        print("wrong")
                    return HttpResponse(reverse('logout'))
            if int(wallet['transactions']['last_page']) != 1:
                for i in range(int(wallet['transactions']['last_page']) - 1):
                    URL = wallet['transactions']['next_page_url']
                    r = requests.get(url=URL, headers=headers)
                    wallet = r.json()
                    if wallet['success']:
                        search = wallet['transactions']['data']
                        for a in search:
                            if a['trx_id'] == trans:
                                try:
                                    sub = SubscriptionsCompanies.objects.create(
                                        company=CompanyProfile.objects.get(
                                            user=Users.objects.get(username=u_name)).company,
                                        date_started=date.today(), subs=Subscriptions.objects.get(uuid=uuid),
                                        date_end=add_months(datetime.date.today(),
                                                            Subscriptions.objects.get(uuid=uuid).duration)
                                    )
                                    sub.save()
                                    past_trx = TransactionCodes.objects.create(trx=trans,
                                                                               created_by=Users.objects.get(id=1))
                                    past_trx.save()
                                except:
                                    print("wrong")
                                return HttpResponse(reverse('logout'))
    return "Not Found"


def confirm_payment_renew(request):
    trans = request.POST.get('trans')
    print(request.POST)
    uuid = request.POST.get('uuid')
    URL = "https://portal.hapokash.app/api/wallet/transactions/17"

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
    }

    r = requests.get(url=URL, headers=headers)
    past_trx = TransactionCodes.objects.filter(trx=trans)
    if past_trx.exists():
        return HttpResponse("Exists")

    wallet = r.json()
    if wallet['success']:
        search = wallet['transactions']['data']
        # print(search)
        for a in search:
            print(a)
            if a['trx_id'] == trans:
                try:
                    sub = SubscriptionsCompanies.objects.get(
                        company=CompanyProfile.objects.get(user=request.user).company)
                    sub.date_started = date.today()
                    sub.date_end = add_months(datetime.date.today(), Subscriptions.objects.get(uuid=uuid).duration)
                    sub.save()
                    past_trx = TransactionCodes.objects.create(trx=trans, created_by=Users.objects.get(id=1))
                    past_trx.save()

                    past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                    past_trx.save()
                except:
                    print("wrong")
                return HttpResponse(reverse('logout'))
        if int(wallet['transactions']['last_page']) != 1:
            for i in range(int(wallet['transactions']['last_page']) - 1):
                URL = wallet['transactions']['next_page_url']
                r = requests.get(url=URL, headers=headers)
                wallet = r.json()
                if wallet['success']:
                    search = wallet['transactions']['data']
                    for a in search:
                        if a['trx_id'] == trans:
                            try:
                                sub = SubscriptionsCompanies.objects.get(
                                    company=CompanyProfile.objects.get(user=request.user).company)
                                sub.date_started = date.today()
                                sub.date_end = add_months(datetime.date.today(),
                                                          Subscriptions.objects.get(uuid=uuid).duration)
                                sub.save()
                                past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                                past_trx.save()
                            except:
                                print("wrong")
                            return HttpResponse(reverse('logout'))

    elif not wallet['success'] and wallet['message'] == "Unauthenticated.":
        refreshToken()
        URL = "https://portal.hapokash.app/api/wallet/transactions/17"

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(AuthTokens.objects.get(id=1).auth)
        }

        r = requests.get(url=URL, headers=headers)
        wallet = r.json()
        if wallet['success']:
            search = wallet['transactions']['data']
            # print(search)
            for a in search:
                print(a)
                if a['trx_id'] == trans:
                    try:
                        sub = SubscriptionsCompanies.objects.get(
                            company=CompanyProfile.objects.get(user=request.user).company)
                        sub.date_started = date.today()
                        sub.date_end = add_months(datetime.date.today(), Subscriptions.objects.get(uuid=uuid).duration)
                        sub.save()
                        past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                        past_trx.save()
                    except:
                        print("wrong")
                    return HttpResponse(reverse('logout'))
            if int(wallet['transactions']['last_page']) != 1:
                for i in range(int(wallet['transactions']['last_page']) - 1):
                    URL = wallet['transactions']['next_page_url']
                    r = requests.get(url=URL, headers=headers)
                    wallet = r.json()
                    if wallet['success']:
                        search = wallet['transactions']['data']
                        for a in search:
                            if a['trx_id'] == trans:
                                try:
                                    sub = SubscriptionsCompanies.objects.get(
                                        company=CompanyProfile.objects.get(user=request.user).company)
                                    sub.date_started = date.today()
                                    sub.date_end = add_months(datetime.date.today(),
                                                              Subscriptions.objects.get(uuid=uuid).duration)
                                    sub.save()
                                    past_trx = TransactionCodes.objects.create(trx=trans, created_by=request.user)
                                    past_trx.save()
                                except:
                                    print("wrong")
                                return HttpResponse(reverse('logout'))
    return "Not Found"


def stkpushreg(mo, am):
    if mo.startswith('0'):
        mobile = '254' + mo[1:]
    elif mo.startswith('1') or mo.startswith('7'):
        mobile = '254' + mo
    elif mo.startswith('+'):
        mobile = mo[1:]
    else:
        mobile = mo

    URL = "https://portal.hapokash.app/api/wallet/top_up"

    headers_dict = {"Accept": "application/json", "Content-Type": "application/json"}
    r = requests.post(url=URL, json={"msisdn": mobile, "amount": int(am), "account_no": 17},
                      headers=headers_dict)
    wallet = r.json()
    print(wallet)


def acc_terms(request):
    tenant = Tenant.objects.get(profile__user=request.user)
    tenant.accept_terms = True
    tenant.save()
    return redirect('dashboard')


def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = Users.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "password/password_reset_email.txt"
                    c = {
                        "email": user.email,
                        'domain': 'mnestafrica.com',
                        'site_name': 'MNEST',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'https',
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, 'admin@example.com', [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                return redirect("/password_reset/done/")

            else:
                messages.error(request, 'An invalid email has been entered.')
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="password/password_reset.html", context={"password_reset_form": password_reset_form})
