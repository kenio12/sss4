from django.core.management.base import BaseCommand
from game_maturi.models import MaturiGame, GamePrediction
from django.utils import timezone
import random
from django.db.models import Count
from django.utils.timezone import make_aware
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = '現在の祭りの予想を作成する'

    def handle(self, *args, **options):
        # 最新の祭りゲームを取得
        game = MaturiGame.objects.last()
        if not game:
            self.stdout.write(self.style.ERROR('祭りゲームが見つかれへんで'))
            return

        # 既存の予想を確認
        existing_predictions = GamePrediction.objects.filter(maturi_game=game)
        if existing_predictions.exists():
            self.stdout.write(self.style.WARNING(
                '既に予想が存在します。既存の予想は保持したまま、予想期間のみ設定します。'
            ))
        
        # 予想期間を設定（現在時刻から1分後）
        now = timezone.now()
        prediction_end = now + timezone.timedelta(minutes=1)
        
        # 祭りの日程を更新（時刻情報も含めて保存）
        game.prediction_start_datetime = now
        game.prediction_end_datetime = prediction_end
        game.save()

        self.stdout.write(f'予想期間を設定したで：{now} から {prediction_end} まで')
        
        created_count = 0
        for predictor in game.entrants.all():
            if predictor.nickname == '祭り作家':
                continue

            self.stdout.write(f'\n{predictor.nickname} の予想作成開始')
            
            # 正解率をランダムに設定（20%～80%）
            correct_rate = random.randint(20, 80) / 100
            self.stdout.write(f'ランダム正解率: {correct_rate*100:.1f}%')
            
            # 全ての小説に対して予想を作成
            for novel in game.maturi_novels.filter(status='published'):
                try:
                    # 自分の小説なら必ず正解
                    if predictor == novel.original_author:
                        predicted_author = novel.original_author
                    else:
                        # 正解を選ぶか、ランダムな作者を選ぶか
                        if random.random() < correct_rate:
                            predicted_author = novel.original_author
                        else:
                            # 正解の作者を除外してランダム選択
                            other_authors = [a for a in game.entrants.all() if a != novel.original_author and a.nickname != '祭り作家']
                            predicted_author = random.choice(other_authors)

                    # 予想を作成
                    prediction = GamePrediction.objects.create(
                        maturi_game=game,
                        novel=novel,
                        predictor=predictor,
                        predicted_author=predicted_author
                    )
                    
                    self.stdout.write(
                        f'予想を作成: {predictor.nickname} が '
                        f'{novel.title} の作者を {predicted_author.nickname} と予想！'
                        f'（{"正解" if predicted_author == novel.original_author else "不正解"}）'
                    )

                    created_count += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'予想作成中にエラー発生: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'テスト予想データを {created_count} 件作成したで！\n'
            f'参加者数: {game.entrants.count()}人'
        ))

        # 時間を進めるかどうかを確認
        self.stdout.write(self.style.WARNING(
            '予想期間を終了して結���を表示するために時間を進めますか？ (yes/no): '
        ))
        
        if input().lower() == 'yes':
            # 現在時刻を予想期間終了後に設定
            future_time = prediction_end + timezone.timedelta(minutes=1)
            
            # 確認メッセージを表示
            self.stdout.write(self.style.WARNING(
                f'システム時刻を {future_time} に進めます。よろしいですか？ (yes/no): '
            ))
            
            if input().lower() == 'yes':
                # MaturiGameモデルの日時を更新
                game.maturi_end_date = future_time.date()
                game.prediction_end_date = prediction_end.date()
                game.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'時間を進めて、予想期間を終了したで！\n'
                    f'結果が見えるようになったで！'
                ))
            else:
                self.stdout.write('時間を進めるのをキャンセルしたで')
        else:
            self.stdout.write(
                '時間を進めへんかったで。\n'
                '1分待ってから結果を確認してな！'
            )