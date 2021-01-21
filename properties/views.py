import csv
import datetime
import io
import os
import random
import string

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Count
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect

from authapp.models import AccTypes
from tree_house import settings
from tree_house.settings import EMAIL_HOST_USER
from .models import *


@login_required
def properties_list(request):
    p = Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company)
    queryset1 = Tenant.objects.filter(unit__property__in=p).values('unit__property__uuid').annotate(count=Count('unit__property__uuid')).order_by(
        'unit__property__uuid')

    tenants = {}
    for entry in queryset1:
        tenants.update({entry['unit__property__uuid']: entry['count']})
    print(tenants)
    context = {
        'prop': p,
        'tenant': tenants,
        'user': request.user,
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

        if request.FILES:
            picture = request.FILES['logo']
        else:
            picture = ''

        prop = Properties.objects.create(
            property_name=name, property_value=val, mngmt_start=start_date, property_type=prop_type, owner=owner,
            no_of_floors=floors, no_of_units=units, parking=parking, electricity=elec, water=water,
            location_desc=loc_desc,
            pics=picture, company=CompanyProfile.objects.get(user=user).company, building_type=build,
            created_by=request.user
        )
        prop.save()
    context = {
        'u': user,
        'user': request.user,
    }
    return render(request, 'properties/add_property.html', context)


@login_required
def list_units(request, u_uid):
    prop = Properties.objects.get(uuid=u_uid)
    unit = Unit.objects.filter(property=prop)
    context = {
        'p': range(prop.no_of_floors),
        'prop': prop,
        'p_id': u_uid,
        'unit': unit,
        'user': request.user,
    }
    return render(request, 'properties/units_list.html', context)


@login_required
def add_units(request, floor, u_uid):
    prop = Properties.objects.get(uuid=u_uid)
    if request.method == "POST":
        unit = request.POST.get('name')
        value = request.POST.get('value')
        unit_status = request.POST.get('status')
        area = request.POST.get('area')
        service_charge = request.POST.get('service_charge')
        no_of_parking = request.POST.get('parking')
        size = request.POST.get('size_unit')
        specify = request.POST.get('other')
        deposit = request.POST.get('deposit')

        u_save = Unit.objects.create(
            unit_name=unit, property=prop, security_deposit=deposit, size=size, other_specify=specify, value=value,
            parking_assigned=no_of_parking, service_charge=service_charge, area=area, unit_status=unit_status,
            floor=floor,
            created_by=request.user
        )
        u_save.save()

    context = {
        'fl': floor,
        'u_id': u_uid,
        'prop': prop,
        'user': request.user,
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
        t = Tenant.objects.create(
            secondary_msisdn=secondary_mobile, date_occupied=date_of_occupancy, unit=unit, profile=p,
            created_by=request.user
        )
        t.save()

        inform(username, pwrd, email, f_name)

        unit.unit_status = "Occupied"
        unit.save()

    if Tenant.objects.filter(unit=unit).exists():
        return redirect('view-tenant', u_uid=unit.uuid)

    context = {
        'u_id': u_uid,
        'unit': unit,
        'user': request.user,
    }

    return render(request, 'properties/add_tenant.html', context)


def inform(u, p, e, n):
    subject = "Welcome to"
    message = '''
    Dear {}, 
    We are thrilled to have you on-board! 
    This email is to let you know that we are continuing to utilise the latest technologies available to provide you with an even better service. 
    A special login has been created for you as follows:
    Web URL:	https://mnest.co.ke/login
    username: {}
    Password:	{}
    It is recommended that you change your password after login in for the first time by choosing the Change Password link in the side menu of the web site.'''.format(
        n, u, p)
    send_mail(subject, message, EMAIL_HOST_USER, [e], fail_silently=False)


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
        't': prop,
        'user': request.user,
    }
    return render(request, 'properties/tenant_view.html', context)


@login_required
def swap_tenant(request, u_uid):
    if request.method == "POST":
        old = Tenant.objects.get(unit__uuid=u_uid)
        new = request.POST.get('unit')

        old.unit = Unit.objects.get(uuid=new)
        old.save()
        u = Unit.objects.get(uuid=u_uid)
        u.unit_status = "Vacant"
        u.save()

        n = Unit.objects.get(uuid=new)
        n.unit_status = "Occupied"

        return redirect('swap-tenant', u_uid=new)

    prop = Tenant.objects.get(unit__uuid=u_uid)

    ten = Tenant.objects.values_list('unit__uuid', flat=True)
    company = CompanyProfile.objects.get(user=request.user).company
    unit = Unit.objects.filter(property__company=company).exclude(uuid__in=ten).order_by('property', 'unit_name')
    print(unit)
    context = {
        'p_id': u_uid,
        'unit': unit,
        't': prop,
        'user': request.user,
    }
    return render(request, 'properties/tenant_swap.html', context)


@login_required
def get_unit(request):
    return

#File uploads
@login_required
def prop_file_upload(request):
    # declaring template

    csv_file = request.FILES['logo']
    # let's check if it is a csv file
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'THIS IS NOT A CSV FILE')
    data_set = csv_file.read().decode('UTF-8')
    # setup a stream which is when we loop through each line we are able to handle a data in a stream

    io_string = io.StringIO(data_set)
    next(io_string)
    for column in csv.reader(io_string, delimiter=',', quotechar="|"):
        print(column)
        created = Properties.objects.create(
            property_name=column[0],
            no_of_floors=column[1],
            property_value=column[2],
            no_of_units=column[3],
            parking=column[4],
            mngmt_start=datetime.datetime.strptime(column[5], "%d/%m/%Y").strftime("%Y-%m-%d"),
            property_type=column[6],
            building_type=column[7],
            electricity=column[8],
            water=column[9],
            location_desc=column[10],
            created_by=request.user,
            company=CompanyProfile.objects.get(user=request.user).company
        )
        created.save()
    return redirect('prop-list')


@login_required
def tenant_file_upload(request):
    return


@login_required
def prop_template(request):
    file_path = os.path.join(settings.MEDIA_ROOT, 'properties.csv')
    print(file_path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404


@login_required
def unit_template(request):
    file_path = os.path.join(settings.MEDIA_ROOT, 'Units.csv')
    print(file_path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404


@login_required
def unit_file_upload(request, uid):
    # declaring template

    csv_file = request.FILES['logo']
    # let's check if it is a csv file
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'THIS IS NOT A CSV FILE')
    data_set = csv_file.read().decode('UTF-8')
    # setup a stream which is when we loop through each line we are able to handle a data in a stream

    io_string = io.StringIO(data_set)
    next(io_string)
    for column in csv.reader(io_string, delimiter=',', quotechar="|"):

        created = Unit.objects.create(
            unit_name=column[0],
            value=column[1],
            area=column[2],
            size=column[3],
            service_charge=column[4],
            security_deposit=column[5],
            unit_status=column[6],
            parking_assigned=column[7],
            floor=column[8],
            property=Properties.objects.get(uuid=uid),
            created_by=request.user
        )
        created.save()
    return redirect('unit-list', u_uid=uid)
