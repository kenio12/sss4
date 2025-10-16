"""
お詫び＋訂正メール送信コマンド
BASE_URL未設定で間違ったリンクを送信してしまったユーザーへの訂正メール
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'リンク不具合のお詫び＋訂正メール送信（作品ID:1936）'

    def handle(self, *args, **options):
        # same_title_decision通知を受け取った実ユーザー17人を取得
        users = User.objects.filter(
            notification_settings__same_title_decision=True,
            is_active=True,
            email_confirmed=True
        ).select_related('notification_settings')

        if not users.exists():
            self.stdout.write(self.style.WARNING('送信対象ユーザーなし'))
            return

        sent_count = 0
        connection = get_connection()
        connection.open()

        try:
            for user in users:
                try:
                    subject = '【お詫び】メール内リンクの不具合について'

                    message = f"""
{user.nickname} 様

超短編小説会です。

先ほどお送りした「一番槍決定」のメールにて、
作品へのリンクに不具合がございました。

正しいリンクはこちらです：
https://www.sss4.life/novels/1936/

ご迷惑をおかけして誠に申し訳ございません。

今後このようなことがないよう、
送信前の確認を徹底いたします。

超短編小説会
                    """.strip()

                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                        connection=connection,
                    )
                    sent_count += 1
                    masked_email = user.email[:3] + '***'
                    logger.info(f'お詫びメール送信成功: {masked_email}')
                    self.stdout.write(self.style.SUCCESS(f'送信成功: {masked_email}'))

                except Exception as e:
                    masked_email = user.email[:3] + '***'
                    logger.error(f'お詫びメール送信失敗: {masked_email} - {str(e)}')
                    self.stdout.write(self.style.ERROR(f'送信失敗: {masked_email} - {str(e)}'))
                    continue

            self.stdout.write(self.style.SUCCESS(f'お詫びメール送信完了: {sent_count}件'))
            logger.info(f'お詫びメール送信完了: {sent_count}件')

        finally:
            connection.close()
