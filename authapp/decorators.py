from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect, render
from properties.models import *


def unsubscribed_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.acc_type.id == 2 or request.user.acc_type.id == 3 or request.user.acc_type.id == 5:
            company = CompanyProfile.objects.get(user=request.user).company
            try:
                check = SubscriptionsCompanies.objects.get(company=company)

                if check.date_end is None:
                    return redirect('subs-pick')
                elif check.date_end < datetime.today().date():
                    return redirect('subs-pick')

                print(company, check)
            except SubscriptionsCompanies.DoesNotExist:
                SubscriptionsCompanies.objects.create(company=company)
                return redirect('subs-pick')

            return view_func(request, *args, **kwargs)
        if request.user.acc_type.id == 4:
            tenant = TenantHistory.objects.get(end_date=None, tenant__profile__user=request.user).curr_unit
            try:
                check = SubscriptionsCompanies.objects.get(company=tenant.property.company)

                if check.date_end is None:
                    return render(request, 'authapp/error-500.html')
                if check.date_end < datetime.today().date():
                    return render(request, 'authapp/error-500.html')

            except SubscriptionsCompanies.DoesNotExist:
                return render(request, 'authapp/error-500.html')

            return view_func(request, *args, **kwargs)
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func