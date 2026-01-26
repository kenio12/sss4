from django.core.management.base import BaseCommand
from novels.models import Novel


class Command(BaseCommand):
    help = 'Fix novel 1989 inconsistency'

    def handle(self, *args, **options):
        novel = Novel.objects.get(id=1989)

        # Fix chapter 3 opening - add transition after Condor left
        old_text = '女は、その闇を、いつまでも見つめていた。\r\n\r\n---\r\n\r\n## 三\r\n\r\n旅一座での暮らしは、甘くなかった。'

        new_text = '女は、その闇を、いつまでも見つめていた。\r\n\r\n---\r\n\r\n## 三\r\n\r\nコンドルが去った翌朝、女は老婆に連れられて一座の者たちに紹介された。\r\n\r\n誰も女に同情の目を向けなかった。一座の者たちは皆、それぞれの過去を背負っていた。今更、焼け出された孤児が一人増えたところで、驚くには値しなかった。\r\n\r\n「働けるかい」\r\n\r\n老婆が問うた。\r\n\r\n「働きます」\r\n\r\n女は答えた。それ以外に、答えようがなかった。\r\n\r\n旅一座での暮らしは、甘くなかった。'

        if old_text in novel.content:
            novel.content = novel.content.replace(old_text, new_text)
            novel.save()
            self.stdout.write(self.style.SUCCESS('Chapter 3 opening fixed!'))
        else:
            self.stdout.write(self.style.ERROR('Text not found'))
            idx = novel.content.find('## 三')
            if idx >= 0:
                self.stdout.write(f'Found "## 三" at index: {idx}')
                self.stdout.write('===ACTUAL TEXT===')
                self.stdout.write(repr(novel.content[idx-100:idx+200]))
