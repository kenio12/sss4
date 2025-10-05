from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from game_maturi.models import MaturiGame, Phrase, GamePrediction
from novels.models import Novel
import datetime
import random

User = get_user_model()

class Command(BaseCommand):
    help = '祭りのテストデータを作成します'

    def handle(self, *args, **options):
        # 1. 祭り作家（ダミー）作成 - ユニーク制約を考慮
        maturi_writer, _ = User.objects.get_or_create(
            email='maturi_writer@example.com',
            defaults={
                'username': f'maturi_writer_{timezone.now().strftime("%Y%m%d%H%M%S")}',  # タイムスタンプ付加
                'nickname': f'祭り作家_{timezone.now().strftime("%Y%m%d%H%M%S")}',  # タイムスタンプ付加
                'password': 'maturi123',
                'user_type': User.MATURI_WRITER,
                'email_confirmed': True,
            }
        )

        # 2. テストユーザー作成 - タイムスタンプ付加
        test_users = []
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        for i in range(1, 7):
            user, _ = User.objects.get_or_create(
                email=f'test_user{i}_{timestamp}@example.com',
                defaults={
                    'username': f'test_user{i}_{timestamp}',
                    'nickname': f'テストユーザー{i}_{timestamp}',
                    'password': 'testpass123',
                    'user_type': User.FREE_MEMBER,
                    'email_confirmed': True,
                }
            )
            test_users.append(user)

        # 3. 語句作成
        phrases = [
            "青空", "夕暮れ", "星空", "雨上がり", "朝日",
            "月光", "虹", "雷", "霧", "雪", "風", "雲"
        ]
        phrase_objects = []
        for phrase_text in phrases:
            phrase, _ = Phrase.objects.get_or_create(text=phrase_text)
            phrase_objects.append(phrase)

        # 4. 祭り作成（2024年の祭り）- タイトルフォーマットを修正
        maturi_game, _ = MaturiGame.objects.get_or_create(
            title='2024年〜2025年の祭り',
            defaults={
                'description': '2024年11月の祭り（テストデータ）',
                'year': '2024年〜2025年の祭り',
                # 祭り全体期間
                'maturi_start_date': datetime.date(2024, 11, 1),
                'maturi_end_date': datetime.date(2024, 12, 31),
                # 各期間
                'entry_start_date': datetime.date(2024, 11, 20),
                'entry_end_date': datetime.date(2024, 11, 22),
                'start_date': datetime.date(2024, 11, 21),
                'end_date': datetime.date(2024, 11, 23),
                'prediction_start_date': datetime.date(2024, 11, 24),
                'prediction_end_date': datetime.date(2024, 11, 25),
                'dummy_author': maturi_writer
            }
        )
        maturi_game.phrases.set(phrase_objects)
        
        # 5. エントラント追加
        maturi_game.entrants.set(test_users)

        # 6. 小説作成（各ユーザー4つずつ）
        for user in test_users:
            for i in range(4):
                novel = Novel.objects.create(
                    title=f'{user.nickname}の祭り小説{i+1}',
                    content=f'''これは{user.nickname}の{i+1}番目の小説です。
                    青空が広がる朝、夕暮れの星空が見え始め、
                    雨上がりの空には朝日が差していました。''',
                    author=maturi_writer,  # 祭り作家として投稿
                    original_author=user,  # 本来の作者
                    genre='祭り',
                    status='published',
                    published_date=timezone.now()
                )
                maturi_game.maturi_novels.add(novel)

        # 7. 予想を追加（各ユーザーが他の小説に対して予想）
        for predictor in test_users:
            # 自分以外の小説に対して予想
            for novel in maturi_game.maturi_novels.exclude(original_author=predictor):
                # 自分以外のユーザーからランダムに予想
                other_users = [u for u in test_users if u != predictor]
                predicted_author = random.choice(other_users)
                
                GamePrediction.objects.get_or_create(
                    novel=novel,
                    predictor=predictor,
                    defaults={'predicted_author': predicted_author}
                )

        self.stdout.write(self.style.SUCCESS(f'''
        テストデータ作成完了！
        - ユーザー数: {len(test_users)}
        - 語句数: {len(phrase_objects)}
        - 小説数: {maturi_game.maturi_novels.count()}
        - 予想数: {GamePrediction.objects.count()}
        ''')) 