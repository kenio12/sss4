"""
同タイトル募集通知送信コマンド

月初（1日）に実行して、全会員に同タイトルイベント募集通知を送信する

使い方:
    python manage.py send_monthly_recruitment

Heroku Schedulerでの設定例:
    python manage.py send_monthly_recruitment
    実行タイミング: 毎月1日 10:00 (JST)
"""
from django.core.management.base import BaseCommand
from game_same_title.notifications import send_same_title_recruitment_notification
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '同タイトル募集通知を全会員に送信（月初1日実行用）'

    def handle(self, *args, **options):
        self.stdout.write('同タイトル募集通知送信開始...')
        logger.info('同タイトル募集通知送信コマンド実行開始')

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
