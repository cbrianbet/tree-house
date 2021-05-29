from properties.models import *
from authapp.models import *
from bills.models import *
import django_filters


def departments(request):
    if request is None:
        return Properties.objects.none()

    comp = CompanyProfile.objects.get(user=request.user).company
    return Properties.objects.filter(company=comp).order_by('property_name')


def tenant(request):
    if request is None:
        return Users.objects.none()

    comp = CompanyProfile.objects.get(user=request.user).company
    return Users.objects.filter(unit__property__company=comp).order_by('unit')


def unit(request):
    if request is None:
        return Unit.objects.none()

    comp = CompanyProfile.objects.get(user=request.user).company
    print(request.GET)
    try:
        if request.GET['unit__property']:
            return Unit.objects.filter(property__company=comp, property_id=request.GET['unit__property']).order_by('unit_name')
    except :
        Unit.objects.filter(property__company=comp).order_by('unit_name')
    return Unit.objects.filter(property__company=comp).order_by('unit_name')


class TenantFilter(django_filters.FilterSet):
    unit__property = django_filters.filters.ModelChoiceFilter(queryset=departments)

    # unit__property = django_filters.ChoiceFilter()

    class Meta:
        model = Tenant
        fields = []
        exclude = ['id_card']


FILTER_CHOICES = (
    (False, 'Open'),
    (True, 'Closed'),
)


class InvoiceFilter(django_filters.FilterSet):
    unit__property = django_filters.filters.ModelChoiceFilter(queryset=departments)
    # invoice_for = django_filters.filters.ModelChoiceFilter(queryset=tenant)
    # id = django_filters.filters.ModelChoiceFilter(queryset=tenant)
    unit = django_filters.filters.ModelChoiceFilter(queryset=unit)
    status = django_filters.ChoiceFilter(choices=FILTER_CHOICES)

    class Meta:
        model = Tenant
        fields = []
        exclude = ['id_card']


class LedgerFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=FILTER_CHOICES)
    date_due = django_filters.DateFromToRangeFilter()

    class Meta:
        model = RentInvoice
        fields = []
