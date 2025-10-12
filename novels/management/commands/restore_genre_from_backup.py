from django.core.management.base import BaseCommand
import subprocess
import os

class Command(BaseCommand):
    help = '一時データベースから元のジャンル情報を復元する緊急修正コマンド'

    def handle(self, *args, **options):
        self.stdout.write('一時データベースからジャンル情報を取得中...')

        # 一時データベースからgenre情報を取得
        result = subprocess.run(
            ['heroku', 'pg:psql', 'TEMP_RESTORE_DB', '--app', 'sss4', '-c',
             'SELECT id, genre FROM novels_novel ORDER BY id;'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            self.stdout.write(self.style.ERROR(f'エラー: {result.stderr}'))
            return

        # 出力をパース
        lines = result.stdout.strip().split('\n')

        # ヘッダーと区切り線をスキップ
        data_lines = [line for line in lines if line.strip() and not line.startswith('--') and not line.startswith('id ')]

        self.stdout.write(f'取得したレコード数: {len(data_lines)}')

        # genreマッピングを作成
        genre_mapping = {}
        for line in data_lines:
            parts = line.split('|')
            if len(parts) >= 2:
                try:
                    novel_id = int(parts[0].strip())
                    genre = parts[1].strip()
                    genre_mapping[novel_id] = genre
                except ValueError:
                    continue

        self.stdout.write(f'有効なgenreマッピング: {len(genre_mapping)}件')

        # データベースを更新
        from novels.models import Novel

        updated_count = 0
        skipped_count = 0

        for novel_id, genre in genre_mapping.items():
            try:
                novel = Novel.objects.get(id=novel_id)
                if novel.genre != genre:
                    novel.genre = genre
                    novel.save(update_fields=['genre'])
                    updated_count += 1
                else:
                    skipped_count += 1
            except Novel.DoesNotExist:
                self.stdout.write(f'小説ID {novel_id} は存在しません（削除済み？）')
                continue

        self.stdout.write(self.style.SUCCESS(f'更新完了: {updated_count}件'))
        self.stdout.write(f'スキップ: {skipped_count}件（既に正しいgenre）')

        # 更新後のジャンル分布を確認
        from django.db.models import Count
        genre_counts = Novel.objects.values('genre').annotate(count=Count('id')).order_by('-count')

        self.stdout.write('\n更新後のジャンル分布:')
        for item in genre_counts[:10]:
            self.stdout.write(f"  {item['genre']}: {item['count']}件")
