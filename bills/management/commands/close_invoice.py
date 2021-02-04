import calendar
from datetime import date

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from bills.models import RentInvoice, RentItems, RentItemTransaction, Invoice, InvoiceItems, InvoiceItemsTransaction
from bills.views import increment_rent_invoice_number
from properties.models import Tenant, Properties, Unit
from authapp.models import Users
from tree_house.settings import EMAIL_HOST_USER


class Command(BaseCommand):
    help = 'Sends invoices out'

    #
    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        try:
            inv = RentInvoice.objects.filter(status=False)
            items = RentItems.objects.filter(invoice__in=inv)
            print(inv)

            for item in items:
                to_pay = item.amount + item.delay_penalties
                p = RentItemTransaction.objects.filter(invoice_item=item).aggregate(Sum('amount_paid'))
                w = RentItemTransaction.objects.filter(invoice_item=item).aggregate(Sum('waiver'))

                if p['amount_paid__sum'] is None:
                    p=0
                if w['waiver__sum'] is None:
                    w=0

                paid =  p['amount_paid__sum'] + w['waiver__sum']
                if paid >= to_pay:
                    invs = RentInvoice.objects.get(id=item.invoice.id)
                    invs.status = True
                    invs.save()

            inv = Invoice.objects.filter(status=False)
            items = InvoiceItems.objects.filter(invoice__in=inv)
            print(inv)

            for item in items:
                to_pay = item.amount
                p = InvoiceItemsTransaction.objects.filter(invoice_item=item).aggregate(Sum('amount_paid'))
                w = InvoiceItemsTransaction.objects.filter(invoice_item=item).aggregate(Sum('waiver'))
                print(p)
                if p['amount_paid__sum'] is None:
                    p=0
                if w['waiver__sum'] is None:
                    w=0
                paid =  p + w
                if paid >= to_pay:
                    invs = Invoice.objects.get(id=item.invoice.id)
                    invs.status = True
                    invs.save()

        except Tenant.DoesNotExist:
            raise CommandError('Failed')
