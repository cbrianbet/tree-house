import calendar
import datetime
from datetime import date

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError

from bills.models import RentInvoice, RentItems
from bills.views import increment_rent_invoice_number
from properties.models import Tenant
from authapp.models import Users
from tree_house.settings import EMAIL_HOST_USER


class Command(BaseCommand):
    help = 'Sends invoices out'

    #
    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        try:
            tenant = Tenant.objects.all()
            today = date.today().day
            month = date.today()
            last_day = calendar.monthrange(month.year, month.month)[1]
            last_day = int(last_day)
            today = int(today)
            print(today, last_day)
            for t in tenant:
                print(t)
                coll_day = 0
                if t.unit.property.rent_collection == "Spec_date":
                    coll_day = t.unit.property.specific_day
                    coll_day = int(coll_day)
                elif t.unit.property.rent_collection == "Occ_date":
                    coll_day = t.date_occupied.date().day
                    coll_day = int(coll_day)

                if coll_day > 3:
                    if coll_day > last_day:
                        coll_day = last_day
                    if today == (coll_day - 3):
                        apply_invoice(t.unit.value, calendar.month_name[month.month], Users.objects.get(id=1), t,
                                      '{}-{}-{}'.format(coll_day, calendar.month_name[month.month], month.year))

                elif coll_day == 0:
                    print('Not assigned')

                elif coll_day <= 3:
                    month = date.today()
                    year = month.year
                    month = month.month
                    if month == 1:
                        month = 12
                        year = year - 1
                    else:
                        month = month - 1

                    last_day = calendar.monthrange(year, month)[1]
                    last_day = int(last_day)

                    if coll_day == 3:
                        coll_day = last_day
                    else:
                        coll_day = coll_day + last_day - 3

                    if today == (coll_day - 3):
                        apply_invoice(t.unit.value, calendar.month_name[month], Users.objects.get(id=1), t,
                                      '{}-{}-{}'.format(coll_day, calendar.month_name[month], year))


        except Tenant.DoesNotExist:
            raise CommandError('Tenant does not exist')



def apply_invoice(rent, month, user, tenant, date):
    try:
        inv_no = increment_rent_invoice_number()
        i = RentInvoice.objects.create(created_by=user, invoice_no=inv_no, invoice_for=tenant.profile.user,
                                       unit=tenant.unit, date_due=datetime.datetime.now() + datetime.timedelta(days=3))
        i.save()
        inv_item1 = RentItems.objects.create(invoice=i, invoice_item='RENT FOR {}'.format(month),
                                             amount=round(rent, 2),
                                             description='RENT')
        inv_item1.save()
        i.email_inform = send_email(tenant, date)
        i.save()
        return True
    except:
        return False


def send_email(t, date):
    subject = "Invoice for {}".format(t.unit.property.property_name)
    message = '''
        Dear {}, 
        This email is to let you know that a Rent Invoice has been created for your unit {} at {}.
        login to your portal at	mnestafrica.com to view it under bills. The incoice is due on: {}  
        Your username is : {} incase you forgot.'''.format(t.profile.first_name, t.unit.unit_name,
                                                           t.unit.property.property_name, date,
                                                           t.profile.user.username)
    try:
        send_mail(subject, message, EMAIL_HOST_USER, [t.profile.user.email], fail_silently=False)
        return True
    except:
        print('failed')
        return False
