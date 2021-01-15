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
    if request.method == "POST":
        name = request.POST.get('p_name')
        val = request.POST.get('val_prop')
        start_date = request.POST.get('start_date')
        prop_type = request.POST.get('p_type')
        owner = request.POST.get('owner')
        floors = request.POST.get('floors')
        units = request.POST.get('units')
        parking = request.POST.get('parking')
        elec = request.POST.get('elec')
        water = request.POST.get('water')
        build = request.POST.get('b_type')
        loc_desc = request.POST.get('loc_desc')
        # picture = request.FILES['pic']
        if request.FILES:
            picture = request.FILES['pic']
        else:
            picture = ''

        prop = Properties.objects.create(
            property_name=name, property_value=val, mngmt_start=start_date, property_type=prop_type, owner=owner,
            no_of_floors=floors, no_of_units=units, parking=parking, electricity=elec, water=water, location_desc=loc_desc,
            pics=picture, company=CompanyProfile.objects.get(user=user).company, building_type=build
        )
        prop.save()
    context = {
        'u': user,
    }
    return render(request, 'properties/add_property.html', context)


@login_required
def list_units(request, u_uid):
    prop = Properties.objects.get(uuid=u_uid)
    context = {
        'p': range(prop.no_of_floors),
        'p_id': u_uid
    }
    return render(request, 'properties/units_list.html', context)


@login_required
def add_units(request, floor, u_uid):
    prop = Properties.objects.get(uuid=u_uid)

    return render(request, 'properties/add_unit.html')
