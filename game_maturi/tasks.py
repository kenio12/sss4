from celery import shared_task
from django.utils import timezone
from novels.models import Novel
from game_maturi.models import MaturiGame

@shared_task
def publish_scheduled_novels():
    now = timezone.now()
    published_count = 0
    
    try:
        scheduled_novels = Novel.objects.filter(
            status='scheduled',
            scheduled_at__lte=now
        )
        
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
    revealed_count = 0
    
    try:
        finished_games = MaturiGame.objects.filter(
            prediction_end_date__lt=now.date(),
            is_author_revealed=False
        )
        
        for game in finished_games:
            if not game.is_prediction_period_finished():
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
            
            game.is_author_revealed = True
            game.save()
            revealed_count += 1
        
        return f"{revealed_count}件の祭りの作者を公開しました"
    except Exception as e:
        print(f"[Error] Author reveal task failed: {str(e)}")
        raise