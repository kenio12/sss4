from django.core.management.base import BaseCommand
from game_maturi.models import MaturiGame
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = '祭り小説の公開予定日時を調整する'

    def handle(self, *args, **options):
        try:
            # 現在の祭りを取得
            game = MaturiGame.objects.last()
            if not game:
                self.stdout.write(self.style.ERROR('祭りが見つかりませんでした。'))
                return

            # 現在時刻の10分後を設定
            new_scheduled_time = timezone.now() + timedelta(minutes=10)

            # 祭り小説の状態を表示
            self.stdout.write(self.style.WARNING('\n=== 祭り小説の状態 ==='))
            maturi_novels = game.maturi_novels.filter(status='scheduled')
            
            if not maturi_novels:
                self.stdout.write('公開待ちの祭り小説が見つかりません。')
                return

            for novel in maturi_novels:
                self.stdout.write(f"- {novel.title}")
                self.stdout.write(f"  現在の公開予定日時: {novel.scheduled_at}")
                self.stdout.write(f"  新しい公開予定日時: {new_scheduled_time}")

            self.stdout.write(self.style.WARNING('\n小説の公開予定日時を更新しますか？ (yes/no): '))
            if input().lower() == 'yes':
                # 日程を更新
                for novel in maturi_novels:
                    novel.scheduled_at = new_scheduled_time
                    novel.save()
                
                self.stdout.write(self.style.SUCCESS('\n小説の公開予定日時を更新しました！'))
                self.stdout.write(f'10分後（{new_scheduled_time}）に公開されます！')
            else:
                self.stdout.write(self.style.WARNING('\n更新をキャンセルしました。'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}')) 