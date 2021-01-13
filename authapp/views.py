from django.http import HttpResponse
from django.shortcuts import render

from authapp.models import Users, Profile, AccTypes
from properties.models import Companies, CompanyProfile


def login(request):
    if request.method == "POST":
        return HttpResponse('dashboard')

    return render(request, 'authapp/login-v3.html')


def dashboard(request):
    return render(request, 'authapp/analytics.html')


def signup(request):
    if request.method == "POST":
        print(request.POST)
        username = request.POST.get('username')
        email = request.POST.get('email')
        pwrd = request.POST.get('password')
        re_pwrd = request.POST.get('re_password')
        f_name = request.POST.get('f_name')
        l_name = request.POST.get('l_name')
        mobile = request.POST.get('mobile')
        terms = request.POST.get('terms')
        company_name = request.POST.get('company')
        no_of_units = request.POST.get('props_no')
        type = request.POST.get('acc_type')

        acc = AccTypes.objects.get(id=int(type))
        user = Users.objects.create_user(username=username, password=pwrd, email=email, acc_type=acc)
        user.save()

        if user.pk:
            profile = Profile.objects.create(first_name = f_name, last_name = l_name, msisdn = mobile, terms_accepted = terms, user = user)
            profile.save()

            company = Companies.objects.create(name = company_name, no_of_units = no_of_units)
            company.save()

            cp = CompanyProfile.objects.create(user = user, company = company)
            cp.save()



        return HttpResponse('login')
    return render(request, 'authapp/register.html')
