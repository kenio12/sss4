"""
全ユーザーにEmailNotificationSettings作成コマンド

既存ユーザーには通知設定が自動作成されてへんから、
このコマンドで一括作成する
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import EmailNotificationSettings

User = get_user_model()


class Command(BaseCommand):
    help = '全ユーザーにEmailNotificationSettings（メール通知設定）を作成'

    def handle(self, *args, **options):
        users = User.objects.all()
        created_count = 0
        existing_count = 0

        for user in users:
            settings, created = EmailNotificationSettings.objects.get_or_create(user=user)
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ 通知設定作成完了: {user.nickname} ({user.email})'
                    )
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'既に設定済み: {user.nickname} ({user.email})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n完了！ 新規作成: {created_count}件、既存: {existing_count}件'
            )
        )
