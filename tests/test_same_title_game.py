import logging
from django.test import TestCase
from django.contrib.auth import get_user_model
from game_same_title.models import TitleProposal, SameTitleEntry, Novel
from datetime import date
from django.urls import reverse
from django.utils import timezone
import datetime
from game_same_title.models import TitleProposal, SameTitleEntry, Novel, MonthlySameTitleInfo

User = get_user_model()

class SameTitleGameTests(TestCase):
    def setUp(self):
        self.users = {
            name: User.objects.create_user(
                email=f'{name}@example.com',
                password='testpassword',
                nickname=f'Nickname{name}'
            ) for name in ['A', 'B', 'C', 'D', 'E']
        }
        
        # 日付の設定
        self.last_month_start = timezone.make_aware(datetime.datetime(2024, 4, 1), timezone.get_default_timezone())
        self.current_month_start = timezone.make_aware(datetime.datetime(2024, 5, 1), timezone.get_default_timezone())
        self.next_month_start = timezone.make_aware(datetime.datetime(2024, 6, 1), timezone.get_default_timezone())
        self.two_months_later_start = timezone.make_aware(datetime.datetime(2024, 7, 1), timezone.get_default_timezone())

        titles = ['Title1', 'Title2', 'Title3']
        for user in ['A', 'B', 'C', 'D']:
            for title in titles:
                TitleProposal.objects.create(proposer=self.users[user], title=title, proposed_at=self.current_month_start)
        
        # エントリーの作成
        for user in ['B', 'C', 'D', 'E']:
            SameTitleEntry.objects.create(user=self.users[user], month=self.last_month_start)

    def test_novel_creation_and_publication(self):
        # 各テストシナリオをここに実装
        ...

    def test_novel_not_in_options_for_proposer(self):
        self.client.login(username='D@example.com', password='testpassword')
        response = self.client.get(reverse('game_same_title:post_or_edit_same_title'))
        self.assertNotIn('Title1', response.content.decode())
        logging.info("test_novel_not_in_options_for_proposer: Passed")

    def test_novel_save_and_fail_to_publish(self):
        # 別のユーザーが同じタイトルでエントリーを作成
        other_user = self.users['B']
        novel_for_other_user = Novel.objects.create(title='Title2', author=other_user, content='Other content', status='draft')
        MonthlySameTitleInfo.objects.create(
            title='Title2',
            author=other_user,
            proposer=other_user,
            published_date=timezone.now(),
            month=self.current_month_start.strftime('%Y-%m'),
            novel=novel_for_other_user
        )

        # ユーザーCでログインしてテスト
        self.client.login(username='C@example.com', password='testpassword')
        novel_id = Novel.objects.create(title='Title2', author=self.users['C'], content='Sample content', status='draft').id
        response = self.client.post(reverse('game_same_title:post_or_edit_same_title_with_id', args=[novel_id]), {
            'title': 'Title2', 
            'status': 'publish'
        })
        self.assertIn('今月の同タイトルは既に決定されています。', response.content.decode())

    def test_novel_publish_without_same_title(self):
        self.client.login(username='C@example.com', password='testpassword')
        response = self.client.post(reverse('game_same_title:post_or_edit_same_title'), {'title': 'Title2', 'is_same_title_game': False})
        # レスポンスから小説のジャンルを取得して確認する
        novel = Novel.objects.get(title='Title2')
        self.assertEqual(novel.genre, '同タイトル崩れ', "ジャンルが「同タイトル崩れ」に設定されていません。")

    def test_novel_creation_denied_without_entry(self):
        self.client.login(username='A@example.com', password='testpassword')
        response = self.client.get(reverse('game_same_title:post_or_edit_same_title'))
        self.assertEqual(response.status_code, 403)

    def test_novel_publication_denied_after_period(self):
        self.client.login(username='E@example.com', password='testpassword')
        response = self.client.post(reverse('game_same_title:post_or_edit_same_title'), {
            'title': 'Title1', 
            'content': 'Sample content for July', 
            'status': 'draft', 
            'created_at': self.two_months_later_start
        })
        response = self.client.post(reverse('game_same_title:post_or_edit_same_title'), {'title': 'Title1'})
        self.assertIn('期間外であるために失敗しました。', response.content.decode())