from properties.models import *
from authapp.models import *
from bills.models import *
import django_filters


def departments(request):
    if request is None:
        return Properties.objects.none()

    comp = CompanyProfile.objects.get(user=request.user).company
    return Properties.objects.filter(company=comp).order_by('property_name')


class TenantFilter(django_filters.FilterSet):
    unit__property = django_filters.filters.ModelChoiceFilter(queryset=departments)
    # unit__property = django_filters.ChoiceFilter()

    class Meta:
        model = Tenant
        fields = []
        exclude = ['id_card']
