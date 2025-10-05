from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from game_same_title.models import SameTitleEntry, TitleProposal
from novels.models import Novel

class Command(BaseCommand):
    help = 'Initializes the database with test data, including a superuser and title proposals.'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        # スーパーユーザーを作成または取得
        user1, created = User.objects.get_or_create(
            email='keikeikun@icloud.com',
            defaults={'nickname': 'けにを', 'username': 'keikeikun@icloud.com'}
        )
        if created:
            user1.set_password('Keniosan2')
            user1.is_superuser = True
            user1.is_staff = True
            user1.save()

        user2, created = User.objects.get_or_create(
            email='keikeikun24@yahoo.co.jp',
            defaults={'nickname': 'やふーけにお', 'username': 'keikeikun24@yahoo.co.jp'}
        )
        if created:
            user2.set_password('Keniosan2')
            user2.save()

        user3, created = User.objects.get_or_create(
            email='keikeikun3@gmail.com',
            defaults={'nickname': 'けにお王３', 'username': 'keikeikun3@gmail.com'}
        )
        if created:
            user3.set_password('Keniosan2')
            user3.save()

        # 4月のエントリー
        SameTitleEntry.objects.get_or_create(user=user1, month=timezone.datetime(2024, 4, 1))
        SameTitleEntry.objects.get_or_create(user=user2, month=timezone.datetime(2024, 4, 1))
        SameTitleEntry.objects.get_or_create(user=user3, month=timezone.datetime(2024, 4, 1))

        # 5月のエントリー
        SameTitleEntry.objects.get_or_create(user=user2, month=timezone.datetime(2024, 5, 1))
        SameTitleEntry.objects.get_or_create(user=user3, month=timezone.datetime(2024, 5, 1))

        # 4月のタイトル提案
        titles_april_user1 = ['サル', 'ゴリラ', 'キリン']
        titles_april_user2 = ['餃子', '焼き飯', '麻婆茄子']
        titles_april_user3 = ['アメリカ', '日本', '台湾']

        for title in titles_april_user1:
            TitleProposal.objects.get_or_create(title=f"先月の{title}", proposer=user1, proposed_at=timezone.datetime(2024, 4, 1), proposal_month=timezone.datetime(2024, 4, 1))

        for title in titles_april_user2:
            TitleProposal.objects.get_or_create(title=f"先月の{title}", proposer=user2, proposed_at=timezone.datetime(2024, 4, 1), proposal_month=timezone.datetime(2024, 4, 1))

        for title in titles_april_user3:
            TitleProposal.objects.get_or_create(title=f"先月の{title}", proposer=user3, proposed_at=timezone.datetime(2024, 4, 1), proposal_month=timezone.datetime(2024, 4, 1))

        # 5月のタイトル提案
        titles_may_user2 = ['餃子', '焼き飯', '麻婆茄子']
        titles_may_user3 = ['ぶらんこ', 'すべり台', 'シーソー']

        for title in titles_may_user2:
            TitleProposal.objects.get_or_create(title=title, proposer=user2, proposed_at=timezone.datetime(2024, 5, 1), proposal_month=timezone.datetime(2024, 5, 1))

        for title in titles_may_user3:
            TitleProposal.objects.get_or_create(title=title, proposer=user3, proposed_at=timezone.datetime(2024, 5, 1), proposal_month=timezone.datetime(2024, 5, 1))

        self.stdout.write(self.style.SUCCESS('Database initialization complete.'))