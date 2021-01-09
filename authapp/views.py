from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    if request.method == "POST":
        return HttpResponse('dashboard')

    return render(request, 'authapp/login-v3.html')
