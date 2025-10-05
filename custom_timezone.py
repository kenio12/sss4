# 例えば、プロジェクトのルートディレクトリに custom_timezone.py というファイルを作成する

from django.utils import timezone as django_timezone

class CustomTimezone:
    def __getattr__(self, name):
        if name == 'now':
            return self.custom_now
        return getattr(django_timezone, name)

    @staticmethod
    def custom_now():
        return django_timezone.localtime(django_timezone.now())

custom_timezone = CustomTimezone()

