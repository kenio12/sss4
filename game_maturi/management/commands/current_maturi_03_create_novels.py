from django.core.management.base import BaseCommand
from accounts.models import User
from game_maturi.models import MaturiGame, Phrase
from novels.models import Novel
from django.utils import timezone
from django.db import transaction
import random

class Command(BaseCommand):
    help = '現在の祭りの小説を作成する'

    def handle(self, *args, **options):
        try:
            # 現在の祭りを取得
            current_maturi = MaturiGame.find_current_game()
            if not current_maturi:
                self.stdout.write(self.style.ERROR('現在の祭りが見つかれへんで'))
                return

            # 現在の祭りから語句を取得するように変更
            available_phrases = list(current_maturi.phrases.all())
            if not available_phrases:
                self.stdout.write(self.style.ERROR('祭りに設定された語句が見つかれへんで'))
                return

            # 作家と作品数の定義
            writer_novels = {
                'a': 3, 'b': 2, 'c': 1, 'd': 2, 'e': 2
            }

            novel_number = 1
            created_novels = []

            # 各作家の小説を作成
            for letter, novel_count in writer_novels.items():
                writer = User.objects.get(username=f'current_writer_{letter}')
                
                for i in range(novel_count):
                    # 祭りの語句から5つ以上をランダムに選択
                    selected_phrases = random.sample(available_phrases, random.randint(5, len(available_phrases)))
                    selected_words = [phrase.text for phrase in selected_phrases]

                    content = f'現在の祭り小説です。作者は{writer.nickname}、作品番号は{novel_number}です。\n\n'
                    content += f'使用した語句: {", ".join(selected_words)}\n\n'
                    content += '本文:\n'
                    for word in selected_words:
                        content += f'{word}が輝く真夏の日、祭りの音が響いていました。\n'
                        content += f'{word}に込められた想いが、物語を彩ります。\n'

                    # 小説を作成（昨日の日付で予約公開）
                    yesterday = timezone.now() - timezone.timedelta(days=1)
                    novel = Novel.objects.create(
                        title=f'現在の祭り小説{novel_number}',
                        content=content,
                        author=User.objects.get(username='current_maturi_writer'),
                        original_author=writer,
                        genre='祭り',
                        status='scheduled',
                        scheduled_at=yesterday
                    )
                    current_maturi.maturi_novels.add(novel)
                    created_novels.append(novel)
                    novel_number += 1

            self.stdout.write(self.style.SUCCESS(
                f'現在の祭り「{current_maturi.title}」の小説を作成したで！\n'
                f'作成した小説数: {len(created_novels)}件\n'
                f'作家ごとの投稿数:\n' + 
                '\n'.join([f'作家{letter.upper()}の投稿数: {count}作品' 
                          for letter, count in writer_novels.items()])
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
            raise
