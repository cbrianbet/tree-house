import csv
import datetime
import io
import os
import random
import string
import calendar

from dateutil import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authapp.decorators import unsubscribed_user
from authapp.models import AccTypes, SignatureLandlord
from authapp.views import hapokashcreate
from bills.models import Invoice, InvoiceItems, RentInvoice, RentItems
from bills.views import increment_invoice_number, increment_rent_invoice_number
from tree_house import settings
from tree_house.settings import EMAIL_HOST_USER
from .models import *
from .pdfs import render_to_pdf
from .serializer import TenantHistorySerializer, VacantUnitSerializer, VacantUnitAPISerializer, EnquireAPISerializer


@login_required
@unsubscribed_user
def properties_list(request):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.view_properties'):
            raise PermissionDenied
        prop = PropertyStaff.objects.filter(user=request.user).values_list('property__uuid', flat=True)
        p = Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company, uuid__in=prop)
        th = TenantHistory.objects.filter(curr_unit__property__in=p, end_date=None).values('curr_unit__property__uuid').annotate(
            count=Count('curr_unit__property__uuid')).order_by('curr_unit__property__uuid')

    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        p = Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company)
        th = TenantHistory.objects.filter(curr_unit__property__in=p, end_date=None).values('curr_unit__property__uuid').annotate(
            count=Count('curr_unit__property__uuid')).order_by('curr_unit__property__uuid')

    tenants = {}
    for entry in th:
        tenants.update({entry['curr_unit__property__uuid']: entry['count']})
    print(tenants)
    sub = SubscriptionsCompanies.objects.get(company=CompanyProfile.objects.get(user=request.user).company).property_limit - p.count()
    print(sub)
    context = {
        'prop': p,
        'tenant': tenants,
        'user': request.user,
        'can_add': True if sub > 0 else False
    }
    return render(request, 'properties/properties_list.html', context)


@login_required
@unsubscribed_user
def properties_add(request):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.add_properties'):
            raise PermissionDenied
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
        long = request.POST.get('longitude')
        lat = request.POST.get('latitude')
        rent_coll = request.POST.get('rent_coll')
        spdate = request.POST.get('specify_day')
        pen_type = request.POST.get('pen_type')
        pen_val = request.POST.get('penalty')

        if request.FILES:
            picture = request.FILES['pic']
        else:
            picture = ''

        prop = Properties.objects.create(
            property_name=name, property_value=val, mngmt_start=start_date, property_type=prop_type, owner=owner,
            no_of_floors=floors, no_of_units=units, parking=parking, electricity=elec, water=water,
            location_desc=loc_desc, long=long, lat=lat, created_by=request.user, rent_collection=rent_coll,
            pics=picture, company=CompanyProfile.objects.get(user=user).company, building_type=build,
            specific_day=spdate, penalty_type=pen_type, penalty_value=pen_val
        )
        prop.save()
    context = {
        'u': user,
        'user': request.user,
    }
    return render(request, 'properties/add_property.html', context)


@login_required
@unsubscribed_user
def properties_payment(request, u_id):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.change_properties'):
            raise PermissionDenied
    user = request.user
    prop = Properties.objects.get(uuid=u_id)
    if request.method == "POST":
        print(request.POST)
        name = request.POST.get('p_mode')
        pay = PaymentAccount.objects.create(payment_mode=name, created_by=request.user, prop=prop)
        pay.save()
        if name == 'MPESA':
            lipa = request.POST.get('lipa')
            if lipa == 'paybill':
                paybill = PaymentPaybill.objects.create(prop=pay, acc=request.POST.get('p_acc_no'),
                                                        paybill=request.POST.get('paybill'))
                paybill.save()
            if lipa == 'tillnumber':
                goods = PaymentTill.objects.create(prop=pay, till=request.POST.get('t_acc_no'))
                goods.save()

        if name == 'BANK':
            bank_acc = BankAcc.objects.create(prop=pay, bank_id=request.POST.get('bank'),
                                              acc=request.POST.get('b_acc_no'))
            bank_acc.save()

    context = {
        'u': user,
        'user': request.user,
        'bank': Banks.objects.all(),
        'uuid': u_id,
        'accb': BankAcc.objects.filter(prop__prop=prop),
        'accp': PaymentPaybill.objects.filter(prop__prop=prop),
        'acct': PaymentTill.objects.filter(prop__prop=prop),
    }
    return render(request, 'properties/payment_account.html', context)


@login_required
@unsubscribed_user
def properties_edit(request, p_id):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.change_properties'):
            raise PermissionDenied
    user = request.user
    prop = Properties.objects.get(uuid=p_id)
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
        long = request.POST.get('longitude')
        lat = request.POST.get('latitude')
        rent_coll = request.POST.get('rent_coll')
        spdate = request.POST.get('specify_day')
        pen_type = request.POST.get('pen_type')
        pen_val = request.POST.get('penalty')

        if request.FILES:
            picture = request.FILES['pic']
        else:
            picture = ''

        prop.property_name = name
        prop.property_value = val
        prop.mngmt_start = start_date
        prop.property_type = prop_type
        prop.owner = owner
        prop.no_of_floors = floors
        prop.no_of_units = units
        prop.parking = parking
        prop.electricity = elec
        prop.water = water
        prop.location_desc = loc_desc
        prop.long = long
        prop.lat = lat
        prop.created_by = request.user
        prop.rent_collection = rent_coll
        prop.pics = picture
        prop.building_type = build
        prop.specific_day = spdate
        prop.penalty_type = pen_type
        prop.penalty_value = pen_val

        prop.save()
        redirect('view-prop', p_id=p_id)
    context = {
        'u': user,
        'user': request.user,
        'prop': prop
    }
    return render(request, 'properties/edit_property.html', context)


