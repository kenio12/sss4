"""
祭り作者予想期間開始通知コマンド

予想期間開始日の10時に全ユーザーへ予想開始通知を送信する
Heroku Schedulerで毎日10時（JST = UTC 01:00）に実行

タイムライン:
- prediction_start_date = 予想期間開始日（例: 12月4日）
- 10:00 JST（= 01:00 UTC）に通知送信
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
    help = '祭り作者予想期間開始通知を全ユーザーに送信する（毎日10時JST実行）'

    def handle(self, *args, **options):
        # 🔥 JST時間取得
        now = timezone.localtime(timezone.now()).date()

        with transaction.atomic():
            # 未送信の祭りを取得（ロック付き）
            unsent_games = MaturiGame.objects.filter(
                prediction_notification_sent=False
            ).select_for_update(of=('self',))

            # 予想期間開始日が今日のゲームをフィルタ
            target_games = []
            for game in unsent_games:
                if game.prediction_start_date == now:
                    target_games.append(game)

            if not target_games:
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
                for game in target_games:
                    self.stdout.write(f'🔮 祭り予想期間開始通知送信開始: {game.title}')
                    sent_count = 0
                    error_count = 0

                    # 予想期間終了日をフォーマット
                    end_date = game.prediction_end_date
                    end_date_str = f'{end_date.month}月{end_date.day}日'

                    for user in users:
                        try:
                            subject = f'【超短編小説会】🔮 {game.title} 作者予想期間スタート！'
                            unsubscribe_url = get_unsubscribe_url(user)

                            # 祭りページのURL
                            game_url = f"{settings.BASE_URL}/game_maturi/game_top/{game.id}/"

                            message = f"""
{user.nickname} 様

さて、予想期間が開始しました。
今より小説の作家予想ができるので、下記リンクから祭り作品の真の作者を予想しましょう！

👉 {game_url}

なお予想期間は{end_date_str}までです。
追加で作品が投稿されるかもしれませんので、最終日である{end_date_str}に再度予想漏れがないか確認しましょう！

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
                            logger.debug(f'祭り予想開始通知送信成功: {masked_email}')

                            # 🔥🔥🔥 レート制限対策：5秒待機 🔥🔥🔥
                            time.sleep(5)

                        except Exception as e:
                            error_count += 1
                            masked_email = user.email[:3] + '***'
                            logger.error(f'祭り予想開始通知送信失敗: {masked_email} - {str(e)}', exc_info=True)
                            continue

                    # 送信済みフラグを立てる
                    game.prediction_notification_sent = True
                    game.save()

                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {game.title}: {sent_count}件送信成功、{error_count}件エラー')
                    )

            finally:
                connection.close()

        self.stdout.write(self.style.SUCCESS('📧 祭り予想期間開始通知送信完了'))
