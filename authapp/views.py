import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login as log_in, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from authapp.forms import LoginForm
from authapp.models import Users, Profile, AccTypes
from bills.models import Invoice, InvoiceItems, InvoiceItemsTransaction
from properties.models import Companies, CompanyProfile, Tenant


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        print(form.is_valid())
        if form.is_valid():
            clean = form.cleaned_data
            user = authenticate(username=clean['username'], password=clean['password'])
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
        num = 10000000
        print(f"{num:,d}")
        prof = Profile.objects.get(user=user)
        tenant = Tenant.objects.get(profile=prof)
        invoice = Invoice.objects.filter(invoice_for=user, status=False)
        inv_item = InvoiceItems.objects.filter(invoice__in=invoice)
        inv_tran = InvoiceItemsTransaction.objects.filter(invoice_item__in=inv_item)

        bals = 0
        for due in inv_item:
            bals = due.amount + bals

        for due in inv_tran:
            bals = bals - due.amount_paid

        bals = '{0:,}'.format(bals)
        context = {
            'user': user,
            'prof': prof,
            'tenant': tenant,
            'bals': bals,
            'inv': invoice.count(),
        }
        return render(request, 'authapp/tenant_dash.html', context)

    elif user.acc_type.id == 1:
        context = {'user': user}
        return render(request, 'authapp/analytics.html', context)

    else:
        context = {'user': user}
        return render(request, 'authapp/analytics.html', context)


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
            'timeline': sorted(events, key = lambda i: (i['days'])),
        }

    elif user.acc_type.id == 1:
        context = {
            'user': user,
        }

    else:
        context = {
            'user': user,
        }
    return render(request, 'authapp/profile.html', context)


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

        if request.FILES:
            logo = request.FILES['logo']
        else:
            logo = ''

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

        return redirect('web-login')
    return render(request, 'authapp/register.html')


@login_required
def logout_request(request):
    logout(request)
    return redirect('web-login')
