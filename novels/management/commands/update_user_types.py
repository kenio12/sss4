from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = '特定のメールアドレスを持つユーザーの user_type を更新する'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        # @example.com のメールアドレスを持つユーザーを検索
        users_to_update = User.objects.filter(email__endswith='@example.com')
        updated_count = users_to_update.update(user_type=User.OLD_SSS_WRITER)
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} users to OLD_SSS_WRITER.'))