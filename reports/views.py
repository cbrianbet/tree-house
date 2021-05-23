from itertools import chain

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect

from authapp.models import Users, Profile, Subscriptions
from bills.models import *
from properties.models import *
from reports.filters import TenantFilter


@login_required
def all_users(request):
    all_users = Profile.objects.filter(Q(user__acc_type_id=2) | Q(user__acc_type_id=3) | Q(user__acc_type_id=5) )

    context = {
        'user': request.user,
        'list': all_users,
    }
    return render(request, 'reports/all_users.html', context)


@login_required
def all_props(request):
    all_props = Properties.objects.all()

    context = {
        'user': request.user,
        'list': all_props,
    }
    return render(request, 'reports/all_properties.html', context)


@login_required
def all_comps(request):
    all_comp = CompanyProfile.objects.filter(user__acc_type_id=3)

    context = {
        'user': request.user,
        'list': all_comp,
    }
    return render(request, 'reports/all_companies.html', context)


@login_required
def all_subs(request):
    if request.user.acc_type.id != 1:
        raise PermissionDenied
    subs = Subscriptions.objects.filter(is_active=True)
    if request.method == "POST":
        val = request.POST.get('val')
        name = request.POST.get('name')
        duration = request.POST.get('duration')
        desc = request.POST.get('desc')

        sub = Subscriptions.objects.create(created_by=request.user, value=val, name=name, duration=duration, description=desc)
        sub.save()

    context = {
        'user': request.user,
        'list': subs,
    }
    return render(request, 'reports/subs.html', context)


@login_required
def delete_subs(request, uuid):
    if request.user.acc_type.id != 1:
        raise PermissionDenied
    try:
        sub = Subscriptions.objects.get(uuid=uuid)
        if SubscriptionsCompanies.objects.filter(subs=sub).exists():
            sub.is_active = False
            sub.save()
        else:
            sub.delete()
        return redirect('all-subs')
    except Subscriptions.DoesNotExist():
        raise PermissionDenied


@login_required
def tenant_list(request, id):
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        comp = CompanyProfile.objects.get(user=request.user).company
        units = Unit.objects.filter(property__company=comp, unit_status="Occupied", property_id=id)
        t = TenantHistory.objects.filter(end_date=None, curr_unit__in=units)
        context = {
            'user': request.user,
            'list': t,
        }
        return render(request, 'reports/tenant_list.html', context)


def tenant_listing(request):
    if request.user == 4:
        raise PermissionDenied
    comp = CompanyProfile.objects.get(user=request.user).company
    units = Unit.objects.filter(property__company=comp, unit_status="Occupied")
    unit_total = Unit.objects.filter(property__company=comp)
    ten_his = TenantHistory.objects.filter(end_date=None, curr_unit__in=units)
    active_tenant = Tenant.objects.filter(id__in=ten_his.values_list('tenant_id', flat=True))
    if request.GET:
        unit_total = Unit.objects.filter(property__company=comp, property_id__in=request.GET['unit__property'])

    filter = TenantFilter(request.GET, request=request, queryset=active_tenant)
    print(request.GET)
    active_tenant = filter.qs
    try:
        occ = (active_tenant.count() / unit_total.count()) * 100
    except ZeroDivisionError:
        occ = 0
    context = {
        'user': request.user,
        'active': active_tenant,
        'units': unit_total.count(),
        'tenant': active_tenant.count(),
        'occ': "{:.2f}".format(occ),
        'TenantFilter': filter
    }
    return render(request, 'reports/tenant_listings.html', context)


def invoice_report(request):

    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        comp = CompanyProfile.objects.get(user=request.user).company
        prop = Properties.objects.filter(company=comp).values_list('id', flat=True)
        rent_inv =  RentInvoice.objects.filter(unit__property__in=prop)
        invoices =  Invoice.objects.filter(unit__property__in=prop)
        inv_items = InvoiceItems.objects.filter(invoice__in=invoices)
        rent_inv_items = RentItems.objects.filter(invoice__in=rent_inv)
        rent_inv_trans = RentItemTransaction.objects.filter(invoice_item__in=rent_inv_items)
        inv_trans = InvoiceItemsTransaction.objects.filter(invoice_item__in=inv_items)
        a = []
        for inv in invoices:
            total = 0
            paid = 0
            inv_items = InvoiceItems.objects.filter(invoice=inv)
            for i in inv_items:
                total = total + i.amount
                trans = InvoiceItemsTransaction.objects.filter(invoice_item=i)
                for ab in trans:
                    paid = ab.amount_paid + paid

            a.append({
                'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
                'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
                'created_at': inv.created_at, 'paid': paid, "status": inv.status
            })


        r = []
        for inv in rent_inv:
            total = 0
            paid = 0
            inv_items = RentItems.objects.filter(invoice=inv)
            for i in inv_items:
                total = total + i.amount
                trans = RentItemTransaction.objects.filter(invoice_item=i)
                for ab in trans:
                    paid = ab.amount_paid + paid

            r.append({
                'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
                'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
                'created_at': inv.created_at, 'paid': paid, "status": inv.status
            })


    else:
        raise PermissionDenied
    print(invoices.count())

    context = {
        'user': request.user,
        'invoice_number': rent_inv.count() + invoices.count(),
        'open_inv': rent_inv.filter(status=False).count() + invoices.filter(status=False).count(),
        'closed_inv': rent_inv.filter(status=True).count() + invoices.filter(status=True).count(),
        'inv':a + r,
    }
    return render(request, 'reports/invoice_listings.html', context)
