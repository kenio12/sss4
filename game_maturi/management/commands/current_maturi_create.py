from django.core.management.base import BaseCommand
from accounts.models import User
from game_maturi.models import MaturiGame, GamePrediction, Phrase
from novels.models import Novel, Comment
from django.utils import timezone
from django.db import transaction
import random
import datetime
import time
from game_maturi.tasks import publish_scheduled_novels

class Command(BaseCommand):
    help = '現在の祭りを作成する'
    def handle(self, *args, **options):
        with transaction.atomic():
            try:
                # 現在時刻を基準に設定
                now = timezone.now()
                print(f"現在時刻: {now}")

                # 各期間を設定
                maturi_start_date = now.date()  # 祭り開始は今日から
                writing_end_date = now.date() + timezone.timedelta(days=7)  # 執筆期間は7日間
                prediction_start_date = writing_end_date + timezone.timedelta(days=1)  # 執筆終了翌日から予想開始
                prediction_end_date = prediction_start_date + timezone.timedelta(days=2)  # 予想期間は2日間
                maturi_end_date = prediction_end_date + timezone.timedelta(days=1)  # 祭り終了は予想期間終了翌日

                # 小説公開時刻（10分後）を設定
                publish_time = now + timezone.timedelta(minutes=10)
                print(f"小説公開予定時刻: {publish_time}")

                print(f"=== 祭りの期間設定 ===")
                print(f"祭り全体: {maturi_start_date} 〜 {maturi_end_date}")
                print(f"執筆期間: {maturi_start_date} 〜 {writing_end_date}")
                print(f"予想期間: {prediction_start_date} 〜 {prediction_end_date}")

                maturi = MaturiGame.objects.create(
                    title='2024年〜2025年の祭り',
                    description='2024年11月の小説祭り',
                    maturi_start_date=maturi_start_date,
                    maturi_end_date=maturi_end_date,
                    prediction_start_date=prediction_start_date,
                    prediction_end_date=prediction_end_date,
                    novel_publish_start_date=publish_time,
                    year='2024年〜2025年の祭り',
                    entry_start_date=maturi_start_date,  # エントリー開始は祭り開始と同時
                    entry_end_date=maturi_start_date + timezone.timedelta(days=2),  # エントリー期間は2日間
                    start_date=maturi_start_date,  # 執筆開始
                    end_date=writing_end_date  # 執筆終了
                )

                print(f"作成された祭り:")  # デバッグ出力
                print(f"- ID: {maturi.id}")
                print(f"- タイトル: {maturi.title}")
                print(f"- 開始日: {maturi.maturi_start_date}")
                print(f"- 終了日: {maturi.maturi_end_date}")

                # 祭り作家を取得または作成
                maturi_writer, _ = User.objects.get_or_create(
                    username='maturi_writer',
                    defaults={
                        'nickname': '祭り作家',
                        'email': 'maturi@example.com'
                    }
                )

                # テスト用の作家を作成して祭りにエントリー
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
                    # ここで祭りにエントリー
                    maturi.entrants.add(writer)
                    print(f"作家{letter.upper()}を祭りにエントリーしました")

                # 小説を作成する
                for letter, writer in writers.items():
                    # 各作家がランダムに2〜3個の小説を書く
                    num_novels = random.randint(2, 3)
                    for j in range(num_novels):
                        novel = Novel.objects.create(
                            title=f'小説{letter.upper()}{j+1}',  # 例：小説A1, 小説A2
                            content=f'これは小説{letter.upper()}{j+1}の内容です。',
                            author=maturi_writer,  # 祭り作家として保存
                            original_author=writer,  # ここを追加！
                            scheduled_at=publish_time,
                            status='scheduled',
                            genre='祭り'
                        )
                        # ManyToManyFieldを使って関連付け
                        maturi.maturi_novels.add(novel)
                        print(f"小説が作成されました: {novel.title} (作者: {writer.nickname})")

                # フレーズを作成
                phrases = [
                    '冬の夜空',
                    '雪の結晶',
                    '暖かい部屋',
                    'クリスマス',
                    '年末年始',
                    '初日の出',
                    '新年の抱負',
                    '冬の散歩',
                    'こたつでみかん',
                    '温かい鍋'
                ]

                # 既存のフレーズを全て削除
                Phrase.objects.all().delete()
                print("既存のフレーズを削除しました")

                # 新しいフレーズを作成
                for phrase_text in phrases:
                    phrase = Phrase.objects.create(
                        text=phrase_text
                    )
                    # ManyToManyFieldの関連付け
                    maturi.phrases.add(phrase)
                    print(f"フレーズを作成: {phrase_text}")

            except Exception as e:
                print(f"エラーが発生しました: {e}")
                raise