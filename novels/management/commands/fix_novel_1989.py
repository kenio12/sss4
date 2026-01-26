from django.core.management.base import BaseCommand
from novels.models import Novel


class Command(BaseCommand):
    help = 'Fix novel 1989 inconsistency'

    def handle(self, *args, **options):
        novel = Novel.objects.get(id=1989)

        old_text = '''「生きろ」

それだけ言って、燃える村を背に、歩き出した。

女は男の肩越しに、崩れ落ちる生家を見た。母の姿は、もう見えなかった。

---

## 二

男は、女を旅の一座に預けた。'''

        new_text = '''「生きろ」

男は女を抱いたまま、燃える村を背に歩き出した。

女は男の肩越しに、崩れ落ちる生家を見た。母の姿は、もう見えなかった。

男は、夜通し歩き続けた。女は、いつしか眠りに落ちていた。目が覚めた時には、空が白み始めていた。

---

## 二

数日後、男は女を旅の一座に預けた。'''

        if old_text in novel.content:
            novel.content = novel.content.replace(old_text, new_text)
            novel.save()
            self.stdout.write(self.style.SUCCESS('Novel 1989 fixed successfully!'))
        else:
            self.stdout.write(self.style.ERROR('Text not found in novel'))
            idx = novel.content.find('生きろ')
            if idx >= 0:
                self.stdout.write(f'Found "生きろ" at index: {idx}')
                self.stdout.write('===ACTUAL TEXT===')
                self.stdout.write(repr(novel.content[idx:idx+350]))
