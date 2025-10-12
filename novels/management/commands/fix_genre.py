from django.core.management.base import BaseCommand
from novels.models import Novel


class Command(BaseCommand):
    help = '「その他」ジャンルを「未分類」に変更する緊急修正コマンド'

    def handle(self, *args, **options):
        # 「その他」を「未分類」に変更
        other_novels = Novel.objects.filter(genre='その他')
        count = other_novels.count()

        self.stdout.write(
            self.style.WARNING(
                f'「その他」ジャンルの小説: {count}件を「未分類」に変更します...'
            )
        )

        updated = other_novels.update(genre='未分類')

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ 完了！{updated}件の小説のジャンルを「未分類」に変更しました'
            )
        )

        # 確認
        remaining = Novel.objects.filter(genre='その他').count()
        if remaining == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    '✅ 「その他」ジャンルは完全に削除されました'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'⚠️ まだ{remaining}件の「その他」ジャンルが残っています'
                )
            )
