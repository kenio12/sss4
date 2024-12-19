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
    help = 'ローカル環境用：旧DBから小説データをインポートする'

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
                        SELECT n.title, u.nickname, n.content, n.published_date, n.genre, n.afterword
                        FROM novels_novel n
                        JOIN accounts_user u ON u.id = n.author_id
                        WHERE n.genre NOT IN ('挨拶', 'イベント企画', 'イベント開催')
                    """)
                    
                    with transaction.atomic():
                        while True:
                            rows = cursor.fetchmany(size=1000)
                            if not rows:
                                break

                            for row in rows:
                                title, nickname, content, published_date, genre, afterword = row

                                # ユーザー作成
                                author_hash = hashlib.md5(str(nickname).encode()).hexdigest()[:8]
                                author_user, created = User.objects.get_or_create(
                                    username=f"user_{author_hash}",
                                    defaults={
                                        'email': f"user_{author_hash}@example.com",
                                        'nickname': nickname,
                                        'user_type': User.OLD_SSS_WRITER
                                    }
                                )

                                # 小説の保存
                                try:
                                    novel = Novel.objects.create(
                                        title=title,
                                        author=author_user,
                                        content=content,
                                        published_date=published_date,
                                        status='published',
                                        genre=genre,
                                        word_count=len(content),
                                        is_same_title_game=(genre == '同タイトル'),
                                        afterword=afterword or ''
                                    )
                                    self.stdout.write(self.style.SUCCESS(f'小説を保存しました: {title}'))
                                except Exception as e:
                                    self.stdout.write(self.style.ERROR(f'小説の保存に失敗: {title} - {str(e)}'))
                                    continue

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'データベースへの接続中にエラーが発生しました: {str(e)}')) 