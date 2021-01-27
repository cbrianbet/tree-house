from django.core.management.base import BaseCommand, CommandError
from properties.models import Tenant
from authapp.models import Users

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'
    #
    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        try:
            poll = Tenant.objects.filter()
            print(poll)
        except Tenant.DoesNotExist:
            raise CommandError('Poll  does not exist')

            # poll.opened = False
            # poll.save()
            #
            # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))