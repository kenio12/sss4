from django.core.management.base import BaseCommand
from game_maturi.models import MaturiGame, GamePrediction
from novels.models import Novel, Comment
from accounts.models import User

class Command(BaseCommand):
    help = '祭り関連の全データを削除する'

    def handle(self, *args, **options):
        try:
            # 確認メッセージを表示
            self.stdout.write(self.style.WARNING(
                '注意: 祭り関連の全データを削除しようとしています。\n'
                '本当に削除しますか？ (yes/no): '
            ))
            
            # ユーザー入力を待つ
            if input().lower() != 'yes':
                self.stdout.write('キャンセルしました')
                return

            # 削除前のデータ数を取得
            maturi_count = MaturiGame.objects.count()
            prediction_count = GamePrediction.objects.count()
            novel_count = Novel.objects.filter(genre='祭り').count()
            comment_count = Comment.objects.filter(is_maturi_comment=True).count()
            writer_count = User.objects.filter(email__startswith='writer_').count()

            # 祭り関連のデータを削除
            GamePrediction.objects.all().delete()
            Comment.objects.filter(is_maturi_comment=True).delete()
            Novel.objects.filter(genre='祭り').delete()
            MaturiGame.objects.all().delete()
            User.objects.filter(email__startswith='writer_').delete()

            self.stdout.write(self.style.SUCCESS(
                f'データを削除したで！\n'
                f'- 祭り: {maturi_count}件\n'
                f'- 予想: {prediction_count}件\n'
                f'- 小説: {novel_count}件\n'
                f'- コメント: {comment_count}件\n'
                f'- 作家: {writer_count}件'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
            raise