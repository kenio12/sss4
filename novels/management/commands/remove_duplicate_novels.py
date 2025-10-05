from django.core.management.base import BaseCommand
from django.db.models import Count
from novels.models import Novel

class Command(BaseCommand):
    help = '重複した小説を削除し、一つだけを残す'

    def handle(self, *args, **kwargs):
        # タイトル、投稿日、著者が同じ小説をグループ化し、カウントする
        duplicates = Novel.objects.values('title', 'published_date', 'author_id').annotate(count=Count('id')).filter(count__gt=1)

        for item in duplicates:
            # 同じタイトル、投稿日、著者の小説を取得
            novels = Novel.objects.filter(title=item['title'], published_date=item['published_date'], author_id=item['author_id'])
            # 最初の1つを除いて残りを削除
            first_novel = novels.first()
            novels_to_delete = novels.exclude(id=first_novel.id)
            count_deleted = novels_to_delete.delete()[0]  # delete() returns a tuple (num_deleted, details)

            self.stdout.write(self.style.SUCCESS(f'Removed {count_deleted} duplicates of "{item["title"]}".'))