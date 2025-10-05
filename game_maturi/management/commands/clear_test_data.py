from django.core.management.base import BaseCommand
from game_maturi.models import MaturiGame, GamePrediction
from novels.models import Novel
from django.db import transaction

class Command(BaseCommand):
    help = '祭り関連のテストデータを削除します'

    def handle(self, *args, **options):
        with transaction.atomic():
            try:
                # 祭り関連の予想を削除
                GamePrediction.objects.all().delete()
                print("祭りの予想データを削除しました")

                # 祭り小説を削除
                Novel.objects.filter(genre='祭り').delete()
                print("祭り小説を削除しました")

                # 祭りデータを削除
                MaturiGame.objects.all().delete()
                print("祭りデータを削除しました")

            except Exception as e:
                print(f"エラーが発生しました: {e}")
                raise