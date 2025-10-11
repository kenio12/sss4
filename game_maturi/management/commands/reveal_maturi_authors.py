from django.core.management.base import BaseCommand
from django.utils import timezone
from game_maturi.models import MaturiGame
from novels.models import Novel, Comment

class Command(BaseCommand):
    help = '祭りゲームの作者とコメント投稿者を公開する'

    def handle(self, *args, **options):
        # 予想期間が終了した祭りゲームを取得
        finished_games = MaturiGame.objects.filter(
            prediction_end_date__lt=timezone.now().date()
        )

        for game in finished_games:
            # 小説の作者を元に戻す
            novels = game.maturi_novels.all()
            for novel in novels:
                if novel.original_author:
                    novel.author = novel.original_author
                    novel.save()

            # コメントの投稿者を元に戻す
            comments = Comment.objects.filter(maturi_game=game)
            for comment in comments:
                if comment.original_commenter:
                    comment.author = comment.original_commenter
                    comment.save()

            self.stdout.write(
                self.style.SUCCESS(f'祭りゲーム "{game.title}" の作者とコメント投稿者を公開しました')
            )