import calendar
import datetime
from datetime import date

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.http import HttpResponse

from bills.models import RentInvoice, RentItems
from bills.views import increment_rent_invoice_number
from properties.models import Tenant, Unit, Properties
from authapp.models import Users, Profile
from tree_house.settings import EMAIL_HOST_USER


def send_invoice(request):
    try:
        tenant = Tenant.objects.all()
        today = date.today().day
        ttoday = date.today()
        last_day = calendar.monthrange(ttoday.year, ttoday.month)[1]
        last_day = int(last_day)
        today = int(today)
        print(today, last_day, ttoday)
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
                    apply_invoice(t.unit.value, calendar.month_name[ttoday.month], Users.objects.get(id=1), t,
                                  '{}-{}-{}'.format(coll_day, calendar.month_name[ttoday.month], ttoday.year))

            elif coll_day == 0:
                print('Not assigned')

            elif coll_day <= 3:
                ttoday = date.today()
                year = ttoday.year
                month = ttoday.month
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
        print('Tenant does not exist')
        raise CommandError('Tenant does not exist')
    return HttpResponse("DOne")


def apply_invoice(rent, month, user, tenant, date):
    try:
        inv_no = increment_rent_invoice_number()
        i = RentInvoice.objects.create(created_by=user, invoice_no=inv_no, invoice_for=tenant.profile.user,
                                       unit=tenant.unit, date_due=datetime.datetime.now() + datetime.timedelta(days=3))
        i.save()
        if i.pk:
            inv_item1 = RentItems.objects.create(invoice_id=i.id, invoice_item='RENT FOR {}'.format(month),
                                                 amount=round(int(rent), 2), description='RENT')
            inv_item1.save()
        print("Heree....")
        i.email_inform = send_email(tenant, date)
        i.save()
        return True
    except Exception as e:
        print(e)
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
    except Exception as e:
        print(e)
        return False


def apply_penalty(request):
    try:
        rent = RentInvoice.objects.filter(date_due__lt=date.today(), status=False)
        for r in rent:
            delta = date.today() - r.date_due

            tenant = Tenant.objects.get(profile=Profile.objects.get(user=r.invoice_for))
            unit = Unit.objects.get(id=tenant.unit_id)
            prop = Properties.objects.get(id=unit.property_id)

            print(r)
            if prop.penalty_type == "percent":
                pen = (int(unit.value) * (int(prop.penalty_value) / 100)) * delta.days
                try:
                    p = RentItems.objects.get(invoice=r)
                    p.delay_penalties = pen
                    p.save()
                    send_email_delay(Tenant.objects.get(profile__user=r.invoice_for), r, delta.days, pen)
                except Exception as e:
                    print(e)
            elif prop.penalty_type == "fixed":

                pen = int(unit.value) + (int(prop.penalty_value) * delta.days)

                try:
                    p = RentItems.objects.get(invoice=r)
                    p.delay_penalties = pen
                    p.save()
                    send_email_delay(Tenant.objects.get(profile__user=r.invoice_for), r, delta.days, pen)
                except Exception as e:
                    print(e)

            print(unit)

    except RentInvoice.DoesNotExist:
        print('Invoice does not exist')
    except Tenant.DoesNotExist:
        print('Tenant does not exist')
    return HttpResponse("DONE")


def send_email_delay(t, r, days, pens):
    subject = "LATENESS PENALTIES"
    message = '''
        Dear {},
        This email is to let you know that Rent Invoice ({}) for your unit {} at {} was due on {}. The penalties that have acured over {} days are {}.
        Login to your portal at	mnestafrica.com to view it under bills. 
        Your username is : {} incase you forgot.'''.format(t.profile.first_name, r.invoice_no, t.unit.unit_name,
                                                           t.unit.property.property_name, r.date_due, days, pens,
                                                           t.profile.user.username)
    try:
        send_mail(subject, message, EMAIL_HOST_USER, [t.profile.user.email], fail_silently=False)
        return True
    except Exception as e:
        print(e)
        return False
