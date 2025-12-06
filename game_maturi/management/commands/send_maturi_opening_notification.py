"""
祭り開幕通知コマンド

祭り作成後の次の17時に全ユーザーへ開幕通知を送信する
Heroku Schedulerで毎日17時（JST = UTC 08:00）に実行
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core import signing
from django.db import transaction
from game_maturi.models import MaturiGame
import logging
import time

User = get_user_model()
logger = logging.getLogger(__name__)


def get_unsubscribe_url(user):
    """配信停止URL生成"""
    token = signing.dumps(user.id, salt='email_unsubscribe')
    return f"{settings.BASE_URL}/accounts/unsubscribe/{token}/"


class Command(BaseCommand):
    help = '祭り開幕通知を全ユーザーに送信する（毎日17時JST実行）'

    def handle(self, *args, **options):
        with transaction.atomic():
            # 未送信の祭りを取得（ロック付き）
            unsent_games = MaturiGame.objects.filter(
                opening_notification_sent=False
            ).select_for_update(of=('self',))

            if not unsent_games.exists():
                self.stdout.write(self.style.WARNING('送信対象の祭りはありません'))
                return

            # 全ユーザーを取得（メール確認済み・アクティブのみ）
            users = User.objects.filter(
                is_active=True,
                email_confirmed=True
            )

            if not users.exists():
                self.stdout.write(self.style.WARNING('送信対象のユーザーがいません'))
                return

            # メール送信接続を再利用（効率化）
            connection = get_connection()
            connection.open()

            try:
                for game in unsent_games:
                    self.stdout.write(f'🎉 祭り開幕通知送信開始: {game.title}')
                    sent_count = 0
                    error_count = 0

                    # 語句一覧を取得
                    phrases = list(game.phrases.values_list('text', flat=True))
                    phrases_text = '、'.join(phrases) if phrases else '（語句未設定）'

                    for user in users:
                        try:
                            subject = f'【超短編小説会】🎉 {game.title} 開幕！'
                            unsubscribe_url = get_unsubscribe_url(user)

                            message = f"""
{user.nickname} 様

🎉 祭りが開幕しました！

━━━━━━━━━━━━━━━━━━━━
■ {game.title}
━━━━━━━━━━━━━━━━━━━━

📝 今回のお題語句：
{phrases_text}

📅 スケジュール：
・小説投稿期間：{game.maturi_start_date.strftime('%m月%d日')} 〜 {game.prediction_start_date.strftime('%m月%d日')}
・作者予想期間：{game.prediction_start_date.strftime('%m月%d日')} 〜 {game.prediction_end_date.strftime('%m月%d日')}

▼ 参加方法
1. 超短編小説会トップページ（{settings.BASE_URL}）にアクセス
2. 画面上部の「🏮祭」マークをクリック
3. 「エントリー」ボタンを押して参加登録！

エントリーのうえ、こぞってご参加ください！
楽しいで🎵

---
このメールの配信を停止する場合は、以下のリンクをクリックしてください。
{unsubscribe_url}

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
                            logger.debug(f'祭り開幕通知送信成功: {masked_email}')

                            # 🔥🔥🔥 レート制限対策：5秒待機 🔥🔥🔥
                            time.sleep(5)

                        except Exception as e:
                            error_count += 1
                            masked_email = user.email[:3] + '***'
                            logger.error(f'祭り開幕通知送信失敗: {masked_email} - {str(e)}', exc_info=True)
                            continue

                    # 送信済みフラグを立てる
                    game.opening_notification_sent = True
                    game.save()

                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {game.title}: {sent_count}件送信成功、{error_count}件エラー')
                    )

            finally:
                connection.close()

        self.stdout.write(self.style.SUCCESS('📧 祭り開幕通知送信完了'))
