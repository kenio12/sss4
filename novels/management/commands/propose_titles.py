import os
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
from game_same_title.models import TitleProposal
from dateutil.relativedelta import relativedelta

class Command(BaseCommand):
    help = 'Propose three random titles from a list'

    def handle(self, *args, **options):
        # 環境変数からユーザー情報を取得
        email = os.environ.get('AI_USER_EMAIL')
        password = os.environ.get('AI_USER_PASSWORD')
        nickname = os.environ.get('AI_USER_NICKNAME')

        # AIユーザーを取得、存在しなければ作成
        User = get_user_model()
        ai_user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email.split('@')[0], 'nickname': nickname}
        )
        if created:
            ai_user.set_password(password)
            ai_user.save()

        # タイトルリストをファイルから読み込んでランダムにシャッフル
        with open('sample_same_titles.txt', 'r') as file:
            all_titles = file.read().splitlines()
        random.shuffle(all_titles)  # タイトルリストをランダムにシャッフル

        # 既に提案されたタイトルを取得してフィルタリング
        proposed_titles = set(TitleProposal.objects.values_list('title', flat=True))
        titles = [title for title in all_titles if title not in proposed_titles]

        proposed_at = datetime(2024, 3, 1, tzinfo=timezone.utc)
        proposal_month = datetime(2024, 3, 1, tzinfo=timezone.utc)

        for _ in range(100 * 12):  # 12ヶ月分の提案を行う
            if len(titles) < 3:  # タイトルが足りなくなったらリセット
                titles = all_titles.copy()

            selected_titles = random.sample(titles, 3)
            for title in selected_titles:
                TitleProposal.objects.create(
                    title=title,
                    proposer=ai_user,
                    proposed_at=proposed_at,
                    proposal_month=proposal_month
                )
                titles.remove(title)  # 選択したタイトルをリストから削除

            # 提案日と提案月を次の月に更新
            proposed_at += relativedelta(months=1)
            proposal_month += relativedelta(months=1)

            if proposed_at.month > 12:
                proposed_at += relativedelta(years=1, months=-12)
                proposal_month += relativedelta(years=1, months=-12)