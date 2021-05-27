import calendar
from itertools import chain

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count
from django.db.models.functions import ExtractMonth, ExtractYear
from django.shortcuts import render, redirect

from authapp.decorators import unsubscribed_user
from authapp.models import Users, Profile, Subscriptions
from bills.models import *
from properties.models import *
from reports.filters import TenantFilter, InvoiceFilter


@login_required
def all_users(request):
    all_users = Profile.objects.filter(Q(user__acc_type_id=2) | Q(user__acc_type_id=3) | Q(user__acc_type_id=5))

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
    subs = Subscriptions.objects.filter(is_active=True).order_by('value')
    if request.method == "POST":
        val = request.POST.get('val')
        name = request.POST.get('name')
        duration = request.POST.get('duration')
        desc = request.POST.get('desc')
        prop = request.POST.get('prop')

        sub = Subscriptions.objects.create(created_by=request.user, value=val, name=name, duration=duration,
                                           description=desc, property_limit=prop)
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
def edit_subs(request, uuid):
    if request.user.acc_type.id != 1:
        raise PermissionDenied

    sub = Subscriptions.objects.get(uuid=uuid)
    if request.method == "POST":
        val = request.POST.get('val')
        name = request.POST.get('name')
        duration = request.POST.get('duration')
        desc = request.POST.get('desc')
        prop = request.POST.get('prop')

        sub.updated_by=request.user
        sub.value=val
        sub.name=name
        sub.duration=duration
        sub.description=desc
        sub.property_limit=prop
        sub.save()
        return redirect('all-subs')

    context = {
        'user': request.user,
        'sub': sub,
    }
    return render(request, 'reports/editsubs.html', context)


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


@login_required
@unsubscribed_user
def tenant_listing(request):
    if request.user == 4:
        raise PermissionDenied
    comp = CompanyProfile.objects.get(user=request.user).company
    units = Unit.objects.filter(property__company=comp, unit_status="Occupied")
    unit_total = Unit.objects.filter(property__company=comp)
    ten_his = TenantHistory.objects.filter(end_date=None, curr_unit__in=units)
    active_tenant = Tenant.objects.filter(id__in=ten_his.values_list('tenant_id', flat=True))
    try:
        if request.GET['unit__property']:
            unit_total = Unit.objects.filter(property__company=comp, property_id__in=request.GET['unit__property'])
    except:
        unit_total = Unit.objects.filter(property__company=comp)

    filter = TenantFilter(request.GET, request=request, queryset=active_tenant)
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


@login_required
@unsubscribed_user
def invoice_report(request):
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        comp = CompanyProfile.objects.get(user=request.user).company
        prop = Properties.objects.filter(company=comp).values_list('id', flat=True)
        rent_inv = RentInvoice.objects.filter(unit__property__in=prop)
        invoices = Invoice.objects.filter(unit__property__in=prop)
        inv_items = InvoiceItems.objects.filter(invoice__in=invoices)
        rent_inv_items = RentItems.objects.filter(invoice__in=rent_inv)
        rent_inv_trans = RentItemTransaction.objects.filter(invoice_item__in=rent_inv_items)
        inv_trans = InvoiceItemsTransaction.objects.filter(invoice_item__in=inv_items)

        filter = InvoiceFilter(request.GET, request=request, queryset=rent_inv)
        rent_inv = filter.qs
        filter = InvoiceFilter(request.GET, request=request, queryset=invoices)
        invoices = filter.qs
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
            print(inv)

            a.append({
                'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
                'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username,
                'created_at': inv.created_at, 'paid': paid, "status": inv.status,
                'tenant': Profile.objects.get(user=inv.invoice_for)
            })

        r = []
        for inv in rent_inv:
            total = 0
            paid = 0
            inv_items = RentItems.objects.filter(invoice=inv)
            delay = 0
            for i in inv_items:
                total = total + i.amount
                delay = delay + i.delay_penalties
                trans = RentItemTransaction.objects.filter(invoice_item=i)
                for ab in trans:
                    paid = ab.amount_paid + paid

            r.append({
                'invoice_no': inv.invoice_no, 'property_name': inv.unit.property.property_name, 'amount': total,
                'uuid': inv.uuid, 'unit_name': inv.unit.unit_name, 'username': inv.created_by.username, 'delay': delay,
                'created_at': inv.created_at, 'paid': paid, "status": inv.status,
                'tenant': Profile.objects.get(user=inv.invoice_for)
            })

    else:
        raise PermissionDenied
    print(invoices.count())

    context = {
        'user': request.user,
        'invoice_number': rent_inv.count() + invoices.count(),
        'open_inv': rent_inv.filter(status=False).count() + invoices.filter(status=False).count(),
        'closed_inv': rent_inv.filter(status=True).count() + invoices.filter(status=True).count(),
        'inv': a + r,
        'InvFilter': filter
    }
    return render(request, 'reports/invoice_listings.html', context)


