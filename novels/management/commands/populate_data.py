from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from novels.models import Novel, Comment, Like
from accounts.models import Profile
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Populates the database with sample data'

    def handle(self, *args, **options):
        User = get_user_model()

        # 既存のデータを全て消去
        User.objects.all().delete()
        Novel.objects.all().delete()
        Comment.objects.all().delete()
        Like.objects.all().delete()

        # 20人のユーザーを作成し、それぞれにプロフィールを設定
        for i in range(1, 21):
            user = User.objects.create_user(email=f"user{i}@example.com", password="password123", nickname=f"ユーザー{i}")
            Profile.objects.create(user=user, age=random.randint(18, 60), gender=random.choice(['M', 'F']), hobby="読書", likes_matcha=random.choice([True, False]))

        genres = ["ファンタジー", "恋愛小説", "サスペンス"]  # ジャンルのリスト

        # 公開小説70件、非公開小説30件を作成
        for i in range(1, 101):
            status = "published" if i <= 70 else "draft"
            genre = random.choice(genres)  # ジャンルをランダムに選択
            novel = Novel.objects.create(
                title=f"小説{i}",
                content=f"これは小説{i}の内容です。",
                author=random.choice(User.objects.all()),
                status=status,
                genre=genre,  # 修正: ジャンルをランダムに設定
                published_date=timezone.now()
            )

            # 公開小説に対して、それぞれ10件のコメントと15件の「いいね」を追加
            if novel.status == "published":
                for j in range(10):
                    Comment.objects.create(
                        novel=novel,
                        author=random.choice(User.objects.all()),
                        content=f"コメント{j}：面白いですね！",
                        created_at=timezone.now()
                    )
                for k in range(15):
                    Like.objects.create(
                        user=random.choice(User.objects.all()),
                        novel=novel
                    )

        self.stdout.write(self.style.SUCCESS('データの流し込みが完了しました。'))