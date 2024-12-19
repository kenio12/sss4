from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time
from .models import TitleProposal, SameTitleEntry
from dateutil.relativedelta import relativedelta
from django.contrib.messages import get_messages

User = get_user_model()

class EntryFlowTest(TestCase):
    def setUp(self):
        # テスト用のユーザーを作成
        self.user1 = User.objects.create_user(email='user1@example.com', password='password123', nickname='nickname1')
        self.user2 = User.objects.create_user(email='user2@example.com', password='password123', nickname='nickname2')

    def test_entry_flow(self):
        self.client.login(username='user1@example.com', password='password123')
        response = self.client.post('/game_same_title/entry/', follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.message == "エントリーが完了しました。" for msg in messages))
        self.assertTrue(SameTitleEntry.objects.filter(user=self.user1, month=timezone.now().date().replace(day=1)).exists())

        # 1ヶ月後にuser1が再度ログインしてエントリー
        with freeze_time(timezone.now() + relativedelta(months=+1)):
            SameTitleEntry.objects.all().delete()  # 1ヶ月後をシミュレートするためにエントリーをクリア
            self.client.login(username='user1@example.com', password='password123')
            response = self.client.post('/game_same_title/entry/', follow=True)
            next_month = timezone.now().date().replace(day=1)
            self.assertTrue(SameTitleEntry.objects.filter(user=self.user1, month=next_month).exists())

        # user2がログインしてエントリー
        self.client.login(username='user2@example.com', password='password123')
        response = self.client.post('/game_same_title/entry/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('エントリーが完了しました。' in response.content.decode())
        self.assertTrue(SameTitleEntry.objects.filter(user=self.user2, month=timezone.now().date().replace(day=1)).exists())

    def tearDown(self):
        # テスト用のデータをクリア
        self.user1.delete()
        self.user2.delete()
        SameTitleEntry.objects.all().delete()