"""
同タイトル決定通知の再送信コマンド

失敗した11人のユーザーに1分間隔で通知メールを再送信します。

使い方:
    python manage.py resend_failed_notifications

スケジュール実行（2025-10-21 12:00 JST）:
    echo "0 12 21 10 * cd /app && python manage.py resend_failed_notifications" | crontab -
"""

import time
import logging
from urllib.parse import quote
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.utils import timezone
from accounts.models import User
from novels.models import Novel
from game_same_title.notifications import get_unsubscribe_url

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '同タイトル決定通知の再送信（失敗した11人に1分間隔で送信）'

    # 🔥🔥🔥 失敗した11人のメールアドレス（Sentryエラーから特定）
    FAILED_EMAILS = [
        'floreat100000@gmail.com',
        'howamefoever@msn.com',
        'keikeikun24@yahoo.co.jp',
        'keikeikun3@gmail.com',
        'keikeikun@icloud.com',
        'kokuentotukyu@infoseek.jp',
        'sonychan@example.com',
        'tosiniyama@gmail.com',
        'tumayouji0103@gmail.com',
        'yu10.riverside@gmail.com',
        'yukikazeyuudati360621@gmail.com',
    ]

    def handle(self, *args, **options):
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('🔥 同タイトル決定通知再送信開始'))
        self.stdout.write(f'開始時刻: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('=' * 80)

        # 今月の一番槍を取得
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        try:
            novel = Novel.objects.filter(
                created_at__gte=current_month_start,
                status='published'
            ).select_related('author').order_by('created_at').first()

            if not novel:
                raise Novel.DoesNotExist()
        except Novel.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ 今月の一番槍が見つかりません'))
            return

        self.stdout.write(f'📚 今月のタイトル: {novel.title}')
        self.stdout.write(f'👤 一番槍: {novel.author.nickname}')
        self.stdout.write('')

        # 失敗したユーザーを取得
        failed_users = User.objects.filter(
            email__in=self.FAILED_EMAILS,
            is_active=True,
            email_confirmed=True
        ).select_related('notification_settings')

        total_users = failed_users.count()
        self.stdout.write(f'📧 送信対象: {total_users}人')
        self.stdout.write('')

        if total_users == 0:
            self.stdout.write(self.style.WARNING('⚠️ 送信対象ユーザーが見つかりません'))
            return

        # メール送信
        sent_count = 0
        failed_count = 0
        current_month = timezone.now().strftime('%Y年%m月')

        # メール送信接続を再利用
        connection = get_connection()
        connection.open()

        try:
            for i, user in enumerate(failed_users, 1):
                try:
                    subject = f'【超短編小説会】{current_month}の同タイトル一番槍が決定！'
                    unsubscribe_url = get_unsubscribe_url(user)
                    encoded_title = quote(novel.title, safe='')

                    message = f"""
{user.nickname} 様

こんにちは！超短編小説会です。

{current_month}の同タイトルイベント、一番槍が決定しました！

※一番槍とは、超短編小説会Ⅳの10月の同タイトルのイベントにおいて、今月最初にこのタイトルで投稿された作品のことです。

◆ 今月のタイトル
「{novel.title}」

一番槍: {novel.author.nickname}

◆ 作品を読む
{settings.BASE_URL}/novels/{novel.id}/

◆ 俺もこのタイトルで作る
{settings.BASE_URL}/novels/post/?title={encoded_title}

あなたも同じタイトルで創作に挑戦してみませんか？

---
今後、このようなメールの受信を拒否されたい方は、以下のリンクをクリックしてください。クリックすることで配信を止めます。
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
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ [{i}/{total_users}] {masked_email} 送信成功')
                    )
                    logger.info(f'同タイトル決定通知再送信成功: {masked_email}')

                    # 🔥🔥🔥 レート制限対策：60秒（1分）待機
                    if i < total_users:  # 最後のユーザーは待機不要
                        self.stdout.write(f'⏳ 次の送信まで60秒待機...')
                        time.sleep(60)

                except Exception as e:
                    failed_count += 1
                    masked_email = user.email[:3] + '***'
                    error_str = str(e)

                    # rate limit エラー（450）の場合はスキップ（待機なし）
                    if '450' in error_str and 'rate' in error_str.lower():
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ [{i}/{total_users}] {masked_email} rate limit エラー（スキップ）')
                        )
                        logger.warning(f'同タイトル決定通知再送信スキップ（rate limit）: {masked_email}')
                        # rate limit エラーは待機せずに次へ
                        continue

                    self.stdout.write(
                        self.style.ERROR(f'❌ [{i}/{total_users}] {masked_email} 送信失敗: {error_str}')
                    )
                    logger.error(f'同タイトル決定通知再送信失敗: {masked_email} - {error_str}', exc_info=True)

                    # その他のエラー時も1分待機（レート制限回避）
                    if i < total_users:
                        time.sleep(60)

        finally:
            connection.close()

        # 完了報告
        self.stdout.write('')
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('🎉 再送信完了'))
        self.stdout.write(f'送信成功: {sent_count}件')
        self.stdout.write(f'送信失敗: {failed_count}件')
        self.stdout.write(f'完了時刻: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('=' * 80)

        logger.info(f'同タイトル決定通知再送信完了: 成功{sent_count}件, 失敗{failed_count}件')
