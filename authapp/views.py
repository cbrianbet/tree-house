from django.http import HttpResponse
from django.shortcuts import render


def login(request):
    if request.method == "POST":
        return HttpResponse('dashboard')

    return render(request, 'authapp/login-v3.html')


def dashboard(request):
    return render(request, 'authapp/analytics.html')


def signup(request):
    if request.method == "POST":
        return HttpResponse('login')
    return render(request, 'authapp/register.html')
