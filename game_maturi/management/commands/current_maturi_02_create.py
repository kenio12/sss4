from django.core.management.base import BaseCommand
from game_maturi.models import MaturiGame, Phrase
from django.utils import timezone
from accounts.models import User
from datetime import date

class Command(BaseCommand):
    help = '現在の祭りの基本設定を作成する'

    def handle(self, *args, **options):
        try:
            # 祭り作家を取得または作成（現在用）
            maturi_writer, _ = User.objects.get_or_create(
                username='current_maturi_writer',
                defaults={
                    'nickname': '現在の祭り作家',
                    'email': 'current_maturi@example.com'
                }
            )

            # テスト用の作家を作成（現在用）
            writers = {}
            for letter in ['a', 'b', 'c', 'd', 'e']:
                writer, _ = User.objects.get_or_create(
                    username=f'current_writer_{letter}',
                    defaults={
                        'nickname': f'現在作家{letter.upper()}',
                        'email': f'current_{letter}@example.com'
                    }
                )
                writers[letter] = writer

            # 現在の年を取得
            current_year = timezone.now().year
            current_month = timezone.now().month

            # 日付を設定（dateオブジェクトのみを使用）
            maturi_start_date = date(current_year, current_month, 1)      # 祭り開始: 1日
            entry_start_date = date(current_year, current_month, 3)       # エントリー開始: 3日
            writing_start_date = date(current_year, current_month, 5)     # 執筆開始: 5日
            entry_end_date = date(current_year, current_month, 19)        # エントリー終了: 19日
            writing_end_date = date(current_year, current_month, 20)      # 執筆終了: 20日
            prediction_start_date = date(current_year, current_month, 21)  # 予想開始: 21日
            prediction_end_date = date(current_year, current_month, 25)    # 予想終了: 25日
            maturi_end_date = date(current_year, current_month, 30)       # 祭り終了: 30日

            # 語句を作成（get_or_createで重複を防ぐ）
            phrases = [
                '青春', '恋愛', '友情', '冒険',
                '幻想', '日常', '学園', 'ファンタジー'
            ]
            phrase_objects = []
            for phrase_text in phrases:
                phrase, _ = Phrase.objects.get_or_create(text=phrase_text)
                phrase_objects.append(phrase)

            # 現在の祭り作成
            current_maturi = MaturiGame.objects.create(
                title=f'{current_year}年〜{current_year + 1}年の祭り',  # フォーマットを修正
                description='テスト用祭り',
                
                # 執筆期間
                start_date=maturi_start_date,
                end_date=maturi_end_date,
                
                # 予想期間を明日から明後日まで
                prediction_start_date=prediction_start_date,
                prediction_end_date=prediction_end_date,
                
                # 祭り期間
                maturi_start_date=maturi_start_date,
                maturi_end_date=maturi_end_date,
                
                # エントリー期間
                entry_start_date=entry_start_date,
                entry_end_date=entry_end_date,
                
                # 小説公開
                novel_publish_start_date=writing_start_date,
                
                year=f'{current_year}年〜{current_year + 1}年の祭り'  # yearも同じフォーマットに
            )

            # 語句を追加
            current_maturi.phrases.add(*phrase_objects)

            # 作家を参加者として追加
            current_maturi.entrants.add(maturi_writer)
            for writer in writers.values():
                current_maturi.entrants.add(writer)

            self.stdout.write(self.style.SUCCESS(
                f'現在の祭り「{current_maturi.title}」を作成したで！\n'
                f'作成時刻: {timezone.now().strftime("%H:%M:%S")}\n'
                f'予想開始: {prediction_start_date.strftime("%Y-%m-%d")}\n'
                f'予想終了: {prediction_end_date.strftime("%Y-%m-%d")}\n'
                f'参加作家: {", ".join(w.nickname for w in writers.values())}\n'
                f'設定語句: {", ".join(p.text for p in phrase_objects)}'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
            raise