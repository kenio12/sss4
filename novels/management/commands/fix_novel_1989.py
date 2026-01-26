from django.core.management.base import BaseCommand
from novels.models import Novel


class Command(BaseCommand):
    help = 'Fix novel 1989 - fix self-reference from 童 to 私'

    def handle(self, *args, **options):
        novel = Novel.objects.get(id=1989)
        content = novel.content

        # Fix: when 16-year-old Sara talks about herself, she should say 私 not 童
        old = '「穀物倉に隠れていた……童を……」'
        new = '「穀物倉に隠れていた……私を……」'

        if old in content:
            content = content.replace(old, new)
            novel.content = content
            novel.save()
            self.stdout.write(self.style.SUCCESS('Fixed: 童 -> 私 (self-reference)'))
        else:
            self.stdout.write(self.style.WARNING('Text not found'))
            # Debug
            idx = content.find('穀物倉に隠れていた')
            if idx >= 0:
                self.stdout.write(f'Found at {idx}:')
                self.stdout.write(repr(content[idx:idx+50]))
