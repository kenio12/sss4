from django.core.management.base import BaseCommand
from novels.models import Novel


class Command(BaseCommand):
    help = 'Fix novel 1989 - add troupe challenge scene'

    def handle(self, *args, **options):
        novel = Novel.objects.get(id=1989)
        content = novel.content

        old_text = '童は答えた。それ以外に、答えようがなかった。\r\n\r\n旅一座での暮らしは、甘くなかった。'

        new_text = '''童は答えた。それ以外に、答えようがなかった。

老婆は厳しい目で童を見た。

「芸を持たぬ者は、この一座では生きていけぬ。いくらあの男に頼まれたとて、役立たずを養う余裕などない」

童は黙って聞いていた。

「お前に何ができる。踊れるか。歌えるか。曲芸ができるか」

童は首を横に振った。

「ならば、覚えるのだ。さもなくば、次の街で置いていく」

老婆の言葉に、嘘はなかった。

旅一座での暮らしは、甘くなかった。'''

        # Convert to \r\n
        new_text = new_text.replace('\n', '\r\n')

        if old_text in content:
            content = content.replace(old_text, new_text)
            novel.content = content
            novel.save()
            self.stdout.write(self.style.SUCCESS('Added troupe challenge scene!'))
        else:
            self.stdout.write(self.style.WARNING('Text not found'))
            idx = content.find('童は答えた。それ以外に')
            if idx >= 0:
                self.stdout.write(f'Found at: {idx}')
                self.stdout.write(repr(content[idx:idx+200]))
