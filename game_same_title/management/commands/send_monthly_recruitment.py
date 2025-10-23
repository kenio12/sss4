"""
同タイトル募集通知送信コマンド

毎日実行されるが、月初（1日）のみ全会員に同タイトルイベント募集通知を送信する

使い方:
    python manage.py send_monthly_recruitment

Heroku Schedulerでの設定例:
    python manage.py send_monthly_recruitment
    実行タイミング: Every day at 01:00 AM UTC（JST 10:00午前）
    実際の送信: 毎月1日のみ
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from game_same_title.notifications import send_same_title_recruitment_notification
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '同タイトル募集通知を全会員に送信（毎日実行・月初1日のみ送信）'

    def handle(self, *args, **options):
        # 今日の日付を取得（JST）
        now = timezone.localtime(timezone.now())
        today = now.day

        # 月初1日じゃなかったら何もせず終了
        if today != 1:
            self.stdout.write(f'今日は{today}日です。月初1日のみ送信するため、何もせず終了します。')
            logger.info(f'同タイトル募集通知: 今日は{today}日のため送信スキップ')
            return

        # 月初1日なので送信開始
        self.stdout.write('🎉 今日は月初1日です！同タイトル募集通知送信開始...')
        logger.info('同タイトル募集通知送信コマンド実行開始（月初1日）')

        try:
            sent_count = send_same_title_recruitment_notification()

            self.stdout.write(
                self.style.SUCCESS(
                    f'同タイトル募集通知送信完了: {sent_count}件送信しました'
                )
            )
            logger.info(f'同タイトル募集通知送信コマンド実行完了: {sent_count}件')

        except Exception as e:
            error_message = f'同タイトル募集通知送信エラー: {str(e)}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message, exc_info=True)
            raise
