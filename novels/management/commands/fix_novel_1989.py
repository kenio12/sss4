from django.core.management.base import BaseCommand
from novels.models import Novel


class Command(BaseCommand):
    help = 'Fix novel 1989 - full review and fix age-appropriate terms'

    def handle(self, *args, **options):
        novel = Novel.objects.get(id=1989)
        content = novel.content

        # Find all occurrences of 童 and show context
        self.stdout.write('=== Searching for 童 in the novel ===')

        idx = 0
        count = 0
        while True:
            idx = content.find('童', idx)
            if idx == -1:
                break
            count += 1
            # Get context (100 chars before and after)
            start = max(0, idx - 80)
            end = min(len(content), idx + 80)
            context = content[start:end].replace('\r\n', ' ')
            self.stdout.write(f'\n--- Occurrence {count} at position {idx} ---')
            self.stdout.write(context)
            idx += 1

        self.stdout.write(f'\n\nTotal: {count} occurrences of 童')
