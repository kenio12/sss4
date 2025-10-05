# novels/management/commands/update_word_counts.py
from django.core.management.base import BaseCommand
from novels.models import Novel

class Command(BaseCommand):
    help = 'Updates the word count for all novels'

    def handle(self, *args, **kwargs):
        novels = Novel.objects.all()
        for novel in novels:
            novel.word_count = len(novel.content)
            novel.save()
            self.stdout.write(self.style.SUCCESS(f'Updated word count for "{novel.title}"'))