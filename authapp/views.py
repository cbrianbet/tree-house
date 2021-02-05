import calendar
import datetime
import os

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login as log_in, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from authapp.forms import LoginForm
from authapp.models import *
from bills.models import *
from properties.models import Companies, CompanyProfile, Tenant, SubscriptionsCompanies, Properties
from tree_house import settings


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        print(form.is_valid())
        if form.is_valid():
            clean = form.cleaned_data
            user = authenticate(username=clean['username'], password=clean['password'])
            if not Users.objects.get(username=clean['username']).is_active:
                return HttpResponse('Account is Disabled')
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
def dashboard(request):
    user = request.user
    if user.acc_type.id == 4:
        prof = Profile.objects.get(user=user)
        tenant = Tenant.objects.get(profile=prof)
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
            r_bals = due.amount + r_bals

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
        }
        return render(request, 'authapp/tenant_dash.html', context)

    elif user.acc_type.id == 1:
        sub = SubscriptionsCompanies.objects.values('subs__name').annotate(c=Count('subs__name')).order_by('-c')
        active_u = Users.objects.all()
        context = {
            'user': user,
            'subs': sub,
            'land': active_u.filter(acc_type_id=2).count(),
            'ag': active_u.filter(acc_type_id=3).count(),
            'staff': active_u.filter(acc_type_id=5).count(),
            'tena': active_u.filter(acc_type_id=4).count(),
        }
        return render(request, 'authapp/Super_analytics.html', context)

    elif user.acc_type.id == 2 or user.acc_type.id == 3:
        prop = Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company)
        unit = Unit.objects.filter(property__in=prop)
        # print(unit)
        paid  = 0
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
def suspend_user(request, uid):
    if not request.user.acc_type.id == 1:
        raise PermissionDenied
    user = Users.objects.get(id=uid)
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    user.save()
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
    cp =CompanyProfile.objects.filter(company=company)
    for c in cp:
        user = Users.objects.get(id=c.user.id)
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.save()

    return redirect('all-companies')


@login_required
def delete_company(request, uid):
    if not request.user.acc_type.id == 1:
        raise PermissionDenied
    company = Companies.objects.get(id=uid)
    cp =CompanyProfile.objects.filter(company=company)
    for c in cp:
        user = Users.objects.get(id=c.user.id)
        user.delete()
    company.delete()
    cp.delete()

    return redirect('all-companies')

@login_required
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
    sub = Subscriptions.objects.all()
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
        mobile = request.POST.get('mobile')
        terms = request.POST.get('terms')
        company_name = request.POST.get('company')
        no_of_units = request.POST.get('props_no')
        type = request.POST.get('acc_type')
        number = request.POST.get('id_no')
        location = request.POST.get('location')
        sub_picked = request.POST.get('sub_picked')

        if request.FILES:
            logo = request.FILES['logo']
        else:
            logo = ''
        try:
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
                sub = SubscriptionsCompanies.objects.create(
                    subs=Subscriptions.objects.get(uuid=sub_picked), company=company,
                    date_end=add_months(datetime.date.today(), Subscriptions.objects.get(uuid=sub_picked).duration),
                    date_started=datetime.date.today()
                )
                sub.save()
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
    PARAMS = {"currency": "KES"}
    r = requests.post(url=URL, data=PARAMS)
    return r.json()


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
