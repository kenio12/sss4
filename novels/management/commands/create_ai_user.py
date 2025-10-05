import os
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from accounts.models import User

class Command(BaseCommand):
    help = 'Creates an AI user for title proposals if it does not exist'

    def handle(self, *args, **options):
        email = os.environ.get('AI_USER_EMAIL')
        nickname = os.environ.get('AI_USER_NICKNAME')
        password = os.environ.get('AI_USER_PASSWORD')
        try:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'nickname': nickname,
                    'password': password,
                    'user_type': User.AI,
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully created AI user: {email}'))
            else:
                self.stdout.write(self.style.WARNING(f'AI user already exists: {email}'))
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f'Error creating AI user: {str(e)}'))