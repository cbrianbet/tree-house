from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from authapp.models import Users, Profile, Subscriptions
from properties.models import Properties, Companies, CompanyProfile


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
    subs = Subscriptions.objects.all()
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