@login_required
@unsubscribed_user
def view_prop(request, p_id):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.view_properties'):
            raise PermissionDenied

    prop = Properties.objects.get(uuid=p_id)
    tenants = TenantHistory.objects.filter(end_date=None, curr_unit__property=prop).count()

    context = {
        'p_id': p_id,
        't': prop,
        't_no': tenants,
        'user': request.user,
    }
    return render(request, 'properties/prop_view.html', context)


@login_required
@unsubscribed_user
def list_units(request, u_uid):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.view_unit'):
            raise PermissionDenied
    prop = Properties.objects.get(uuid=u_uid)
    unit = Unit.objects.filter(property=prop)
    can_add = False
    if unit.count() < prop.no_of_units:
        can_add = True
    context = {
        'p': range(prop.no_of_floors),
        'prop': prop,
        'p_id': u_uid,
        'unit': unit,
        'user': request.user,
        'can_add': can_add,
    }
    return render(request, 'properties/units_list.html', context)


@login_required
@unsubscribed_user
def add_units(request, floor, u_uid):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.add_unit'):
            raise PermissionDenied
    prop = Properties.objects.get(uuid=u_uid)
    if Unit.objects.filter(property=prop).count() >= prop.no_of_units:
        return redirect('unit-list', u_uid=u_uid)

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
@unsubscribed_user
def view_unit(request, pid):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.view_properties'):
            raise PermissionDenied

    prop = Unit.objects.get(uuid=pid)

    context = {
        'p_id': pid,
        't': prop,
        'user': request.user,
    }
    return render(request, 'properties/unit_view.html', context)


@login_required
@unsubscribed_user
def edit_units(request, u_uid):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.change_unit'):
            raise PermissionDenied
    unit = Unit.objects.get(uuid=u_uid)

    if request.method == "POST":
        unit_name = request.POST.get('name')
        value = request.POST.get('value')
        unit_status = request.POST.get('status')
        area = request.POST.get('area')
        service_charge = request.POST.get('service_charge')
        no_of_parking = request.POST.get('parking')
        size = request.POST.get('size_unit')
        specify = request.POST.get('other')
        deposit = request.POST.get('deposit')

        unit.unit_name=unit_name
        unit.security_deposit=deposit
        unit.size=size
        unit.other_specify=specify
        unit.value=value
        unit.parking_assigned=no_of_parking
        unit.service_charge=service_charge
        unit.area=area
        unit.updated_by=request.user

        unit.save()

    context = {
        'unit': unit,
        'u_id': u_uid,
        'user': request.user,
    }

    return render(request, 'properties/edit_unit.html', context)


@login_required
@unsubscribed_user
def add_tenant(request, u_uid):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.add_tenant'):
            raise PermissionDenied

    unit = Unit.objects.get(uuid=u_uid)
    if request.method == "POST":
        print(request.POST)

        f_name = request.POST.get('f_name')
        l_name = request.POST.get('l_name')
        id_no = request.POST.get('id_no')
        mobile = request.POST.get('primary')
        secondary_mobile = request.POST.get('secondary')
        email = request.POST.get('email')
        date_of_occupancy = datetime.datetime.strptime(request.POST.get('date'), "%m/%d/%Y").strftime("%Y-%m-%d")
        username = get_random_username()
        pwrd = ''.join((random.choice(string.ascii_letters + string.digits) for i in range(8)))
        acc = AccTypes.objects.get(id=4)
        dis_type = request.POST.get('dis_type')
        discount = request.POST.get('discount')

        if request.FILES:
            pic = request.FILES['pic']
        else:
            pic = ''

        if request.POST.get('deprent') == "True":
            dep = True
        else:
            dep = False

        u = Users.objects.create_user(username=username, password=pwrd, email=email, acc_type=acc)
        u.save()
        p = Profile.objects.create(
            first_name=f_name, last_name=l_name, msisdn=mobile, id_number=id_no, user=u
        )
        wal_id = hapokashcreate()
        try:
            if wal_id['success']:
                p.hapokash = wal_id['wallet']['id']
                p.save()
            else:
                print('false')
        except:
            print(wal_id)

        p.save()
        t = Tenant.objects.create(
            secondary_msisdn=secondary_mobile, date_occupied=date_of_occupancy, unit=unit, profile=p, discount=discount,
            created_by=request.user, discount_type=dis_type, id_card=pic
        )
        t.save()

        inform(username, pwrd, email, f_name, Properties.objects.get(id=unit.property.id).property_name)

        unit.unit_status = "Occupied"
        unit.save()

        th = TenantHistory.objects.create(tenant=t, curr_unit=unit, start_date=datetime.datetime.today().date())
        th.save()

        if dep:
            rent = unit.value
            if dis_type == "Percent":
                rent = float(rent) - ((float(discount) / 100) * float(rent))
                print(rent)
            if dis_type == "Amount":
                rent = float(rent) - float(discount)
                print(rent)
            inv = apply_invoice(float(rent), float(unit.security_deposit), request.user, t)
            email_inform = inform_invoice(username, unit, email, f_name,
                                              Properties.objects.get(id=unit.property.id).property_name)
            # inv.save()

    if TenantHistory.objects.filter(curr_unit=unit, end_date=None).exists():
        return redirect('view-tenant', u_uid=unit.uuid)

    context = {
        'u_id': u_uid,
        'unit': unit,
        'user': request.user,
    }

    return render(request, 'properties/add_tenant.html', context)


