from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from game_same_title.models import PendingNotification
from game_same_title.notifications import send_same_title_proposal_notification
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '予約されたタイトル提案通知を12時（正午）に一斉送信する'

    def handle(self, *args, **options):
        # トランザクション内で処理（複数プロセス同時実行を防止）
        with transaction.atomic():
            # 未送信の「提案」通知のみ取得（ロック付き）
            pending_notifications = PendingNotification.objects.filter(
                is_sent=False,
                notification_type='提案'
            ).select_related('proposal', 'proposal__proposer').select_for_update(of=('self',))

            total_count = pending_notifications.count()
            self.stdout.write(f'未送信タイトル提案通知: {total_count}件')

            sent_count = 0
            error_count = 0

            for notification in pending_notifications:
                try:
                    # タイトル提案通知
                    send_same_title_proposal_notification(notification.proposal)
                    self.stdout.write(f'✅ タイトル提案通知送信: {notification.proposal.title} (提案者: {notification.proposal.proposer.username})')

                    # 送信完了マーク
                    notification.is_sent = True
                    notification.sent_at = timezone.now()
                    notification.save()
                    sent_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(f'タイトル提案通知送信エラー: {notification.id} - {str(e)}')
                    self.stdout.write(self.style.ERROR(f'❌ エラー: {notification.proposal.title} - {str(e)}'))

            self.stdout.write(self.style.SUCCESS(f'📧 タイトル提案通知送信完了: {sent_count}件成功、{error_count}件エラー'))
