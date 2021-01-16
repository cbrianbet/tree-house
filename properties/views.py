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
    unit = Unit.objects.filter(property=prop)
    context = {
        'p': range(prop.no_of_floors),
        'p_id': u_uid,
        'unit': unit,
    }
    return render(request, 'properties/units_list.html', context)


@login_required
def add_units(request, floor, u_uid):
    prop = Properties.objects.get(uuid=u_uid)
    if request.method == "POST":
        unit = request.POST.get('name')
        type_of_units = request.POST.get('type')
        value = request.POST.get('value')
        unit_status = request.POST.get('status')
        area = request.POST.get('area')
        service_charge = request.POST.get('service_charge')
        no_of_parking = 0
        size = request.POST.get('size_unit')
        specify = request.POST.get('other')

        u_save = Unit.objects.create(
            unit_name=unit, property=prop, type_of_unit=type_of_units, size=size, other_specify=specify, value=value,
            parking_assigned=no_of_parking, service_charge=service_charge, area=area, unit_status=unit_status, floor=floor
        )
        u_save.save()

    context = {
        'fl': floor,
        'u_id': u_uid,
        'prop': prop,
    }

    return render(request, 'properties/add_unit.html', context)
