"""
AccessLogを簡単に確認するための管理コマンド

使い方:
  python manage.py show_access_logs --hours 24
  python manage.py show_access_logs --path /game_same_title/post_or_edit/
  python manage.py show_access_logs --user kenio
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from game_same_title.models import AccessLog


class Command(BaseCommand):
    help = 'AccessLogを確認する'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='過去何時間のログを表示するか（デフォルト: 24時間）'
        )
        parser.add_argument(
            '--path',
            type=str,
            default=None,
            help='特定のパスのみフィルタ（例: /game_same_title/post_or_edit/）'
        )
        parser.add_argument(
            '--user',
            type=str,
            default=None,
            help='特定のユーザーのみフィルタ（username）'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        path_filter = options['path']
        user_filter = options['user']

        # 時間範囲でフィルタ
        now = timezone.now()
        time_threshold = now - timedelta(hours=hours)
        logs = AccessLog.objects.filter(
            accessed_at__gte=time_threshold
        ).select_related('user').order_by('-accessed_at')

        # パスでフィルタ
        if path_filter:
            logs = logs.filter(path__startswith=path_filter)

        # ユーザーでフィルタ
        if user_filter:
            logs = logs.filter(user__username=user_filter)

        # 結果表示
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(f"📊 過去{hours}時間のアクセスログ: {logs.count()}件")
        self.stdout.write(f"{'='*70}\n")

        if logs.count() == 0:
            self.stdout.write(self.style.WARNING("⚠️ アクセスログが見つかりませんでした"))
            return

        for log in logs:
            # ユーザー情報取得
            if log.user:
                nickname = getattr(log.user.profile, 'nickname', log.user.username) if hasattr(log.user, 'profile') else log.user.username
                user_info = f"{nickname} ({log.user.username})"
            else:
                user_info = "匿名ユーザー"

            # 日時（日本時間）
            jst_time = timezone.localtime(log.accessed_at)

            self.stdout.write(self.style.SUCCESS(f"🕒 {jst_time.strftime('%Y-%m-%d %H:%M:%S')}"))
            self.stdout.write(f"   👤 ユーザー: {user_info}")
            self.stdout.write(f"   🌐 IP: {log.ip_address}")
            self.stdout.write(f"   📍 パス: {log.path}")
            self.stdout.write(f"   📝 メソッド: {log.method}")
            self.stdout.write("")

        self.stdout.write(f"{'='*70}")
        self.stdout.write(self.style.SUCCESS(f"✅ 合計 {logs.count()}件のアクセスログを表示しました"))
        self.stdout.write(f"{'='*70}\n")
