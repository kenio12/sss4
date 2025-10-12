"""
データ移行コマンド: eventフィールド設定とgenre変更

実行方法:
    python manage.py migrate_event_data

処理内容:
1. is_same_title_game=Trueの作品
   → event='同タイトル' + genre='その他'に変更

2. genre='祭り'の作品
   → event='祭り' + genre='その他'に変更

3. is_same_title_gameフラグは削除せず保持
"""
from django.core.management.base import BaseCommand
from novels.models import Novel


class Command(BaseCommand):
    help = 'eventフィールド設定とgenre変更のデータ移行'

    def handle(self, *args, **options):
        # 1. is_same_title_game=Trueの作品を処理
        same_title_novels = Novel.objects.filter(is_same_title_game=True)
        same_title_count = same_title_novels.count()

        self.stdout.write(f'\n【同タイトルゲーム作品】処理対象: {same_title_count}件')

        for novel in same_title_novels:
            old_genre = novel.genre
            novel.event = '同タイトル'
            novel.genre = 'その他'
            novel.save()
            self.stdout.write(
                f'  - {novel.title[:30]}: genre={old_genre} → その他, event=同タイトル'
            )

        # 2. genre='祭り'の作品を処理
        maturi_novels = Novel.objects.filter(genre='祭り')
        maturi_count = maturi_novels.count()

        self.stdout.write(f'\n【祭り作品】処理対象: {maturi_count}件')

        for novel in maturi_novels:
            novel.event = '祭り'
            novel.genre = 'その他'
            novel.save()
            self.stdout.write(
                f'  - {novel.title[:30]}: genre=祭り → その他, event=祭り'
            )

        # 3. 旧genreを「その他」に統一（event指定のない作品）
        # 設計図のGENRE_CHOICESにないgenreを持つ作品を処理
        valid_genres = ['恋愛', 'SF', 'ミステリー', 'ホラー', 'ファンタジー', 'その他']
        invalid_genre_novels = Novel.objects.exclude(genre__in=valid_genres)
        invalid_count = invalid_genre_novels.count()

        self.stdout.write(f'\n【旧ジャンル作品】処理対象: {invalid_count}件')

        for novel in invalid_genre_novels:
            old_genre = novel.genre
            novel.genre = 'その他'
            novel.save()
            self.stdout.write(
                f'  - {novel.title[:30]}: genre={old_genre} → その他'
            )

        # 結果サマリー
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ データ移行完了\n'
            f'   - 同タイトル作品: {same_title_count}件\n'
            f'   - 祭り作品: {maturi_count}件\n'
            f'   - 旧ジャンル作品: {invalid_count}件\n'
            f'   - 合計: {same_title_count + maturi_count + invalid_count}件\n'
        ))
