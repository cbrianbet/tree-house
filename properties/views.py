from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import *


@login_required
def properties_list(request):
    p = Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company)
    context = {
        'prop': p,
    }
    return render(request, 'properties/properties_list.html', context)


@login_required
def properties_add(request):
    user = request.user
    p = Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company)
    context = {
        'prop': p,
        'u': user,
    }
    return render(request, 'properties/add_property.html', context)
