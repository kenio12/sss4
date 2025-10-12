from django.core.management.base import BaseCommand
from django.utils import timezone
from novels.models import Novel
from django.db.models import Min


class Command(BaseCommand):
    help = '同タイトル・同月で最初に投稿した小説に一番槍フラグを付与'

    def handle(self, *args, **options):
        # 同タイトルイベントの小説を取得
        same_title_novels = Novel.objects.filter(
            event='同タイトル',
            status='published'
        ).exclude(same_title_event_month__isnull=True)

        # タイトル + 月でグループ化
        title_month_groups = {}
        for novel in same_title_novels:
            key = (novel.title, novel.same_title_event_month)
            if key not in title_month_groups:
                title_month_groups[key] = []
            title_month_groups[key].append(novel)

        updated_count = 0
        cleared_count = 0

        # 各グループで最初の投稿を特定
        for (title, month), novels in title_month_groups.items():
            # 公開日時が最も早い小説を取得
            earliest_novel = min(novels, key=lambda n: n.published_date)

            for novel in novels:
                if novel.id == earliest_novel.id:
                    # 一番槍フラグを付与
                    if not novel.is_first_post:
                        novel.is_first_post = True
                        novel.first_post_acquired_at = timezone.now()
                        novel.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ 一番槍付与: {novel.title} ({month}) by {novel.author.nickname}'
                            )
                        )
                else:
                    # 一番槍でない小説はフラグをクリア
                    if novel.is_first_post:
                        novel.is_first_post = False
                        novel.first_post_acquired_at = None
                        novel.save()
                        cleared_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️ 一番槍解除: {novel.title} ({month}) by {novel.author.nickname}'
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n完了！一番槍付与: {updated_count}件、解除: {cleared_count}件'
            )
        )
