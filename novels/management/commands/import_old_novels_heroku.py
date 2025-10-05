from django.core.management.base import BaseCommand
from novels.models import Novel
from django.contrib.auth import get_user_model
from django.db import transaction
import psycopg2
import os
from django.utils import timezone
import pytz
from datetime import datetime
import hashlib

class Command(BaseCommand):
    help = 'Heroku用：旧DBから小説データをインポートする'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        try:
            database_url = os.getenv('OLD_DATABASE_URL')
            if not database_url:
                self.stdout.write(self.style.ERROR('OLD_DATABASE_URLが設定されていません'))
                return

            with psycopg2.connect(database_url) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT title, sakushamei, honbun, toukouhiduke, genre, atogaki
                        FROM novels
                        WHERE flag = TRUE
                        AND genre NOT IN ('挨拶', 'イベント企画', 'イベント開催')
                    """)
                    
                    try:
                        with transaction.atomic():
                            while True:
                                rows = cursor.fetchmany(size=1000)  # Heroku用にバッチサイズを調整
                                if not rows:
                                    break

                                for row in rows:
                                    title, sakushamei, honbun, toukouhiduke, genre, atogaki = row

                                    # 日付の処理
                                    tokyo_tz = pytz.timezone('Asia/Tokyo')
                                    if toukouhiduke.tzinfo is None:
                                        toukouhiduke = tokyo_tz.localize(toukouhiduke)
                                    else:
                                        toukouhiduke = toukouhiduke.astimezone(tokyo_tz)

                                    # ユーザー作成
                                    sakushamei_hash = hashlib.md5(sakushamei.encode()).hexdigest()[:8]
                                    author_user, created = User.objects.get_or_create(
                                        username=f"user_{sakushamei_hash}",
                                        defaults={
                                            'email': f"user_{sakushamei_hash}@example.com",
                                            'nickname': f"旧：{sakushamei}",
                                            'user_type': User.OLD_SSS_WRITER
                                        }
                                    )

                                    # 小説の保存
                                    try:
                                        novel = Novel.objects.create(
                                            title=title,
                                            author=author_user,
                                            content=honbun,
                                            published_date=toukouhiduke,
                                            status='published',
                                            genre=genre,
                                            word_count=len(honbun),
                                            is_same_title_game=(genre == '同タイトル'),
                                            afterword=atogaki or ''
                                        )
                                        self.stdout.write(self.style.SUCCESS(f'小説を保存しました: {title}'))
                                    except Exception as e:
                                        self.stdout.write(self.style.ERROR(f'小説の保存に失敗: {title} - {str(e)}'))
                                        continue

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'データの取得中にエラーが発生しました: {str(e)}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'データベースへの接続中にエラーが発生しました: {str(e)}'))