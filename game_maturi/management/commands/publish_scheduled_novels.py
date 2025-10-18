from django.core.management.base import BaseCommand
from django.utils import timezone
from novels.models import Novel

class Command(BaseCommand):
    help = '予約公開された小説を自動公開する'

    def handle(self, *args, **options):
        now = timezone.now()
        published_count = 0

        # 予約公開時刻が過ぎた小説を取得
        scheduled_novels = Novel.objects.filter(
            status='scheduled',
            scheduled_at__lte=now
        )

        self.stdout.write(f'処理対象の予約公開小説: {scheduled_novels.count()}件')

        for novel in scheduled_novels:
            novel.status = 'published'
            novel.published_date = now
            novel.save()
            published_count += 1

            self.stdout.write(f'  - 小説 "{novel.title}" を公開')

        if published_count == 0:
            self.stdout.write(
                self.style.WARNING('公開する予約小説はありませんでした')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ 合計 {published_count}件の小説を公開しました')
            )
