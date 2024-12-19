from django.test import TestCase, Client
from django.urls import reverse
from novels.models import Novel, Comment, Like
from accounts.models import User
from django.utils import timezone
import random

class CommentNotificationTest(TestCase):
    def setUp(self):
        # 1. テストユーザーの作成
        self.client = Client()
        
        # 小説投稿ユーザー8人を作成
        self.authors = []
        for i in range(8):
            author = User.objects.create_user(
                username=f'author{i+1}',
                password='testpass123',
                nickname=f'作者{i+1}'
            )
            self.authors.append(author)
        
        # イイねするユーザー10人を作成
        self.like_users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'like_user{i+1}',
                password='testpass123',
                nickname=f'いいね{i+1}'
            )
            self.like_users.append(user)
        
        # コメントするユーザー211人を作成
        self.comment_users = []
        for i in range(211):
            user = User.objects.create_user(
                username=f'comment_user{i+1}',
                password='testpass123',
                nickname=f'コメント{i+1}'
            )
            self.comment_users.append(user)

    def test_full_comment_scenario(self):
        # 2. 小説を23件作成
        novels = []
        novel_counts = [4, 2, 5, 3, 2, 3, 2, 2]  # 各作者の小説数
        
        for author_idx, count in enumerate(novel_counts):
            for i in range(count):
                novel = Novel.objects.create(
                    title=f'小説{len(novels)+1}',
                    content='テスト本文',
                    author=self.authors[author_idx],
                    status='published',
                    published_date=timezone.now()
                )
                novels.append(novel)

        # 3. 最初の小説に10個のイイねをつける
        first_novel = novels[0]
        for like_user in self.like_users:
            Like.objects.create(
                novel=first_novel,
                user=like_user
            )

        # イイね数の確認
        self.assertEqual(Like.objects.filter(novel=first_novel).count(), 10)

        # 4. 322件のコメントを投稿
        comments_count = 0
        while comments_count < 322:
            novel = random.choice(novels)
            user = random.choice(self.comment_users)
            Comment.objects.create(
                novel=novel,
                author=user,
                content=f'テストコメント{comments_count+1}',
                is_read=False
            )
            comments_count += 1

        # 5. 各作者でログインしてテスト
        for author in self.authors:
            self.client.login(username=author.username, password='testpass123')
            
            # 未読コメント数を確認
            response = self.client.get(reverse('novels:get_unread_comments_count'))
            author_unread_count = response.json()['unread_count']
            
            # コメントを1つずつ既読化
            author_comments = Comment.objects.filter(
                novel__author=author,
                is_read=False
            ).exclude(author=author)
            
            for comment in author_comments:
                response = self.client.post(
                    reverse('novels:toggle_comment_read_status'),
                    {'comment_id': comment.id},
                    content_type='application/json'
                )
                
                # 既読化後の未読カウント確認
                new_count = response.json()['unread_count']
                self.assertEqual(new_count, author_unread_count - 1)
                author_unread_count = new_count

            # すべて既読後は0になっているか確認
            response = self.client.get(reverse('novels:get_unread_comments_count'))
            self.assertEqual(response.json()['unread_count'], 0)

            self.client.logout() 