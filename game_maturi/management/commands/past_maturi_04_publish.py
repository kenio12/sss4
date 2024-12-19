from django.core.management.base import BaseCommand
from game_maturi.models import MaturiGame, GamePrediction
from django.utils import timezone
import random

class Command(BaseCommand):
    help = '過去の祭りの小説を公開し、予想データを作成する'

    def handle(self, *args, **options):
        try:
            # 過去の祭りを取得
            past_maturi = MaturiGame.objects.filter(
                title__contains=str(timezone.now().year - 1)
            ).first()

            if not past_maturi:
                self.stdout.write(self.style.ERROR('過去の祭りが見つかれへんで'))
                return

            # 過去の日付を計算
            past_publish_time = timezone.now() - timezone.timedelta(days=389)

            # 予想データを作成
            self.stdout.write("予想データを作成します...")
            prediction_count = 0
            
            # 各予想者に対して
            for predictor in past_maturi.entrants.all():
                # 全ての小説に対して予想を作成（自分の小説も含む）
                for novel in past_maturi.maturi_novels.all():
                    # 自分の小説なら必ず正解
                    if predictor == novel.original_author:
                        predicted_author = novel.original_author
                    else:
                        # 他の小説は20-80%の確率で正解
                        if random.random() < 0.5:
                            predicted_author = novel.original_author
                        else:
                            possible_authors = list(past_maturi.entrants.exclude(
                                id=predictor.id
                            ))
                            predicted_author = random.choice(possible_authors)
                    
                    GamePrediction.objects.create(
                        maturi_game=past_maturi,
                        novel=novel,
                        predictor=predictor,
                        predicted_author=predicted_author,
                        created_at=past_publish_time
                    )
                    prediction_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'過去の祭りの処理が完了したで！ {prediction_count}件の予想を作成したで！'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
            raise
