from django.core.management.base import BaseCommand
from novels.models import Novel


class Command(BaseCommand):
    help = 'Fix novel 1989 - fix typo 闘->闇'

    def handle(self, *args, **options):
        novel = Novel.objects.get(id=1989)
        content = novel.content

        # Fix typo: 闘 -> 闇
        old = '童は、その闘を、いつまでも見つめていた'
        new = '童は、その闇を、いつまでも見つめていた'

        if old in content:
            content = content.replace(old, new)
            novel.content = content
            novel.save()
            self.stdout.write(self.style.SUCCESS('Fixed typo: 闘 -> 闇'))
        else:
            self.stdout.write(self.style.WARNING('Text not found'))

        # Old code below for reference
        replacements_ch1 = [
            ('だが、女が最も鮮明に覚えているのは', 'だが、童が最も鮮明に覚えているのは'),
            ('その一連の動作を、女は見つめていた', 'その一連の動作を、童は見つめていた'),
            ('男は女を見下ろした', '男は童を見下ろした'),
            ('女も何も言えなかった', '童も何も言えなかった'),
            ('女の肩にかけた', '童の肩にかけた'),
            ('その言葉の意味を、女は解さなかった', 'その言葉の意味を、童は解さなかった'),
            ('男は女を抱き上げた', '男は童を抱き上げた'),
            ('その時、女の頬が男の胸に触れた', 'その時、童の頬が男の胸に触れた'),
            ('男は女を抱いたまま、燃える村を背に歩き出した', '男は童を抱いたまま、燃える村を背に歩き出した'),
            ('女は男の肩越しに', '童は男の肩越しに'),
            ('女は、いつしか眠りに落ちていた', '童は、いつしか眠りに落ちていた'),
        ]

        # Chapter 2 - still age 7
        replacements_ch2 = [
            ('数日後、男は女を旅の一座に預けた', '数日後、男は童を旅の一座に預けた'),
            ('老婆は女を見た。女は老婆を見た', '老婆は童を見た。童は老婆を見た'),
            ('老婆が問うた。女は答えられなかった', '老婆が問うた。童は答えられなかった'),
            ('その指を、女は見ていた', 'その指を、童は見ていた'),
            ('老婆は女の手を取った', '老婆は童の手を取った'),
            ('女は男の背を見つめた', '童は男の背を見つめた'),
            ('女は息を呑んだ', '童は息を呑んだ'),
            ('女の目から涙が溢れた', '童の目から涙が溢れた'),
            ('女は、その闇を、いつまでも見つめていた', '童は、その闘を、いつまでも見つめていた'),
        ]

        # Chapter 3 opening - still age 7, change to 童
        replacements_ch3 = [
            ('コンドルが去った翌朝、女は老婆に連れられて', 'コンドルが去った翌朝、童は老婆に連れられて'),
            ('誰も女に同情の目を向けなかった', '誰も童に同情の目を向けなかった'),
            ('女は答えた', '童は答えた'),
        ]

        all_replacements = replacements_ch1 + replacements_ch2 + replacements_ch3

        for old, new in all_replacements:
            if old in content:
                content = content.replace(old, new)
                changes += 1
                self.stdout.write(f'Replaced: {old[:30]}...')

        if changes > 0:
            novel.content = content
            novel.save()
            self.stdout.write(self.style.SUCCESS(f'Fixed {changes} occurrences!'))
        else:
            self.stdout.write(self.style.WARNING('No replacements made'))