def inform(u, p, e, n, prop):
    subject = "Welcome to {}".format(prop)
    html_message = render_to_string('properties/email_temp_04.html', {'n': n,'u':u, 'p':p})
    plain_message = strip_tags(html_message)
    message = '''
    Dear {}, 
    We are thrilled to have you on-board! 
    This email is to let you know that we are continuing to utilise the latest technologies available to provide you with an even better service. 
    A special login has been created for you as follows:
    Web URL:	mnestafrica.com
    username: {}
    Password:	{}
    It is recommended that you change your password after login in for the first time by choosing the Change Password link in the side menu of the web site.'''.format(
        n, u, p)
    try:
        send_mail(subject, plain_message, EMAIL_HOST_USER, [e], html_message=html_message,  fail_silently=False)
    except:
        print('failed')


def inform_invoice(u, unit, e, n, prop):
    subject = "Invoice for {}".format(prop)
    message = '''
    Dear {}, 
    This email is to let you know that an Invoice has been created for your unit {} at {}.
    login to your portal at	mnestafrica.com to view it under bills. 
    Your username is : {} incase you forgot.'''.format(n, unit.unit_name, prop, u)
    try:
        send_mail(subject, message, EMAIL_HOST_USER, [e], fail_silently=False)
        return True
    except:
        print('failed')
        return False


def get_random_username():
    username = ''.join(random.sample(string.ascii_uppercase, 2)) + '-' + ''.join(random.sample(string.digits, 6))
    if not Users.objects.filter(username=username).exists():
        return username
    else:
        get_random_username()


def apply_invoice(rent, dep, user, tenant):
    inv_no = increment_rent_invoice_number()

    if tenant.unit.property.rent_collection == "Spec_date":
        coll_day = tenant.unit.property.specific_day
        coll_day = int(coll_day)
    elif tenant.unit.property.rent_collection == "Occ_date":
        print(Tenant.objects.get(id=tenant.id).date_occupied)
        coll_day = Tenant.objects.get(id=tenant.id).date_occupied.date().day
        coll_day = int(coll_day)
    month = datetime.date.today()
    last_day = calendar.monthrange(month.year, month.month)[1]
    last_day = int(last_day)

    if coll_day > last_day:
        coll_day = last_day
    date = datetime.datetime(month.year, month.month, coll_day)
    nextmonth = date + relativedelta.relativedelta(months=1)
    print(nextmonth)

    # i = RentInvoice.objects.create(
    #     created_by=user, invoice_no=inv_no, invoice_for=tenant.profile.user, unit=tenant.unit, date_due=nextmonth
    # )
    # i.save()
    d = Invoice.objects.create(created_by=user, invoice_no=increment_invoice_number(), invoice_for=tenant.profile.user,
                               unit=tenant.unit)
    d.save()
    # inv_item1 = RentItems.objects.create(invoice=i, invoice_item='RENT', amount=round(rent, 2), description='RENT')
    # inv_item1.save()
    inv_item2 = InvoiceItems.objects.create(invoice=d, invoice_item='DEPOSIT', amount=round(dep, 2),
                                            description='DEPOSIT')
    inv_item2.save()
    # return i


@login_required
@unsubscribed_user
def view_tenant(request, u_uid):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.view_tenant'):
            raise PermissionDenied
    prop = TenantHistory.objects.get(curr_unit__uuid=u_uid, end_date=None).tenant
    unit = Unit.objects.filter(id=prop.unit.id)
    context = {
        'p_id': u_uid,
        'unit': unit,
        't': prop,
        'user': request.user,
        'history': TenantHistory.objects.filter(tenant=prop),
    }
    return render(request, 'properties/tenant_view.html', context)


@login_required
@unsubscribed_user
def remove_tenant(request, u_uid):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.view_tenant'):
            raise PermissionDenied
    prop = TenantHistory.objects.get(tenant__uuid=u_uid, end_date=None)
    prop.end_date = datetime.date.today()
    prop.save()
    unit = Unit.objects.get(id=prop.curr_unit.id)
    unit.unit_status = "Vacant"
    unit.save()

    return redirect('unit-list', u_uid=unit.property.uuid)


