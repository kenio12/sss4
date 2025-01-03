from celery import shared_task
from django.utils import timezone
from novels.models import Novel
from game_maturi.models import MaturiGame

@shared_task
def publish_scheduled_novels():
    # タイムゾーン情報を含むデバッグ出力を追加
    now = timezone.now()
    print(f"[Debug] Current time: {now}")
    print(f"[Debug] Current timezone: {timezone.get_current_timezone()}")
    
    # カウンターを try 文の外で初期化
    published_count = 0
    revealed_count = 0
    
    try:
        # 予約公開の小説を探す前にクエリの内容を確認
        all_scheduled = Novel.objects.filter(status='scheduled')
        print(f"[Debug] All scheduled novels: {all_scheduled.count()}")
        for novel in all_scheduled:
            print(f"[Debug] Novel {novel.id}: scheduled_at={novel.scheduled_at}, status={novel.status}")

        # 実際のクエリ結果を確認
        scheduled_novels = Novel.objects.filter(
            status='scheduled',
            scheduled_at__lte=now
        )
        print(f"[Debug] Filtered scheduled novels: {scheduled_novels.count()}")
        for novel in scheduled_novels:
            print(f"[Debug] Will publish: {novel.id} (scheduled_at={novel.scheduled_at})")
        
        # 予約済み小説の詳細なデバッグ情報
        for novel in scheduled_novels:
            print(f"[Debug] Novel ID: {novel.id}")
            print(f"[Debug] Novel scheduled_at: {novel.scheduled_at}")
            print(f"[Debug] Novel scheduled_at timezone: {novel.scheduled_at.tzinfo}")
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