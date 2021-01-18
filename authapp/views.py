from django.contrib import messages
from django.contrib.auth import authenticate, login as log_in, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from authapp.forms import LoginForm
from authapp.models import Users, Profile, AccTypes
from properties.models import Companies, CompanyProfile


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
    return render(request, "authApp/login-v3.html", {'form': form})


@login_required
def dashboard(request):
    return render(request, 'authapp/analytics.html')


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
            logo = request.FILES['pic']
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
                company = Companies.objects.create(name=company_name, no_of_emp=no_of_units, location=location, logo=logo)
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