@login_required
@unsubscribed_user
def swap_tenant(request, u_uid):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.change_tenant'):
            raise PermissionDenied
    if request.method == "POST":
        old = Tenant.objects.get(unit__uuid=u_uid)
        new = request.POST.get('unit')

        th = TenantHistory.objects.get(tenant=old, curr_unit=old.unit, end_date=None)
        th.end_date = datetime.datetime.today().date()
        th.save()

        old.unit = Unit.objects.get(uuid=new)
        old.save()
        u = Unit.objects.get(uuid=u_uid)
        u.unit_status = "Vacant"
        u.save()

        n = Unit.objects.get(uuid=new)
        n.unit_status = "Occupied"
        n.save()

        th = TenantHistory.objects.create(tenant=old, curr_unit=n, start_date=datetime.datetime.today().date())
        th.save()

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
@unsubscribed_user
def get_unit(request):
    return


# File uploads
@login_required
@unsubscribed_user
def prop_file_upload(request):
    # declaring template
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.add_properties'):
            raise PermissionDenied

    csv_file = request.FILES['logo']
    # let's check if it is a csv file
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'THIS IS NOT A CSV FILE')
    data_set = csv_file.read().decode('UTF-8')
    print(data_set)
    # setup a stream which is when we loop through each line we are able to handle a data in a stream

    io_string = io.StringIO(data_set)
    next(io_string)
    next(io_string)
    next(io_string)
    for column in csv.reader(io_string, delimiter=',', quotechar="|"):
        print(column)
        created = Properties.objects.create(
            property_name=column[0],
            no_of_floors=column[1],
            property_value=column[2],
            no_of_units=column[3],
            parking=column[4],
            property_type=column[5],
            building_type=column[6],
            electricity=column[7],
            water=column[8],
            location_desc=column[9],
            penalty_type=column[10],
            penalty_value=column[11],
            rent_collection="Occ_date",
            long=-1.28759,
            lat=36.8109,
            created_by=request.user,
            company=CompanyProfile.objects.get(user=request.user).company
        )
        created.save()
    return redirect('prop-list')


@login_required
@unsubscribed_user
def tenant_file_upload(request):
    return


@login_required
@unsubscribed_user
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
@unsubscribed_user
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
@unsubscribed_user
def unit_file_upload(request, uid):
    # declaring template
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.add_unit'):
            raise PermissionDenied

    csv_file = request.FILES['logo']
    # let's check if it is a csv file
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'THIS IS NOT A CSV FILE')
    data_set = csv_file.read().decode('UTF-8')
    # setup a stream which is when we loop through each line we are able to handle a data in a stream

    io_string = io.StringIO(data_set)
    next(io_string)
    next(io_string)
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


@login_required
@unsubscribed_user
def staff(request):
    if request.user.acc_type.id == 4:
        raise PermissionDenied
    if request.user.acc_type.id == 5:
        raise PermissionDenied
    comp = CompanyProfile.objects.filter(company=CompanyProfile.objects.get(user=request.user).company).values_list(
        'user', flat=True)
    staff = Profile.objects.filter(user__in=comp, user__acc_type_id=5)
    print(staff)
    can_add = False
    if staff.count() < CompanyProfile.objects.get(user=request.user).company.no_of_emp:
        can_add = True
    if request.method == "POST":
        username = get_random_username_staff()
        email = request.POST.get('email')
        pwrd = ''.join((random.choice(string.ascii_letters + string.digits) for i in range(8)))
        f_name = request.POST.get('f_name')
        l_name = request.POST.get('l_name')
        mobile = request.POST.get('mobile')
        number = request.POST.get('id_no')
        props = request.POST.getlist('prop')
        perms = request.POST.getlist('perms')

        print(request.POST)

        try:
            acc = AccTypes.objects.get(id=5)
            user = Users.objects.create_user(username=username, password=pwrd, email=email, acc_type=acc)
            user.save()

            if user.pk:
                profile = Profile.objects.create(first_name=f_name, last_name=l_name, msisdn=mobile, id_number=number,
                                                 user=user)
                profile.save()

                cp = CompanyProfile.objects.create(user=user,
                                                   company=CompanyProfile.objects.get(user=request.user).company)
                cp.save()

                for p in props:
                    ps = PropertyStaff.objects.create(property_id=p, created_by=request.user, user=user)
                    ps.save()

                for par in perms:
                    user.user_permissions.add(Permission.objects.get(id=par))
                    user.user_permissions.all()


        except:
            print('error')
        inform_staff(username, pwrd, email, f_name, CompanyProfile.objects.get(user=request.user).company.name)

    perm = Permission.objects.filter(
        Q(name__contains='Can add properties') | Q(name__contains='Can change properties') | Q(
            name__contains='Can delete properties') | Q(name__contains='Can view properties') | Q(
            name__exact='Can add unit') | Q(name__exact='Can change unit') | Q(name__exact='Can delete unit') | Q(
            name__exact='Can view unit') | Q(name__exact='Can add tenant') | Q(name__exact='Can change tenant') |
        Q(name__exact='Can view tenant') | Q(name__exact='Can add invoice') | Q(name__exact='Can view tenant') | Q(
            name__exact='Can change invoice') | Q(name__exact='Can view invoice') | Q(
            name__exact='Can view tenant') | Q(name__exact='Can delete tenant') | Q(
            name__exact='Can add invoice items transaction') | Q(name__exact='Can view invoice items transaction') |
        Q(name__exact='Can add vacate notice') | Q(name__exact='Can change invoice items request') |
        Q(name__exact='Can add invoice items request') | Q(name__exact='Can add invoice items request')
    )

    context = {
        'user': request.user,
        'staff': staff,
        'props': Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company),
        'can_add': can_add,
        'perms': perm,
    }
    return render(request, 'properties/comany_staff.html', context)


