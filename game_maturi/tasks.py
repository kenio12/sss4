from celery import shared_task
from django.utils import timezone
from novels.models import Novel
from game_maturi.models import MaturiGame

@shared_task
def publish_scheduled_novels():
    # 実際のシステム時間を使用
    now = timezone.now()
    print(f"[Debug] Current time: {now}")
    print(f"[Debug] Current time type: {type(now)}")
    
    # カウンターを try 文の外で初期化
    published_count = 0
    revealed_count = 0
    
    try:
        scheduled_novels = Novel.objects.filter(
            status='scheduled',
            scheduled_at__lte=now
        )
        print(f"[Debug] Found {scheduled_novels.count()} scheduled novels")
        
        # 予約公開の処理
        for novel in scheduled_novels:
            print(f"[Debug] Novel: {novel.title}")
            print(f"[Debug] Scheduled at: {novel.scheduled_at}")
            print(f"[Debug] Publishing novel: {novel.title}")
            novel.status = 'published'
            novel.published_date = now
            novel.save()
            published_count += 1
        
        # 作者公開の処理
        finished_games = MaturiGame.objects.filter(
            prediction_end_date__lt=now.date(),
            is_author_revealed=False
        )
        print(f"[Debug] Found {finished_games.count()} finished games")
        
        for game in finished_games:
            print(f"[Debug] Processing game {game.id} for author reveal")
            
            if not game.is_prediction_period_finished():
                print(f"[Debug] Game {game.id} prediction period not finished yet")
                continue

            # 小説の作者を元に戻す
            for novel in game.maturi_novels.all():
                if novel.original_author:
                    novel.author = novel.original_author
                    novel.save()
            
            # コメントの投稿者を元に戻す
            for comment in game.comments.all():
                if comment.original_commenter:
                    comment.author = comment.original_commenter
                    comment.save()
            
            # 作者公開済みフラグを設定
            game.is_author_revealed = True
            game.save()
            
            revealed_count += 1
            print(f"[Debug] Successfully revealed game {game.id}")
        
        return f"{published_count}件の小説を公開し、{revealed_count}件の祭りの作者を公開しました"
    except Exception as e:
        print(f"[Error] Task failed: {str(e)}")
        raise