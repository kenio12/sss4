from django.core.management.base import BaseCommand
from game_maturi.models import MaturiGame
from django.utils import timezone
from accounts.models import User

class Command(BaseCommand):
    help = '過去の祭りの基本設定を作成する'

    def handle(self, *args, **options):
        try:
            # 祭り作家を取得または作成
            maturi_writer, _ = User.objects.get_or_create(
                username='maturi_writer',
                defaults={
                    'nickname': '祭り作家',
                    'email': 'maturi@example.com'
                }
            )

            # テスト用の作家を作成
            writers = {}
            for letter in ['a', 'b', 'c', 'd', 'e']:
                writer, _ = User.objects.get_or_create(
                    username=f'writer_{letter}_1',
                    defaults={
                        'nickname': f'作家{letter.upper()}',
                        'email': f'writer_{letter}@example.com'
                    }
                )
                writers[letter] = writer

            # 1年前の日付を計算
            past_publish_time = timezone.now() - timezone.timedelta(days=389)
            last_year = timezone.now().year - 1

            # 過去の祭り作成（終了日を確実に過去に）
            past_maturi = MaturiGame.objects.create(
                title=f'{last_year}年〜{last_year+1}年の祭り',
                description=f'{last_year}年の小説祭り',
                maturi_start_date=(past_publish_time - timezone.timedelta(days=6)).date(),
                maturi_end_date=(past_publish_time + timezone.timedelta(days=2)).date(),
                entry_start_date=(past_publish_time - timezone.timedelta(days=5)).date(),
                entry_end_date=(past_publish_time - timezone.timedelta(days=3)).date(),
                start_date=(past_publish_time - timezone.timedelta(days=2)).date(),
                end_date=past_publish_time.date(),
                prediction_start_date=past_publish_time.date(),
                prediction_end_date=(past_publish_time + timezone.timedelta(days=2)).date(),
                novel_publish_start_date=past_publish_time.date(),
                year=f'{last_year}年〜{last_year+1}年の祭り'
            )

            # 作家を参加者として追加
            past_maturi.entrants.add(maturi_writer)
            for writer in writers.values():
                past_maturi.entrants.add(writer)

            self.stdout.write(self.style.SUCCESS(
                f'過去の祭り「{past_maturi.title}」を作成したで！\n'
                f'祭り開始日: {past_maturi.maturi_start_date}\n'
                f'祭り終了日: {past_maturi.maturi_end_date}\n'
                f'参加作家: {", ".join(w.nickname for w in writers.values())}'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
            raise
