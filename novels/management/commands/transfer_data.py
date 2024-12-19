import os
import psycopg2
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import pytz
from datetime import datetime
import hashlib
from django.contrib.auth import get_user_model
from novels.models import Novel

class Command(BaseCommand):
    help = 'データを shumi から sss4 に転送する'

    def handle(self, *args, **kwargs):
        shumi_database_url = os.getenv('SHUMI_DATABASE_URL')
        sss4_database_url = os.getenv('SSS4_DATABASE_URL')

        # shumi のデータベースからデータを読み取る
        with psycopg2.connect(shumi_database_url) as shumi_conn:
            with shumi_conn.cursor() as shumi_cursor:
                shumi_cursor.execute("""
                    SELECT title, sakushamei, honbun, toukouhiduke, genre
                    FROM novels
                    WHERE flag = TRUE
                    AND genre NOT IN ('挨拶', 'イベント企画', 'イベント開催');
                """)
                data_to_transfer = shumi_cursor.fetchall()

        # sss4 のデータベースにデータを保存する
        with psycopg2.connect(sss4_database_url) as sss4_conn:
            with sss4_conn.cursor() as sss4_cursor:
                with transaction.atomic():
                    for row in data_to_transfer:
                        title, sakushamei, honbun, toukouhiduke, genre = row
                        tokyo_tz = pytz.timezone('Asia/Tokyo')
                        if toukouhiduke.tzinfo is None:
                            toukouhiduke = tokyo_tz.localize(toukouhiduke)
                        else:
                            toukouhiduke = toukouhiduke.astimezone(tokyo_tz)

                        sakushamei_hash = hashlib.md5(sakushamei.encode()).hexdigest()[:8]
                        User = get_user_model()
                        # ユーザーの取得または作成
                        author_user, created = User.objects.get_or_create(
                            username=f"user_{sakushamei_hash}",
                            defaults={
                                'email': f"user_{sakushamei_hash}@example.com",
                                'nickname': f"旧：{sakushamei}"
                            }
                        )
                        # デバッグ情報の出力
                        self.stdout.write(f"User {author_user.username} created: {created}")
                        self.stdout.write(f"Current user_type before update: {author_user.user_type}")

                        # user_type の更新
                        if created or author_user.user_type != User.OLD_SSS_WRITER:
                            author_user.user_type = User.OLD_SSS_WRITER
                            author_user.save()
                            self.stdout.write(f"Updated user_type to OLD_SSS_WRITER for {author_user.username}")

                        self.stdout.write(f"Current user_type after update: {author_user.user_type}")

                        novel = Novel(
                            title=title,
                            content=honbun,
                            author=author_user,
                            published_date=toukouhiduke,
                            status='published',
                            genre=genre,
                            word_count=len(honbun),
                            is_same_title_game=(genre == '同タイトル')
                        )
                        novel.save()
                        self.stdout.write(self.style.SUCCESS(f'Novel "{title}" saved successfully.'))