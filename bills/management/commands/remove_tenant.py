import datetime
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from properties.models import Unit, TenantHistory, VacateNotice


class Command(BaseCommand):
    help = 'Vacate Tenant'

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
