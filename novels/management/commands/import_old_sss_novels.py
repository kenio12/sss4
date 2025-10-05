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
    help = '旧短編小説会のデータを取り込む'

    def handle(self, *args, **kwargs):
        try:
            # 環境変数からデータベース接続情報を取得して接続
            database_url = os.getenv('DATABASE_URL', 'デフォルトの開発環境用のデータベースURL')
            connection = psycopg2.connect(database_url)
            cursor = connection.cursor()

            cursor.execute("""
                SELECT title, sakushamei, honbun, toukouhiduke, genre
                FROM novels
                WHERE flag = TRUE
                AND genre NOT IN ('挨拶', 'イベント企画', 'イベント開催');
            """)

            User = get_user_model()
            novels_to_create = []

            for row in cursor.fetchall():
                title, sakushamei, honbun, toukouhiduke, genre = row
                
                # ニックネームが「超短編小説会公式」の場合はスキップ
                if sakushamei == "超短編小説会公式":
                    continue

                # 日付の処理
                tokyo_tz = pytz.timezone('Asia/Tokyo')
                if toukouhiduke.tzinfo is None:
                    toukouhiduke = tokyo_tz.localize(toukouhiduke)
                else:
                    toukouhiduke = toukouhiduke.astimezone(tokyo_tz)

                nickname = f"旧：{sakushamei}"
        
                sakushamei_hash = hashlib.md5(sakushamei.encode()).hexdigest()[:8]
                email = f"user_{sakushamei_hash}@example.com"
        
                author_user, _ = User.objects.get_or_create(
                    username=f"user_{sakushamei_hash}",
                    defaults={'email': email, 'nickname': nickname, 'user_type': User.OLD_SSS_WRITER}
                )

                # 「同タイトル」ジャンルの場合、is_same_title_gameをTrueに設定
                is_same_title_game = genre == '同タイトル'

                novel = Novel(
                    title=title,
                    author=author_user,
                    content=honbun,
                    published_date=toukouhiduke,
                    status='published',
                    genre=genre,
                    word_count=len(honbun),
                    is_same_title_game=is_same_title_game
                )
                novels_to_create.append(novel)

            # bulk_createの呼び出し、バッチサイズを指定
            Novel.objects.bulk_create(novels_to_create, batch_size=100)

            cursor.close()
            connection.close()

            self.stdout.write(self.style.SUCCESS('データの取り込みが完了しました。'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
        finally:
            cursor.close()
            connection.close()