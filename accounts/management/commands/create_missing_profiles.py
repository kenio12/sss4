from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Profile

class Command(BaseCommand):
    help = 'Creates missing profiles for users'

    def handle(self, *args, **options):
        users = get_user_model().objects.all()
        for user in users:
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created profile for {user.email}'))
            else:
                self.stdout.write(f'Profile already exists for {user.email}')