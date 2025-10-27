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
超短編小説会をご利用いただき、ありがとうございます。

本日2025年10月27日、わしが
「【超短編小説会】2025年10月の同タイトル一番槍が決定！」
という間違ったメールを送信してしまいました。

このメールは皆さんとは全く関係ありません。
完全にわしのミスで送られた無意味なメールです。

これは10月中旬に既に決定・通知済みの古い話を、
わしが間違って再送信してしまったものです。
皆さんが一番槍を獲得したわけでも、何かする必要があるわけでもありません。
無視していただいて結構です。

なぜこんなことになったかというと：
10月中旬に一部の方へメール送信が失敗したので、
10月21日に1回だけ再送信する処理をわしが作成しました。
ところが、わしの設定ミスで、その処理が毎日実行される設定になっていました。
そのため、本日も誤って10月の古い内容のメールを送信してしまいました。

わしが間違ったメールを送ってしまいました。
大変申し訳ございませんでした。

すでに修正を完了しましたので、明日からは同じミスは起こりません。
今後はこのようなことがないよう、わしが十分に確認してから実行します。

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