@login_required
@unsubscribed_user
def edit_staff(request, uid):
    if request.user.acc_type.id == 4:
        raise PermissionDenied
    if request.user.acc_type.id == 5:
        raise PermissionDenied
    profile_staff = Profile.objects.get(id=uid)
    prop = PropertyStaff.objects.filter(user=profile_staff.user)
    comp = CompanyProfile.objects.filter(company=CompanyProfile.objects.get(user=request.user).company).values_list(
        'user', flat=True)

    staff = Profile.objects.filter(user__in=comp, user__acc_type_id=5)
    print(profile_staff)

    can_add = False
    if staff.count() < CompanyProfile.objects.get(user=request.user).company.no_of_emp:
        can_add = True
    if request.method == "POST":
        email = request.POST.get('email')
        f_name = request.POST.get('f_name')
        l_name = request.POST.get('l_name')
        mobile = request.POST.get('mobile')
        number = request.POST.get('id_no')
        props = request.POST.getlist('prop')
        perms = request.POST.getlist('perms')

        print(request.POST)

        try:
            user = Users.objects.get(id=profile_staff.user_id)
            user.email = email
            user.save()

            if user.pk:
                profile_staff.first_name = f_name
                profile_staff.last_name = l_name
                profile_staff.msisdn = mobile
                profile_staff.id_number = number
                profile_staff.save()

                PropertyStaff.objects.filter(user=profile_staff.user).delete()
                for p in props:
                    ps = PropertyStaff.objects.create(property_id=p, created_by=request.user, user=user)
                    ps.save()

                Permission.objects.filter(user=profile_staff.user).delete()
                for par in perms:
                    user.user_permissions.add(Permission.objects.get(id=par))
                    user.user_permissions.all()
                    print(par)


        except:
            print('error')

    perm = Permission.objects.filter(
        Q(name__contains='Can add properties') | Q(name__contains='Can change properties') | Q(
            name__contains='Can delete properties') | Q(name__contains='Can view properties') | Q(
            name__exact='Can add unit') | Q(name__exact='Can change unit') | Q(name__exact='Can delete unit') | Q(
            name__exact='Can view unit') | Q(name__exact='Can add tenant') | Q(name__exact='Can change tenant') |
        Q(name__exact='Can view tenant') | Q(name__exact='Can add invoice') | Q(name__exact='Can view tenant') | Q(
            name__exact='Can change invoice') | Q(name__exact='Can view invoice') | Q(
            name__exact='Can view tenant') | Q(name__exact='Can delete tenant') | Q(
            name__exact='Can add invoice items transaction') | Q(name__exact='Can view invoice items transaction') |
        Q(name__exact='Can add vacate notice') | Q(name__exact='Can change invoice items request') |
        Q(name__exact='Can add invoice items request') | Q(name__exact='Can add invoice items request')
    ).exclude(user=profile_staff.user)
    all_p = Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company).exclude(
        id__in=prop.values_list('property_id', flat=True))
    print(Permission.objects.filter(user=profile_staff.user))

    context = {
        'user': request.user,
        'staff': staff,
        'props': all_p,
        'can_add': can_add,
        'perms': perm,
        'profile_staff': profile_staff,
        'sel_p': prop,
        'sel_perm': Permission.objects.filter(user=profile_staff.user),

    }
    return render(request, 'properties/edit_staff.html', context)


def get_random_username_staff():
    username = ''.join(random.sample(string.ascii_uppercase, 2)) + '-' + ''.join(random.sample(string.digits, 3))
    if not Users.objects.filter(username=username).exists():
        return username
    else:
        get_random_username_staff()


def inform_staff(u, p, e, n, prop):
    subject = "Welcome to {}".format(prop)
    html_message = render_to_string('properties/email_temp_03.html', {'u':u, 'p':p})
    plain_message = strip_tags(html_message)
    message = '''
    Dear {}, 
    This email is to let you know that we are continuing to utilise the latest technologies available to provide you with an even better service. 
    A special login has been created for you as follows:
    Web URL:	mnestafrica.com/login
    username: {}
    Password: {}
    It is recommended that you change your password after login in for the first time by choosing the Change Password link in the side menu of the web site.'''.format(
        n, u, p)
    try:
        send_mail(subject, plain_message, EMAIL_HOST_USER, [e], html_message=html_message, fail_silently=False)
    except:
        print('failed')


def attach_people(request):
    pa = PeopleAttached.objects.filter(tenant__profile__user=request.user)
    if request.method == "POST":
        relation = request.POST.get('relation')
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        mobile = request.POST.get('mobile')

        people = PeopleAttached.objects.create(relationship=relation, created_by=request.user, f_name=fname,
                                               l_name=lname, tenant=Tenant.objects.get(profile__user=request.user),
                                               mobile_number=mobile)
        people.save()
    context = {
        'user': request.user,
        'people': pa
    }
    return render(request, 'properties/attach_extras.html', context)


