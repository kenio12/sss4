"""
現在の問題点：
1. タスクの戻り値が常に1になってしまう問題が未解決
2. デバッグログは出力されるが、実行状況の確認が必要
3. 本番環境（Heroku）でのログ確認が必要

注意：上記の問題により、必要な場合は手動で実行する必要があります。
"""

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from novels.models import Novel
from game_maturi.models import MaturiGame

@shared_task
def publish_scheduled_novels():
    now = timezone.now()
    published_count = 0

    try:
        # トランザクション内で処理（重複実行防止）
        with transaction.atomic():
            scheduled_novels = Novel.objects.filter(
                status='scheduled',
                scheduled_at__lte=now
            ).select_for_update(of=('self',))

            for novel in scheduled_novels:
                novel.status = 'published'
                novel.published_date = now
                novel.save()
                published_count += 1

        return f"{published_count}件の小説を公開しました"
    except Exception as e:
        print(f"[Error] Publishing task failed: {str(e)}")
        raise

@shared_task
def reveal_maturi_authors():
    now = timezone.now()
    print(f"[Debug] Task started at: {now}")  # デバッグログ追加
    revealed_count = 0

    try:
        # トランザクション内で処理（重複実行防止）
        with transaction.atomic():
            finished_games = MaturiGame.objects.filter(
                prediction_end_date__lt=now.date(),
                is_author_revealed=False
            ).select_for_update(of=('self',))

            print(f"[Debug] Found {finished_games.count()} games to process")  # デバッグログ追加

            for game in finished_games:
                print(f"[Debug] Processing game: {game.id}")  # デバッグログ追加
                if not game.is_prediction_period_finished():
                    print(f"[Debug] Game {game.id} prediction period not finished")  # デバッグログ追加
                    continue

                # 小説の作者を元に戻す
                for novel in game.maturi_novels.all():
                    print(f"[Debug] Restoring author for novel: {novel.id}")  # デバッグログ追加
                    if novel.original_author:
                        novel.author = novel.original_author
                        novel.save()

                # コメントの投稿者を元に戻す
                for comment in game.comments.all():
                    print(f"[Debug] Restoring commenter for comment: {comment.id}")  # デバッグログ追加
                    if comment.original_commenter:
                        comment.author = comment.original_commenter
                        comment.save()

                game.is_author_revealed = True
                game.save()
                revealed_count += 1
                print(f"[Debug] Game {game.id} processed successfully")  # デバッグログ追加

        return f"{revealed_count}件の祭りの作者を公開しました"
    except Exception as e:
        print(f"[Error] Author reveal task failed: {str(e)}")
        raise