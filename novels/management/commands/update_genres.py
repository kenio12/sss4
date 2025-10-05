from django.core.management.base import BaseCommand
from novels.models import Novel

class Command(BaseCommand):
    def handle(self, *args, **options):
        m = Novel.objects.filter(genre='祭り').update(genre='旧祭り')
        s = Novel.objects.filter(genre='同タイトル').update(genre='旧同タイトル')
        self.stdout.write(f'祭り:{m}件, 同タイトル:{s}件 を変更しました')
