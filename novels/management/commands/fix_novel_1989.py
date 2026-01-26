from django.core.management.base import BaseCommand
from novels.models import Novel


class Command(BaseCommand):
    help = 'Fix novel 1989 - change "女" to "童/幼子" in early chapters'

    def handle(self, *args, **options):
        novel = Novel.objects.get(id=1989)

        # Show first part of novel for analysis
        idx = novel.content.find('## 一')
        if idx >= 0:
            self.stdout.write('===CHAPTER 1 START===')
            self.stdout.write(novel.content[idx:idx+2000])