@login_required
@unsubscribed_user
def tenants_ledge_listing(request):
    if request.user == 4:
        raise PermissionDenied
    comp = CompanyProfile.objects.get(user=request.user).company
    units = Unit.objects.filter(property__company=comp, unit_status="Occupied")
    unit_total = Unit.objects.filter(property__company=comp)
    ten_his = TenantHistory.objects.filter(end_date=None, curr_unit__in=units)
    active_tenant = Tenant.objects.filter(id__in=ten_his.values_list('tenant_id', flat=True))

    filter = TenantFilter(request.GET, request=request, queryset=active_tenant)
    active_tenant = filter.qs

    context = {
        'user': request.user,
        'active': active_tenant,
    }
    return render(request, 'reports/tenants.html', context)


@login_required
@unsubscribed_user
def tenant_ledger(request, uuid):
    if request.user.acc_type.id == 2 or request.user.acc_type.id == 3:
        comp = CompanyProfile.objects.get(user=request.user).company
        prop = Properties.objects.filter(company=comp).values_list('id', flat=True)
        rent_inv = RentInvoice.objects.filter(unit__property__in=prop,
                                              invoice_for_id=Tenant.objects.get(uuid=uuid).profile.user.id)
        rent_ann = rent_inv.annotate(month=ExtractMonth('date_due'),
                                     year=ExtractYear('date_due'), ).order_by('date_due').values('month',
                                                                                                 'year').annotate(
            total=Count('*')).values('month', 'year', 'total', 'uuid', 'status')
        print(rent_ann)
        invoices = Invoice.objects.filter(unit__property__in=prop,
                                          invoice_for=Tenant.objects.get(uuid=uuid).profile.user)
        inv_items = InvoiceItems.objects.filter(invoice__in=invoices)
        rent_inv_items = RentItems.objects.filter(invoice__in=rent_inv)
        rent_inv_trans = RentItemTransaction.objects.filter(invoice_item__in=rent_inv_items)
        inv_trans = InvoiceItemsTransaction.objects.filter(invoice_item__in=inv_items)

        filter = InvoiceFilter(request.GET, request=request, queryset=rent_inv)
        rent_inv = filter.qs
        filter = InvoiceFilter(request.GET, request=request, queryset=invoices)
        invoices = filter.qs
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
                'created_at': inv.created_at, 'paid': paid, "status": inv.status,
                'tenant': Profile.objects.get(user=inv.invoice_for)
            })

        r = []
        rent_total = 0
        late_total = 0
        other_total = 0
        waiver_total = 0
        paid_total = 0
        bal_total = 0
        for inv in rent_ann:
            balance = 0
            delay = 0
            other = 0
            date_paid = None
            rent_due = 0
            waiver = 0
            total = 0
            paid = 0
            inv_items = RentItems.objects.filter(invoice__uuid=inv['uuid'])
            for i in inv_items:
                total = total + i.amount
                delay = delay + i.delay_penalties
                trans = RentItemTransaction.objects.filter(invoice_item=i).order_by('date_paid')
                for ab in trans:
                    paid = ab.amount_paid + paid
                    waiver = ab.waiver + waiver
                    date_paid = ab.date_paid
            credit = total + delay + other
            debit = paid + waiver
            balance = credit - debit
            rent_due = total

            #totals
            waiver_total= waiver_total + waiver
            rent_total= rent_total + rent_due
            late_total= late_total + delay
            other_total= other_total + other
            paid_total= paid_total + paid
            bal_total= bal_total + balance
            
            r.append({
                'amount': total, 'uuid': inv['uuid'], 'paid': paid, "status": inv['status'], 'waiver': "{:.2f}".format(waiver),
                'other': "{:.2f}".format(other), 'date_paid': date_paid, 'balance': "{:.2f}".format(balance), 'delay': delay, 'rent': rent_due,
                'month': calendar.month_name[inv['month']], 'year': inv['year'],
            })


    else:
        raise PermissionDenied

    context = {
        'user': request.user,
        'invoice_number': rent_inv.count() + invoices.count(),
        'tenant': Tenant.objects.get(uuid=uuid),
        'inv': r,
        'InvFilter': filter,
        'rent_total': "{:.2f}".format(rent_total),
        "late_total": "{:.2f}".format(late_total),
        'other_total': "{:.2f}".format(other_total),
        'waiver_total': "{:.2f}".format(waiver_total),
        'paid_total': "{:.2f}".format(paid_total),
        'bal_total': "{:.2f}".format(bal_total)
    }
    return render(request, 'reports/tenant_ledger.html', context)


@login_required
@unsubscribed_user
def staffList(request):
    if request.user.acc_type.id == 4:
        raise PermissionDenied
    if request.user.acc_type.id == 5:
        raise PermissionDenied
    comp = CompanyProfile.objects.filter(company=CompanyProfile.objects.get(user=request.user).company).values_list(
        'user', flat=True)
    staff = Profile.objects.filter(user__in=comp, user__acc_type_id=5)
    print(staff)

    context = {
        'user': request.user,
        'staff': staff,
        'props': Properties.objects.filter(company=CompanyProfile.objects.get(user=request.user).company),
    }
    return render(request, 'reports/staff_listings.html', context)
