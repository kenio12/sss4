from django.test import TestCase
from django.urls import reverse
from .models import Novel, Comment
from django.contrib.auth import get_user_model
from django.http import Http404


class NovelDetailViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='testuser@example.com', password='12345', nickname='testnickname')
        # 小説を公開状態で作成
        self.novel = Novel.objects.create(title='Test Novel', content='This is a test novel.', author=self.user, status='published')
        self.comment = Comment.objects.create(novel=self.novel, author=self.user, content='Test comment.')

    def test_novel_detail_view_status_code(self):
        # 小説の詳細ページが200ステータスコードを返すかテスト
        url = reverse('novels:novel_detail', args=(self.novel.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_novel_detail_view_with_comments(self):
        # コメントが正しく表示されるかテスト
        url = reverse('novels:novel_detail', args=(self.novel.id,))
        response = self.client.get(url)
        self.assertContains(response, 'Test comment.')

    def test_novel_detail_view_template_used(self):
        # 正しいテンプレートが使用されているかテスト
        url = reverse('novels:novel_detail', args=(self.novel.id,))
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'novels/detail.html')

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class AdminLoginTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass',
            nickname='admin'
        )

    def test_admin_login_page(self):
        # ログアウトしてからログインページにアクセスするテスト
        self.client.logout()  # ログアウトを追加
        response = self.client.get(reverse('admin:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"', html=False)

    def test_admin_login_post(self):
        # ログイン処理をテスト
        response = self.client.post(
            reverse('admin:login'),
            {'username': 'admin@example.com', 'password': 'adminpass'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.resolver_match.view_name, 'accounts:view_profile')

# このコードは管理者ログインのテストを行うためのものや。setUpでスーパーユーザーを作成し、
# test_admin_login_pageではログアウト状態からログインページにアクセスすることを確認し、
# test_admin_login_postではログイン処理が正しくリダイレクトされるかをテストしているんや。
