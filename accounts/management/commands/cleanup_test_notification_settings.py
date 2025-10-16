"""
テストユーザーの通知設定削除コマンド
ダミーメールアドレス（example.com等）やemail_confirmed=Falseのユーザーの
通知設定を削除する
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import EmailNotificationSettings

User = get_user_model()

class Command(BaseCommand):
    help = 'テストユーザーの通知設定を削除'

    def handle(self, *args, **options):
        # テストユーザーの通知設定を取得
        test_settings = EmailNotificationSettings.objects.filter(
            user__email__icontains='example.com'
        ) | EmailNotificationSettings.objects.filter(
            user__email_confirmed=False
        )

        count = test_settings.count()

        if count == 0:
            self.stdout.write(self.style.WARNING('削除対象の通知設定なし'))
            return

        # 削除実行
        test_settings.delete()

        self.stdout.write(
            self.style.SUCCESS(f'テストユーザーの通知設定を削除: {count}件')
        )

        # 残った通知設定数を確認
        remaining = EmailNotificationSettings.objects.count()
        real_users = EmailNotificationSettings.objects.filter(
            user__email_confirmed=True
        ).exclude(
            user__email__icontains='example.com'
        ).count()

        self.stdout.write(
            self.style.SUCCESS(f'残った通知設定: {remaining}件（実ユーザー: {real_users}件）')
        )
