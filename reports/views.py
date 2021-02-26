from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect

from authapp.models import Users, Profile, Subscriptions
from properties.models import *


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
