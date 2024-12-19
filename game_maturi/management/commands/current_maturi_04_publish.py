from django.core.management.base import BaseCommand
from game_maturi.models import MaturiGame, GamePrediction
from django.utils import timezone
import random

class Command(BaseCommand):
    help = '現在の祭りの予想データを作成する'

    def handle(self, *args, **options):
        try:
            # 現在の祭りを取得
            current_maturi = MaturiGame.find_current_game()
            if not current_maturi:
                self.stdout.write(self.style.ERROR('現在の祭りが見つかれへんで'))
                return

            # 予想データを作成
            self.stdout.write("予想データを作成します...")
            prediction_count = 0
            
            # 各予想者に対して
            for predictor in current_maturi.entrants.all():
                # 全ての小説に対して予想を作成
                for novel in current_maturi.maturi_novels.all():
                    # 自分の小説なら必ず正解
                    if predictor == novel.original_author:
                        predicted_author = novel.original_author
                    else:
                        # 他の小説は20-80%の確率で正解
                        if random.random() < 0.5:
                            predicted_author = novel.original_author
                        else:
                            possible_authors = list(current_maturi.entrants.exclude(
                                id=predictor.id
                            ))
                            predicted_author = random.choice(possible_authors)
                    
                    # 予想を作成（5分後の時間で）
                    GamePrediction.objects.create(
                        maturi_game=current_maturi,
                        novel=novel,
                        predictor=predictor,
                        predicted_author=predicted_author,
                        created_at=timezone.now() + timezone.timedelta(minutes=5)
                    )
                    prediction_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'現在の祭りの予想データを作成したで！ {prediction_count}件の予想を作成したで！'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
            raise