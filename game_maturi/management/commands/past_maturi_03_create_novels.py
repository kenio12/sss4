from django.core.management.base import BaseCommand
from accounts.models import User
from game_maturi.models import MaturiGame, Phrase
from novels.models import Novel, Comment
from django.utils import timezone
from django.db import transaction
import random

class Command(BaseCommand):
    help = '過去の祭りの小説を作成する'

    def handle(self, *args, **options):
        try:
            # 過去の祭りを取得
            past_maturi = MaturiGame.objects.filter(
                title__contains=str(timezone.now().year - 1)
            ).first()

            if not past_maturi:
                self.stdout.write(self.style.ERROR('過去の祭りが見つかれへんで'))
                return

            # 共通の語句を設定
            words = [
                '桜', '月光', '風鈴', '花火', '浴衣',
                '祭囃子', '提灯', '屋台', '神輿', '夕涼み'
            ]

            # 作家と作品数の定義
            writer_novels = {
                'a': 3, 'b': 2, 'c': 1, 'd': 2, 'e': 2
            }

            novel_number = 1
            created_novels = []

            # 過去の日付を計算
            past_publish_time = timezone.now() - timezone.timedelta(days=389)

            # 各作家の小説を作成
            for letter, novel_count in writer_novels.items():
                writer = past_maturi.entrants.get(username=f'writer_{letter}_1')
                
                for i in range(novel_count):
                    # ここで語句をランダムに選んで一回だけ登録
                    selected_words = random.sample(words, random.randint(5, 7))
                    for word in selected_words:
                        phrase, _ = Phrase.objects.get_or_create(text=word)
                        past_maturi.phrases.add(phrase)  # 一回だけ追加

                    content = f'祭り小説の内容です。作者は{writer.nickname}、作品番号は{novel_number}です。\n\n'
                    content += f'使用した語句: {", ".join(selected_words)}\n\n'
                    content += '本文:\n'
                    for word in selected_words:
                        content += f'{word}が輝く夜空の下、祭りの雰囲気が漂っていました。\n'
                        content += f'{word}にまつわる思い出が、この物語の中心となります。\n'

                    # 小説を作成（予約公開状態で）
                    novel = Novel.objects.create(
                        title=f'過去の祭り小説{novel_number}',
                        content=content,
                        author=past_maturi.entrants.get(username='maturi_writer'),
                        original_author=writer,
                        genre='祭り',
                        status='published',
                        published_date=past_publish_time,
                        scheduled_at=past_publish_time
                    )
                    past_maturi.maturi_novels.add(novel)
                    created_novels.append(novel)
                    novel_number += 1

            self.stdout.write(self.style.SUCCESS(
                f'過去の祭り「{past_maturi.title}」の小説を作成したで！\n'
                f'作成した小説数: {len(created_novels)}件\n'
                f'作家ごとの投稿数:\n' + 
                '\n'.join([f'作家{letter.upper()}の投稿数: {count}作品' 
                          for letter, count in writer_novels.items()])
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
            raise
