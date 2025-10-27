"""
謝罪メール送信コマンド

間違った同タイトル決定通知を受け取った11人に謝罪メールを送信します。

使い方:
    python manage.py send_apology_email
"""

import logging
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '謝罪メール送信（間違った同タイトル決定通知を受け取った11人へ）'

    # 間違ったメールを受け取った11人のメールアドレス
    RECIPIENT_EMAILS = [
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
        self.stdout.write(self.style.SUCCESS('📧 謝罪メール送信開始'))
        self.stdout.write(f'送信対象: {len(self.RECIPIENT_EMAILS)}人')
        self.stdout.write(f'開始時刻: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('=' * 80)

        sent_count = 0
        failed_count = 0

        # メール送信接続を再利用（効率化）
        connection = get_connection()
        connection.open()

        try:
            for email in self.RECIPIENT_EMAILS:
                try:
                    subject = '【超短編小説会】誤送信のお詫び'

                    message = f"""
平素より超短編小説会をご利用いただき、誠にありがとうございます。

本日2025年10月27日、
「【超短編小説会】2025年10月の同タイトル一番槍が決定！」
という誤ったメールを送信いたしました。

メールに記載されていた、テキサス万歳さんが書かれた小説「カセットテープ」は、同タイトルイベントの小説ではありませんでした。
完全な誤送信でございます。

誠に申し訳ございませんでした。

既に修正を完了しておりますので、明日以降、同様のミスは発生いたしません。

---
超短編小説会
管理人 けにを
開発担当 そに〜（Claude Sonnet 4.5）
{settings.BASE_URL}
                    """.strip()

                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                        connection=connection
                    )

                    sent_count += 1
                    masked_email = email[:3] + '***'
                    self.stdout.write(f'✅ [{sent_count}/{len(self.RECIPIENT_EMAILS)}] {masked_email} 送信成功')
                    logger.info(f'謝罪メール送信成功: {masked_email}')

                except Exception as e:
                    failed_count += 1
                    masked_email = email[:3] + '***'
                    error_str = str(e)
                    self.stdout.write(
                        self.style.ERROR(f'❌ [{failed_count}] {masked_email} 送信失敗: {error_str}')
                    )
                    logger.error(f'謝罪メール送信失敗: {masked_email} - {error_str}', exc_info=True)

        finally:
            connection.close()

        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS(f'📧 謝罪メール送信完了'))
        self.stdout.write(f'成功: {sent_count}件 / 失敗: {failed_count}件')
        self.stdout.write(f'終了時刻: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('=' * 80)

        logger.info(f'謝罪メール送信完了: 成功{sent_count}件, 失敗{failed_count}件')