def vacate_tenant(request, tid):
    tenant = Tenant.objects.get(pk=tid)
    context = {
        'user': request.user,
    }
    return render(request, '', context)


def vacate_tenant_request(request):
    tenant = Tenant.objects.get(profile__user=request.user)
    if VacateNotice.objects.filter(notice_from=tenant).exists():
        return redirect('generate-vacate-request')
    if request.method == "POST":
        print(request.POST)

        reason = request.POST.get('reason')
        moving_contact = request.POST.get('moving_contact')
        days_notice = request.POST.get('days_notice')
        date = request.POST.get('date')

        req = VacateNotice.objects.create(reason=reason, new_contacts=moving_contact, days_notice=days_notice,
                                          vacate_date=date, notice_from=tenant, created_by=request.user, unit=tenant.unit)
        req.save()
        return redirect('generate-vacate-request')
    context = {
        'user': request.user,
    }
    return render(request, 'properties/vacate_request.html', context)


@login_required
@unsubscribed_user
def delete_property(request, pid):
    if request.user.acc_type.id == 5:
        if not request.user.has_perm('properties.delete_properties'):
            raise PermissionDenied
    if request.user.acc_type.id == 1:
        prop = Properties.objects.get(id=pid)
        unit = Unit.objects.filter(property=prop)
        tenant = Tenant.objects.filter(unit__in=unit)
        for t in tenant:
            user = Users.objects.filter(id=t.profile.user.id)
            user.delete()
        tenant.delete()
        unit.delete()
        prop.delete()
        return redirect('all-props')
    elif request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        prop = Properties.objects.get(id=pid)
        unit = Unit.objects.filter(property=prop)
        unit.delete()
        prop.delete()
        return redirect('prop-list')


@login_required
@unsubscribed_user
def generate_vacate_notice(request):
    user = request.user
    tenant = Tenant.objects.get(profile__user=user)
    notice = VacateNotice.objects.get(notice_from=tenant)
    company = CompanyProfile.objects.get(company=tenant.unit.property.company, user__acc_type_id__in=[2, 3]).user

    landlord = Profile.objects.get(user=company)

    data = {
        'tenant': tenant,
        'landlord': landlord,
        'notice': notice,
    }
    pdf = render_to_pdf('properties/vacate.html', data)
    return HttpResponse(pdf, content_type='application/pdf')


@login_required
@unsubscribed_user
def inspection_report(request, id):
    if  request.user.acc_type.id == 4:
        raise PermissionDenied
    user = request.user
    vac = VacateNotice.objects.get(id=id)

    if request.method == "POST":
        fault = request.POST.get('faults')
        charge = request.POST.get('charges')

        insp = InspectionReport.objects.create(faults=fault, charges=charge, created_by=user, notice=vac)
        insp.save()

    if vac.status:
        insp = InspectionReport.objects.filter(notice=vac)
        context = {
            'user': user,
            'id': id,
            'ins': insp
        }
        return render(request, 'properties/insp_report_past.html', context)

    context = {
        'user': user,
        'id': id
    }
    return render(request, 'properties/inspection_report.html', context)


@login_required
@unsubscribed_user
def approve_vac(request, id):
    if  request.user.acc_type.id == 4:
        raise PermissionDenied

    vac = VacateNotice.objects.get(id=id)
    vac.status =True
    vac.save()

    return redirect('vacate-list')


@login_required
@unsubscribed_user
def vacate_list(request):
    if request.user.acc_type.id == 4:
        return PermissionDenied

    p = Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company)

    vacate = VacateNotice.objects.filter(unit__property__in=p, status=False)
    vac_app = VacateNotice.objects.filter(unit__property__in=p, status=True)

    context = {
        'user': request.user,
        'list': vacate,
        'vac_app': vac_app
    }
    return render(request, 'properties/vacate_list.html', context)


@login_required
@unsubscribed_user
def enquire_list(request):
    if request.user.acc_type.id == 4:
        return PermissionDenied

    company = CompanyProfile.objects.get(user=request.user)
    eq = Enquire.objects.filter(unit__property__company=company.company, response=None)

    context = {
        'eq': eq
    }
    return render(request, 'properties/enq_vacant_list.html', context)


@login_required
@unsubscribed_user
def respond_yes(request, u_id):
    if request.user.acc_type.id == 4:
        return PermissionDenied

    eq = Enquire.objects.get(uuid=u_id)
    eq.response = True
    eq.save()
    unit =Unit.objects.get(id=eq.unit_id)

    company = CompanyProfile.objects.get(company=unit.property.company, user__acc_type_id__in=[2, 3]).user
    landlord = Profile.objects.get(user=company)

    subject = "Enquiry for {}".format(eq.unit.unit_name)
    html_message = render_to_string('properties/email_temp_07.html',  {'unit': unit, 'landlord': landlord} )
    plain_message = strip_tags(html_message)
    message = '''
            This is a notice that your request for the unit has been approved. The contact details will be sent
            '''
    try:
        send_mail(subject, plain_message, EMAIL_HOST_USER, [eq.user.email], html_message=html_message,fail_silently=False)
    except:
        print('failed')
    return redirect('enquire-list')


