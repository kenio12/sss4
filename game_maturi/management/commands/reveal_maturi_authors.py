from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from game_maturi.models import MaturiGame
from novels.models import Novel, Comment

class Command(BaseCommand):
    help = '祭りゲームの作者とコメント投稿者を公開する'

    def handle(self, *args, **options):
        now = timezone.now().date()
        revealed_count = 0

        try:
            # トランザクション内で処理（重複実行防止）
            with transaction.atomic():
                # 予想期間が終了した祭りゲームを取得（is_author_revealed=False のみ）
                finished_games = MaturiGame.objects.filter(
                    prediction_end_date__lt=now,
                    is_author_revealed=False
                ).select_for_update(of=('self',))

                self.stdout.write(f'処理対象の祭りゲーム: {finished_games.count()}件')

                for game in finished_games:
                    # 予想期間が本当に終了してるか確認
                    if not game.is_prediction_period_finished():
                        self.stdout.write(
                            self.style.WARNING(f'祭りゲーム "{game.title}" の予想期間はまだ終了していません')
                        )
                        continue

                    # 小説の作者を元に戻す
                    novels = game.maturi_novels.all()
                    for novel in novels:
                        if novel.original_author:
                            novel.author = novel.original_author
                            novel.save()
                            self.stdout.write(f'  - 小説 "{novel.title}" の作者を公開')

                    # コメントの投稿者を元に戻す
                    comments = Comment.objects.filter(maturi_game=game)
                    for comment in comments:
                        if comment.original_commenter:
                            comment.author = comment.original_commenter
                            comment.save()

                    # 🔥 重要：is_author_revealed フラグを True にする
                    game.is_author_revealed = True
                    game.save()
                    revealed_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(f'✅ 祭りゲーム "{game.title}" の作者とコメント投稿者を公開しました')
                    )

            if revealed_count == 0:
                self.stdout.write(
                    self.style.WARNING('公開する祭りゲームはありませんでした')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'合計 {revealed_count}件の祭りゲームの作者を公開しました')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'エラーが発生しました: {str(e)}')
            )
            raise