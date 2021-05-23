from properties.models import *
from authapp.models import *
from bills.models import *
import django_filters


def departments(request):
    if request is None:
        return Properties.objects.none()

    comp = CompanyProfile.objects.get(user=request.user).company
    units = Unit.objects.filter(property__company=comp, unit_status="Occupied")
    ten_his = TenantHistory.objects.filter(end_date=None, curr_unit__in=units).values('curr_unit__property__property_name').distinct()
    return Properties.objects.filter(company=comp)


class TenantFilter(django_filters.FilterSet):
    unit__property = django_filters.filters.ModelChoiceFilter(queryset=departments)
    # unit__property = django_filters.ChoiceFilter()

    class Meta:
        model = Tenant
        fields = []
        exclude = ['id_card']