@login_required
@unsubscribed_user
def respond_no(request, u_id):
    if request.user.acc_type.id == 4:
        return PermissionDenied

    eq = Enquire.objects.get(uuid=u_id)
    eq.response = False
    eq.save()

    subject = "Enquiry for {}".format(eq.unit.unit_name)
    message = '''
            This is a notice that your request for the unit has been rejected.
            '''
    html_message = render_to_string('properties/email_temp_06.html')
    plain_message = strip_tags(html_message)
    try:
        send_mail(subject, plain_message, EMAIL_HOST_USER, [eq.user.email], html_message=html_message, fail_silently=False)
    except:
        print('failed')
    return redirect('enquire-list')


@login_required
@unsubscribed_user
def enquire_unit(request, u_id):
    if request.user.acc_type.id != 4:
        return PermissionDenied

    company = CompanyProfile.objects.get(company=Unit.objects.get(id=u_id).property.company, user__acc_type_id__in=[2, 3]).user
    landlord = Profile.objects.get(user=company)
    eq = Enquire.objects.create(unit=Unit.objects.get(id=u_id), user=request.user, created_by=request.user)
    eq.save()
    send_email_enq(Unit.objects.get(id=u_id).unit_name, Profile.objects.get(user=request.user), landlord.user.email)
    return redirect('dashboard')


def send_email_enq(t, prof, l):
    subject = "Enquiry for {}".format(t)
    message = '''
        This is a notice that {} {} is enquiring about unit: {}. Login to respond.
        '''.format(prof.first_name, prof.last_name, t)

    html_message = render_to_string('properties/email_temp_05.html', {"prof": prof, "t": t})
    plain_message = strip_tags(html_message)
    try:
        send_mail(subject, plain_message, EMAIL_HOST_USER, [l], html_message=html_message,fail_silently=False)
    except:
        print('failed')


@login_required
@unsubscribed_user
def search_vacant(request):
    user = request.user
    units = []
    property = Properties.objects.all()
    if request.method == "POST":
        units = Unit.objects.filter(unit_status="Vacant", property_id=request.POST.get('prop')).order_by('floor')
        data =  list(units.values())
        return JsonResponse(data, safe=False)

    context = {
        'user': user,
        'u': units,
        'props': property,
        't': Tenant.objects.get(profile__user=user)

    }
    return render(request, 'properties/search_vacant.html', context)


@login_required
@unsubscribed_user
def document(request):
    user = request.user
    try:
        vac = VacateNotice.objects.get(notice_from=Tenant.objects.get(profile__user=user))
    except :
        vac = None

    try:
        non_com = NonCompliance.objects.filter(tenant=Tenant.objects.get(profile__user=user))
    except :
        non_com = None

    context = {
        'user': user,
        'vac': vac,
        'non_com': non_com,
        't': Tenant.objects.get(profile__user=user)

    }
    return render(request, 'properties/documents.html', context)


@login_required
@unsubscribed_user
def document_lease(request):
    user = request.user
    tenant = Tenant.objects.get(profile__user=user)
    company = CompanyProfile.objects.get(company=tenant.unit.property.company, user__acc_type_id__in=[2, 3]).user

    landlord = Profile.objects.get(user=company)
    try:
        sign = SignatureLandlord.objects.get(user=company)
    except SignatureLandlord.DoesNotExist:
        sign = None
    context = {
        'user': user,
        'tenant': Tenant.objects.get(profile__user=user),
        'landlord': landlord,
        'sign': sign
    }
    return render(request, 'properties/lease_agg.html', context)


@login_required
@unsubscribed_user
def document_lease_api(request):
    user = request.user
    tenant = Tenant.objects.get(profile__user=user)
    company = CompanyProfile.objects.get(company=tenant.unit.property.company, user__acc_type_id__in=[2, 3]).user

    landlord = Profile.objects.get(user=company)
    try:
        sign = SignatureLandlord.objects.get(user=company)
    except SignatureLandlord.DoesNotExist:
        sign = None
    context = {
        'user': user,
        'tenant': Tenant.objects.get(profile__user=user),
        'landlord': landlord,
        'sign': sign
    }
    return render(request, 'properties/lease_api.html', context)


@login_required
@unsubscribed_user
def document_non_comp(request, vid):
    user = request.user
    tenant = Tenant.objects.get(profile__user=user)
    non_comp = NonCompliance.objects.get(tenant=tenant, id=vid)

    sign = SignatureLandlord.objects.get(user=non_comp.created_by)
    context = {
        'user': user,
        't': Tenant.objects.get(profile__user=user),
        'non_comp': non_comp,
        'sign': sign
    }
    return render(request, 'properties/non_comp.html', context)


@login_required
@unsubscribed_user
def document_non_comp_api(request, vid):
    user = request.user
    tenant = Tenant.objects.get(profile__user=user)
    non_comp = NonCompliance.objects.get(tenant=tenant, id=vid)

    sign = SignatureLandlord.objects.get(user=non_comp.created_by)
    context = {
        'user': user,
        't': Tenant.objects.get(profile__user=user),
        'non_comp': non_comp,
        'sign': sign
    }
    return render(request, 'properties/violation_api.html', context)


