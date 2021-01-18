import datetime
import random
import string

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from authapp.models import AccTypes
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
            picture = request.FILES['logo']
        else:
            picture = ''

        prop = Properties.objects.create(
            property_name=name, property_value=val, mngmt_start=start_date, property_type=prop_type, owner=owner,
            no_of_floors=floors, no_of_units=units, parking=parking, electricity=elec, water=water, location_desc=loc_desc,
            pics=picture, company=CompanyProfile.objects.get(user=user).company, building_type=build, created_by=request.user
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
            parking_assigned=no_of_parking, service_charge=service_charge, area=area, unit_status=unit_status, floor=floor,
            created_by=request.user
        )
        u_save.save()

    context = {
        'fl': floor,
        'u_id': u_uid,
        'prop': prop,
    }

    return render(request, 'properties/add_unit.html', context)


@login_required
def add_tenant(request, u_uid):
    unit = Unit.objects.get(uuid=u_uid)
    if request.method == "POST":

        f_name = request.POST.get('f_name')
        l_name = request.POST.get('l_name')
        id_no = request.POST.get('id_no')
        mobile = request.POST.get('primary')
        secondary_mobile = request.POST.get('secondary')
        email = request.POST.get('email')
        date_of_occupancy = datetime.datetime.strptime(request.POST.get('date'), "%d/%m/%Y").strftime("%Y-%m-%d")
        username = get_random_username()
        pwrd = ''.join((random.choice(string.ascii_letters + string.digits) for i in range(8)))
        acc = AccTypes.objects.get(id=4)

        u = Users.objects.create_user(username=username, password=pwrd, email=email, acc_type=acc)
        u.save()
        p = Profile.objects.create(
            first_name=f_name, last_name=l_name, msisdn=mobile, id_number=id_no, user=u
        )
        p.save()
        t =Tenant.objects.create(
            secondary_msisdn=secondary_mobile, date_occupied=date_of_occupancy, unit=unit, profile=p, created_by=request.user
        )
        t.save()

        unit.unit_status = "Occupied"
        unit.save()

    if Tenant.objects.filter(unit=unit).exists():
        return redirect('view-tenant', u_uid=unit.uuid)


    context = {
        'u_id': u_uid,
        'unit': unit,
    }

    return render(request, 'properties/add_tenant.html', context)


def get_random_username():
    username = ''.join(random.sample(string.ascii_uppercase, 2)) + '-' + ''.join(random.sample(string.digits, 6))
    if not Users.objects.filter(username=username).exists():
        return username
    else:
        get_random_username()


@login_required
def view_tenant(request, u_uid):
    prop = Tenant.objects.get(unit__uuid=u_uid)
    unit = Unit.objects.filter(id=prop.unit.id)
    context = {
        'p_id': u_uid,
        'unit': unit,
        't': prop
    }
    return render(request, 'properties/tenant_view.html', context)
