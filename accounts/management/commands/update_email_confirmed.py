"""
既存ユーザーのemail_confirmedを更新するmanagement command

実メールアドレス（@example.com以外、user_で始まらない）: email_confirmed=True
仮メールアドレス（@example.com、user_で始まる）: email_confirmed=False
"""
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = '既存ユーザーのemail_confirmedを更新'

    def handle(self, *args, **options):
        # 実メールアドレスのユーザー（@example.com以外、user_で始まらない）
        real_email_users = User.objects.exclude(
            email__icontains='@example.com'
        ).exclude(
            email__startswith='user_'
        )

        # 仮メールアドレスのユーザー（@example.comまたはuser_で始まる）
        fake_email_users = User.objects.filter(
            email__icontains='@example.com'
        ) | User.objects.filter(
            email__startswith='user_'
        )

        self.stdout.write(f'実メールアドレスユーザー: {real_email_users.count()}人')
        self.stdout.write(f'仮メールアドレスユーザー: {fake_email_users.count()}人')

        # 実メールアドレスのユーザーをemail_confirmed=Trueに更新
        real_updated = real_email_users.update(email_confirmed=True)
        self.stdout.write(self.style.SUCCESS(f'実メールアドレスユーザー更新完了: {real_updated}人'))

        # 仮メールアドレスのユーザーをemail_confirmed=Falseに更新
        fake_updated = fake_email_users.update(email_confirmed=False)
        self.stdout.write(self.style.SUCCESS(f'仮メールアドレスユーザー更新完了: {fake_updated}人'))

        self.stdout.write(self.style.SUCCESS('更新完了！'))