@login_required
@unsubscribed_user
def document_vacate(request):
    user = request.user
    tenant = Tenant.objects.get(profile__user=user)
    company = CompanyProfile.objects.get(company=tenant.unit.property.company, user__acc_type_id__in=[2, 3]).user

    landlord = Profile.objects.get(user=company)

    context = {
        'user': user,
        'tenant': Tenant.objects.get(profile__user=user),
        'notice': VacateNotice.objects.get(notice_from=tenant),
        'landlord': landlord,

    }
    return render(request, 'properties/vacate_doc.html', context)


@login_required
@unsubscribed_user
def document_vacate_api(request):
    user = request.user
    tenant = Tenant.objects.get(profile__user=user)
    company = CompanyProfile.objects.get(company=tenant.unit.property.company, user__acc_type_id__in=[2, 3]).user

    landlord = Profile.objects.get(user=company)

    context = {
        'user': user,
        'tenant': Tenant.objects.get(profile__user=user),
        'notice': VacateNotice.objects.get(notice_from=tenant),
        'landlord': landlord,

    }
    return render(request, 'properties/vac_doc_api.html', context)


@login_required
@unsubscribed_user
def non_compliance(request, tenant):
    user = request.user
    t = Tenant.objects.get(id=tenant)
    non_comp = NonCompliance.objects.create(tenant=t, created_by=user, unit=t.unit, violation=request.POST.get('violation'))
    non_comp.save()

    return redirect('view-tenant', u_uid=t.unit.uuid)


#api
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_app_api(request):
    hist = TenantHistory.objects.get(tenant__profile__user_id=request.user.id, end_date=None)
    ser = TenantHistorySerializer(hist, many=False)
    return Response({'success': True, 'data': ser.data}, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def previous_app_api(request):
    hist = TenantHistory.objects.filter(tenant__profile__user_id=request.user.id, end_date__lt=datetime.date.today())
    ser = TenantHistorySerializer(hist, many=True)
    return Response({'success': True, 'data': ser.data}, status.HTTP_200_OK)


@swagger_auto_schema(method='post', request_body=VacantUnitAPISerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_vacate_notice_api(request):
    tenant = Tenant.objects.get(profile__user=request.user)
    if VacateNotice.objects.filter(notice_from=tenant).exists():
        return Response({"success": False, "message": "Vacate notice already sent   "}, status.HTTP_200_OK)
    if request.method == "POST":
        print(request.data)
        reason = request.data['reason']
        moving_contact = request.data['moving_contact']
        days_notice = request.data['days_notice']
        date = request.data['date']

        req = VacateNotice.objects.create(reason=reason, new_contacts=moving_contact, days_notice=days_notice,
                                          vacate_date=date, notice_from=tenant, created_by=request.user,
                                          unit=tenant.unit)
        req.save()

    return Response({"success": True, "message": "Vacate notice sent"}, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vacancy_search_within(request):
    user = request.user
    t = Tenant.objects.get(profile__user=user)
    units = Unit.objects.filter(property=t.unit.property, unit_status="Vacant")
    ser = VacantUnitSerializer(units, many=True)
    return Response({'success': True, 'data': ser.data}, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vacancy_search_api(request):
    user = request.user
    t = Tenant.objects.get(profile__user=user)
    units = Unit.objects.filter(unit_status="Vacant").exclude(property=t.unit.property).order_by('property_id')
    ser = VacantUnitSerializer(units, many=True)
    return Response({'success': True, 'data': ser.data}, status.HTTP_200_OK)


@swagger_auto_schema(method='post', request_body=EnquireAPISerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vacancy_enquire_api(request):
    if request.user.acc_type.id != 4:
        return PermissionDenied
    u_id = request.data['uuid']
    try:
        company = CompanyProfile.objects.get(company=Unit.objects.get(uuid=u_id).property.company, user__acc_type_id__in=[2, 3]).user
        landlord = Profile.objects.get(user=company)
        eq = Enquire.objects.create(unit=Unit.objects.get(uuid=u_id), user=request.user, created_by=request.user)
        eq.save()
        send_email_enq(Unit.objects.get(uuid=u_id).unit_name, Profile.objects.get(user=request.user), landlord.user.email)

        return Response({'success': True, 'message': "You will receive a response via email"}, status.HTTP_200_OK)
    except Unit.DoesNotExist:
        return Response({'success': False, 'message': "unit does not exist"}, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def documents_api(request):
    user = request.user
    try:
        non_com = NonCompliance.objects.filter(tenant=Tenant.objects.get(profile__user=user))
    except :
        non_com = None
    violations = []
    for n in non_com:
        violations.append({
            'link': request.build_absolute_uri(reverse('document-non-comp-api', kwargs={'vid': n.id} ))
        })

    data = {
        'vacate_notice': {
            'link': request.build_absolute_uri(reverse('document-vacate-api'))
        },
        'non_compliance': violations,
        'lease_agreement': {
            'unit': TenantHistory.objects.get(tenant__profile__user=user).curr_unit.unit_name,
            'link': request.build_absolute_uri(reverse('document-lease-api'))
        }
    }
    return Response({'success': True, 'data': data}, status=status.HTTP_200_OK)
