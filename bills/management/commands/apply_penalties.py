import calendar
from datetime import date

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from bills.models import RentInvoice, RentItems, RentItemTransaction, Invoice, InvoiceItems, InvoiceItemsTransaction
from bills.views import increment_rent_invoice_number
from properties.models import Tenant, Properties, Unit
from authapp.models import Users, Profile
from tree_house.settings import EMAIL_HOST_USER


class Command(BaseCommand):
    help = 'Apply penalties'

    #
    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        try:
            rent = RentInvoice.objects.filter(date_due__lt=date.today(), status=False)
            for r in rent:
                delta = date.today() - r.date_due
                print(delta.days)

                tenant = Tenant.objects.get(profile=Profile.objects.get(user=r.invoice_for))
                unit = Unit.objects.get(id=tenant.unit_id)
                prop = Properties.objects.get(id=unit.property_id)

                if prop.penalty_type == "percent":
                    # if RentItems.objects.get(invoice=r).delay_penalties == 0.00:
                    # paid = RentItemTransaction.objects.filter(invoice_item__invoice=r).aggregate(Sum('amount_paid'))
                    # w = RentItemTransaction.objects.filter(invoice_item__invoice=r).aggregate(Sum('waiver'))

                    # if paid['amount_paid__sum'] is None:
                    #     paid = 0
                    # else:
                    #     paid = paid['amount_paid__sum']
                    #
                    # if w['waiver__sum'] is None:
                    #     w = 0
                    # else:
                    #     w = w['waiver__sum']

                    # p = paid + w

                    pen = int(prop.penalty_value) * int(unit.value) * delta.days / 100
                    p = RentItems.objects.get(invoice=r)
                    p.delay_penalties = pen
                    p.save()
                elif prop.penalty_type == "fixed":

                    pen = int(prop.penalty_value) + int(unit.value) * delta.days
                    p = RentItems.objects.get(invoice=r)
                    p.delay_penalties = pen
                    p.save()

                print(unit)

        except RentInvoice.DoesNotExist:
            raise CommandError('Tenant does not exist')
