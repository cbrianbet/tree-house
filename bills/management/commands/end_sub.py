import calendar
from datetime import date

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from bills.models import RentInvoice, RentItems, RentItemTransaction, Invoice, InvoiceItems, InvoiceItemsTransaction
from bills.views import increment_rent_invoice_number
from properties.models import Tenant, Properties, Unit
from properties.models import *
from tree_house.settings import EMAIL_HOST_USER


class Command(BaseCommand):
    help = 'End Subscriptions'

    #
    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        try:
            subs = SubscriptionsCompanies.objects.filter(date_end__lt=date.today())
            subs.delete()
        except:
            print("Try again")
