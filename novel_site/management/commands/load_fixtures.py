from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Load all fixtures data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading fixtures...')
        call_command('loaddata', 'novels.json')
        self.stdout.write(self.style.SUCCESS('Successfully loaded fixtures')) 