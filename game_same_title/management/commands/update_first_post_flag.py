"""
一番槍フラグ修正コマンド

MonthlySameTitleInfoで一番槍として記録されてる小説に
is_first_post=Trueフラグを付ける
"""
from django.core.management.base import BaseCommand
from game_same_title.models import MonthlySameTitleInfo
from novels.models import Novel


class Command(BaseCommand):
    help = '一番槍として記録されてる小説にis_first_post=Trueフラグを設定'

    def handle(self, *args, **options):
        # MonthlySameTitleInfoで一番槍記録を全部取得
        ichiban_yari_records = MonthlySameTitleInfo.objects.exclude(
            novel__isnull=True
        ).select_related('novel')

        updated_count = 0
        already_set_count = 0

        for record in ichiban_yari_records:
            novel = record.novel

            if novel.is_first_post:
                already_set_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'既に設定済み: {novel.title} ({record.month})'
                    )
                )
            else:
                novel.is_first_post = True
                novel.save(update_fields=['is_first_post'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ フラグ設定完了: {novel.title} ({record.month}) - 著者: {novel.author.nickname}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n完了！ 新規設定: {updated_count}件、既存: {already_set_count}件'
            )
        )
