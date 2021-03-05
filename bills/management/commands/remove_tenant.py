import calendar
import datetime
from datetime import date

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from bills.models import RentInvoice, RentItems, RentItemTransaction, Invoice, InvoiceItems, InvoiceItemsTransaction
from bills.views import increment_rent_invoice_number
from properties.models import Tenant, Properties, Unit, TenantHistory, VacateNotice
from authapp.models import Users, Profile
from tree_house.settings import EMAIL_HOST_USER


class Command(BaseCommand):
    help = 'Vacate Tenant'

    #
    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        try:
            van = VacateNotice.objects.filter(vacate_date=date.today())
            for v in van:
                prop = TenantHistory.objects.get(tenant__uuid=v.notice_from.uuid, end_date=None)
                prop.end_date = datetime.date.today()
                prop.save()
                unit = Unit.objects.get(id=prop.curr_unit.id)
                unit.unit_status = "Vacant"
                unit.save()

        except:
            raise CommandError('Tenant does not exist')
