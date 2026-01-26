from django.core.management.base import BaseCommand
from novels.models import Novel


class Command(BaseCommand):
    help = 'Fix novel 1989 - fix incorrect 童 in chapters 4+ (age 16+)'

    def handle(self, *args, **options):
        novel = Novel.objects.get(id=1989)
        content = novel.content
        changes = 0

        # These are occurrences in chapters 4+ where 童 should be 女
        # Chapter 4 (age 16) - Sara reunites with Condor
        fixes = [
            # Occurrence 25: 16歳のシーン
            ('月明かりが、その顔を照らした。\r\n\r\n童は息を呑んだ。\r\n\r\n九年前と同じ顔であった。',
             '月明かりが、その顔を照らした。\r\n\r\n女は息を呑んだ。\r\n\r\n九年前と同じ顔であった。'),

            # Occurrence 27: 16歳のシーン - tears
            ('その言葉を聞いた瞬間、童の目から涙が溢れた。',
             'その言葉を聞いた瞬間、女の目から涙が溢れた。'),

            # Occurrence 28: 19歳のシーン - "いえ"
            ('「いえ」\r\n\r\n童は答えた。だが、体は正直であった。',
             '「いえ」\r\n\r\n女は答えた。だが、体は正直であった。'),

            # Occurrence 29: 19歳のシーン - coat on shoulder
            ('コンドルは外套を脱いで、童の肩にかけた。',
             'コンドルは外套を脱いで、女の肩にかけた。'),

            # Occurrence 30: 19歳のシーン - gasp
            ('胸から、全身へ。\r\n\r\n童は息を呑んだ。頬が熱くなった。',
             '胸から、全身へ。\r\n\r\n女は息を呑んだ。頬が熱くなった。'),
        ]

        for old, new in fixes:
            if old in content:
                content = content.replace(old, new)
                changes += 1
                self.stdout.write(f'Fixed: {old[:40]}...')
            else:
                self.stdout.write(self.style.WARNING(f'Not found: {old[:40]}...'))

        if changes > 0:
            novel.content = content
            novel.save()
            self.stdout.write(self.style.SUCCESS(f'\nFixed {changes} occurrences!'))
        else:
            self.stdout.write(self.style.WARNING('\nNo changes made'))
