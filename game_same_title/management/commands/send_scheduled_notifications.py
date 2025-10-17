from django.core.management.base import BaseCommand
from django.utils import timezone
from game_same_title.models import PendingNotification
from game_same_title.notifications import send_same_title_decision_notification, send_same_title_follower_praise_notification
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '予約されたメール通知を18時に一斉送信する'

    def handle(self, *args, **options):
        # 未送信の通知を全て取得
        pending_notifications = PendingNotification.objects.filter(is_sent=False).select_related('novel', 'novel__author')

        total_count = pending_notifications.count()
        self.stdout.write(f'未送信通知: {total_count}件')

        sent_count = 0
        error_count = 0

        for notification in pending_notifications:
            try:
                if notification.notification_type == '決定':
                    # 一番槍通知
                    send_same_title_decision_notification(notification.novel)
                    self.stdout.write(f'✅ 一番槍通知送信: {notification.novel.title} (ユーザー: {notification.novel.author.username})')

                elif notification.notification_type == '追随':
                    # 追随通知
                    send_same_title_follower_praise_notification(notification.novel, notification.rank)
                    self.stdout.write(f'✅ 追随通知送信: {notification.novel.title} - {notification.rank}番目 (ユーザー: {notification.novel.author.username})')

                # 送信完了マーク
                notification.is_sent = True
                notification.sent_at = timezone.now()
                notification.save()
                sent_count += 1

            except Exception as e:
                error_count += 1
                logger.error(f'通知送信エラー: {notification.id} - {str(e)}')
                self.stdout.write(self.style.ERROR(f'❌ エラー: {notification.novel.title} - {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'📧 通知送信完了: {sent_count}件成功、{error_count}件エラー'))
