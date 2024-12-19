from django.core.management.base import BaseCommand
from accounts.models import User
from game_maturi.models import MaturiGame, GamePrediction, Phrase
from novels.models import Novel, Comment
from django.utils import timezone
from django.db import transaction
import random
import datetime
from game_maturi.tasks import publish_scheduled_novels
import time

class Command(BaseCommand):
    def handle(self, *args, **options):
        with transaction.atomic():
            try:
                # 既存の祭りデータを削除
                MaturiGame.objects.all().delete()
                Phrase.objects.all().delete()
                
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

                # 共通の語句を設定
                words = [
                    '桜', '月光', '風鈴', '花火', '浴衣',
                    '祭囃子', '提灯', '屋台', '神輿', '夕涼み'
                ]

                # 作家と作品数の定義
                writer_novels = {
                    'a': 3, 'b': 2, 'c': 1, 'd': 2, 'e': 2
                }

                # コメントのテストデータ
                comment_texts = [
                    "とても面白い作品でした！",
                    "素晴らしい展開ですね。",
                    "この作品は誰の作品でしょうか？",
                    "語句の使い方が上手いです。",
                    "祭りの雰囲気がよく伝わってきます。"
                ]

                # 1年前の祭り作成（日付を調整）
                past_publish_time = timezone.now() - timezone.timedelta(days=389)
                last_year = timezone.now().year - 1
                past_maturi = MaturiGame.objects.create(
                    title=f'{last_year}年〜{last_year+1}年の祭り',
                    description=f'{last_year}年の小説祭り',
                    maturi_start_date=(past_publish_time - timezone.timedelta(days=6)).date(),
                    maturi_end_date=(past_publish_time + timezone.timedelta(days=30)).date(),
                    entry_start_date=(past_publish_time - timezone.timedelta(days=5)).date(),
                    entry_end_date=(past_publish_time - timezone.timedelta(days=3)).date(),
                    start_date=(past_publish_time - timezone.timedelta(days=2)).date(),
                    end_date=past_publish_time.date(),
                    prediction_start_date=past_publish_time.date(),
                    prediction_end_date=(past_publish_time + timezone.timedelta(days=2)).date(),
                    novel_publish_start_date=past_publish_time.date(),
                    year=f'{last_year}年〜{last_year+1}年の祭り'
                )

                # 1年後の祭り作成
                next_year = timezone.now().year + 1
                future_maturi = MaturiGame.objects.create(
                    title=f'{next_year}年〜{next_year+1}年の祭り',
                    description=f'{next_year}年の小説祭り',
                    maturi_start_date=(timezone.now() + timezone.timedelta(days=365)).date(),
                    maturi_end_date=(timezone.now() + timezone.timedelta(days=395)).date(),
                    entry_start_date=(timezone.now() + timezone.timedelta(days=366)).date(),
                    entry_end_date=(timezone.now() + timezone.timedelta(days=368)).date(),
                    start_date=(timezone.now() + timezone.timedelta(days=369)).date(),
                    end_date=(timezone.now() + timezone.timedelta(days=370)).date(),
                    prediction_start_date=(timezone.now() + timezone.timedelta(days=371)).date(),
                    prediction_end_date=(timezone.now() + timezone.timedelta(days=373)).date(),
                    novel_publish_start_date=timezone.now() + timezone.timedelta(days=371),
                    year=f'{next_year}年〜{next_year+1}年の祭り'
                )

                # 語句を作成して各祭りに追加
                for word in words:
                    phrase, _ = Phrase.objects.get_or_create(text=word)
                    past_maturi.phrases.add(phrase)
                    future_maturi.phrases.add(phrase)

                # 1年前の祭りのデータ作成（公開処理を変更）
                novel_number = 1
                for letter, novel_count in writer_novels.items():
                    writer = writers[letter]
                    past_maturi.entrants.add(writer)
                    future_maturi.entrants.add(writer)
                    
                    for i in range(novel_count):
                        selected_words = random.sample(words, random.randint(5, 7))
                        content = f'祭り小説の内容です。作者は{writer.nickname}、作品番号は{novel_number}です。\n\n'
                        content += f'使用した語句: {", ".join(selected_words)}\n\n'
                        content += '本文:\n'
                        for word in selected_words:
                            content += f'{word}が輝く夜空の下、祭りの雰囲気が漂っていました。\n'
                            content += f'{word}にまつわる思い出が、この物語の中心となります。\n'

                        # 1年前の祭り用の小説（予約公開状態で作成）
                        past_novel = Novel.objects.create(
                            title=f'過去の祭り小説{novel_number}',
                            content=content,
                            author=maturi_writer,  # 最初は祭り作家
                            original_author=writer,
                            genre='祭り',
                            status='scheduled',
                            scheduled_at=past_publish_time,
                            published_date=None
                        )
                        past_maturi.maturi_novels.add(past_novel)

                        # 1年後の祭り用の小説（未公開）
                        future_novel = Novel.objects.create(
                            title=f'未来の祭り小説{novel_number}',
                            content=content,
                            author=maturi_writer,
                            original_author=writer,
                            genre='祭り',
                            status='draft'  # 下書き状態
                        )
                        future_maturi.maturi_novels.add(future_novel)

                        novel_number += 1

                # 過去の祭りの小説を公開
                self.stdout.write("過去の祭りの小説を公開します...")
                time.sleep(1)  # 1秒待機

                # 過去の祭りの小説を強制的に公開状態に
                for novel in past_maturi.maturi_novels.all():
                    novel.status = 'published'
                    novel.published_date = timezone.now() - timezone.timedelta(days=387)
                    novel.save()

                self.stdout.write("小説を公開しました")

                # 過去の祭りの予想とコメントを作成
                for novel in past_maturi.maturi_novels.all():
                    # 予想を作成
                    for predictor in writers.values():
                        if predictor != novel.original_author:
                            is_correct = random.random() < random.uniform(0.2, 0.8)
                            predicted_author = novel.original_author if is_correct else random.choice([
                                w for w in writers.values() 
                                if w != novel.original_author
                            ])
                            
                            GamePrediction.objects.create(
                                maturi_game=past_maturi,
                                novel=novel,
                                predictor=predictor,
                                predicted_author=predicted_author
                            )

                    # コメントを作成
                    commenters = random.sample(list(writers.values()), random.randint(1, 3))
                    for commenter in commenters:
                        if commenter != novel.original_author:
                            Comment.objects.create(
                                novel=novel,
                                content=random.choice(comment_texts),
                                author=commenter,  # 本来の投稿者名で表示
                                original_commenter=commenter,
                                is_maturi_comment=True,
                                maturi_game=past_maturi,
                                created_at=timezone.now() - timezone.timedelta(days=387)
                            )

                self.stdout.write(self.style.SUCCESS(
                    f'1年前の祭り「{past_maturi.title}」と1年後の祭り「{future_maturi.title}」を作成しました！'
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
                raise 