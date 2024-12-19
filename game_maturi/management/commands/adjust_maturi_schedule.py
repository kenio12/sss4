from django.core.management.base import BaseCommand
from game_maturi.models import MaturiGame
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = '祭りの日程を調整する（小説公開を早める）'

    def handle(self, *args, **options):
        try:
            # 現在の祭りを取得
            game = MaturiGame.objects.last()
            if not game:
                self.stdout.write(self.style.ERROR('祭りが見つかりませんでした。'))
                return

            # 現在時刻を基準に設定
            now = timezone.now()
            today = now.date()

            # 新しい日程を設定（予想期間は変更しない）
            new_schedule = {
                'novel_publish_start_date': now + timedelta(minutes=10),  # 小説公開は10分後
                'prediction_start_date': today,  # 予想開始は今日から
            }

            # 祭り小説の状態を表示
            self.stdout.write(self.style.WARNING('\n=== 祭り小説の状態 ==='))
            maturi_novels = game.maturi_novels.all()
            for novel in maturi_novels:
                self.stdout.write(f"- {novel.title}")
                self.stdout.write(f"  状態: {novel.status}")
                self.stdout.write(f"  公開予定日時: {novel.scheduled_at}")

            # 変更前の日程を表示
            self.stdout.write(self.style.WARNING('\n=== 現在の日程 ==='))
            self.stdout.write(f'小説公開日時: {game.novel_publish_start_date}')
            self.stdout.write(f'予想期間: {game.prediction_start_date} 〜 {game.prediction_end_date}')

            # 確認メッセージ
            self.stdout.write(self.style.WARNING('\n=== 新しい日程 ==='))
            self.stdout.write(f'小説公開日時: {new_schedule["novel_publish_start_date"]}')
            self.stdout.write(f'予想開始日: {new_schedule["prediction_start_date"]}')
            self.stdout.write('※予想終了日は変更しません')

            self.stdout.write(self.style.WARNING('\n日程を更新しますか？ (yes/no): '))
            if input().lower() == 'yes':
                # 日程を更新
                for field, value in new_schedule.items():
                    setattr(game, field, value)
                game.save()
                
                self.stdout.write(self.style.SUCCESS('\n日程を更新しました！'))
                self.stdout.write('10分後に小説が公開され、予想が始まります！')
            else:
                self.stdout.write(self.style.WARNING('\n更新をキャンセルしました。'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}')) 