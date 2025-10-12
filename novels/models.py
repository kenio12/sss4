from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

# ジャンルの選択肢（同タイトル・祭りはeventに移動）
GENRE_CHOICES = [
    ('恋愛', '恋愛'),
    ('SF', 'SF'),
    ('ミステリー', 'ミステリー'),
    ('ホラー', 'ホラー'),
    ('ファンタジー', 'ファンタジー'),
    ('その他', 'その他'),
]

# ジャンルごとの色と文字色を定義
GENRE_STYLES = {
    '恋愛': {'bg': '#FF69B4', 'text': 'white'},  # ホットピンク
    'SF': {'bg': '#4169E1', 'text': 'white'},  # ロイヤルブルー
    'ミステリー': {'bg': '#483D8B', 'text': 'white'},  # ダークスレートブルー
    'ホラー': {'bg': '#8B0000', 'text': 'white'},  # ダークレッド
    'ファンタジー': {'bg': '#9370DB', 'text': 'white'},  # ミディアムパープル
    'その他': {'bg': '#A9A9A9', 'text': 'white'},  # ダークグレー
}

class Novel(models.Model):
    title = models.CharField(max_length=100)
    initial = models.CharField(max_length=1, blank=True, null=True)  # 頭文字を保存
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='novels')
    published_date = models.DateTimeField(null=True, blank=True)  # 公開時に設定

    # 新しいフィールドを追加
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日
    updated_at = models.DateTimeField(auto_now=True)  # 編集日

    STATUS_CHOICES = [
        ('draft', '作成中'),
        ('scheduled', '予約公開'),
        ('published', '公開'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    genre = models.CharField(max_length=100, choices=GENRE_CHOICES, default='その他')

    # イベントフィールド（新規追加）
    EVENT_CHOICES = [
        ('同タイトル', '同タイトル'),
        ('祭り', '祭り'),
    ]
    event = models.CharField(max_length=50, choices=EVENT_CHOICES, blank=True, null=True)

    word_count = models.IntegerField(default=0, editable=False)  # 文字数（自動計算）
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Like', related_name='liked_novels')
    is_same_title_game = models.BooleanField(default=False)  # 既存フィールド保持
    same_title_event_month = models.CharField(max_length=7, blank=True, null=True)
    afterword = models.TextField(blank=True, null=True)  # 後書きフィールド

    # sssのデータ注入時、一時的にコメントアウトしていた
    original_author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='original_novels'
    )

    scheduled_at = models.DateTimeField(null=True, blank=True)  # 予約公開日時

    @property
    def color_index(self):
        """
        小説IDに基づいて0-9の色インデックスを返す
        """
        return self.id % 10 if self.id else 0

    @property
    def likes_count(self):
        """いいね数を返す"""
        return self.likes.count()

    @property
    def comments_count(self):
        """コメント数を返す"""
        return self.comments.count()

    def save(self, *args, **kwargs):
        # 文字数をcontentの長さに設定
        self.word_count = len(self.content)

        # 現在時刻を取得
        now = timezone.now()

        # 予約公開の処理
        if self.status == 'scheduled' and self.scheduled_at:
            if now >= self.scheduled_at:  # 現在時刻が予約時刻以降の場合のみ公開
                self.status = 'published'
                self.published_date = now

        # 公開時にpublished_dateを設定（未設定の場合のみ）
        if self.status == 'published' and not self.published_date:
            self.published_date = now

        # 同タイトルゲーム（イベント）の処理（既存フラグを維持しつつeventフィールドも設定）
        if self.is_same_title_game:
            self.event = '同タイトル'  # eventフィールドに設定

            # 公開時にsame_title_event_monthを設定（未設定の場合のみ）
            if self.status == 'published' and not self.same_title_event_month:
                self.same_title_event_month = now.strftime('%Y-%m')

            # 新規作成時のみ月を設定（既存の月は変更しない）
            if not self.pk and not self.same_title_event_month:
                self.same_title_event_month = timezone.now().strftime('%Y-%m')

        super(Novel, self).save(*args, **kwargs)

    def __str__(self):
        return self.title  # ここを追加

    def is_visible_to(self, user=None):
        """
        小説が指定されたユーザーに見えるかどうかを判定するメソッド
        """
        # 公開済みなら誰でも見える
        if self.status == 'published':
            return True

        # 未ログインユーザーには下書きと予約公開は見えない
        if not user or not user.is_authenticated:
            return False

        # 作者本人、オリジナルの作者、または管理者なら見える
        if user == self.author or (hasattr(self, 'original_author') and user == self.original_author) or user.is_staff:
            return True

        # それ以外のユーザーには下書きと予約公開は見えない
        return False

    def get_genre_style(self):
        """ジャンルに応じた背景色と文字色を返すメソッド"""
        return GENRE_STYLES.get(self.genre, {'bg': '#A9A9A9', 'text': 'white'})

class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'novel'], name='unique_like_per_user')
        ]

class Comment(models.Model):
    novel = models.ForeignKey('Novel', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='comments')
    original_commenter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='original_comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_maturi_comment = models.BooleanField(default=False)
    maturi_game = models.ForeignKey(
        'game_maturi.MaturiGame',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comments'
    )

    def __str__(self):
        return self.content[:20]

    def save(self, *args, **kwargs):
        if not self.pk:  # 新規作成時のみ
            # 祭りイベントの小説の場合
            if self.novel.event == '祭り':
                # 実際の作者（original_author）とコメント投稿者を比較して既読フラグを設定
                if self.author == self.novel.original_author:
                    self.is_read = True
                else:
                    self.is_read = False

                # 小説に関連する祭りゲームを取得
                maturi_game = self.novel.maturi_games.first()
                if maturi_game:
                    now = timezone.now().date()
                    # 予想期間終了日までは祭り作家として投稿
                    if now <= maturi_game.prediction_end_date:
                        User = get_user_model()
                        try:
                            maturi_writer = User.objects.get(email='maturi@example.com')
                            self.original_commenter = self.author  # 元の投稿者を保存
                            self.author = maturi_writer  # 祭り作家に切り替え
                        except User.DoesNotExist:
                            logger.error("祭り作家のユーザーが見つかりません")
            # 通常の小説の場合
            else:
                if self.author == self.novel.author:
                    self.is_read = True
                else:
                    self.is_read = False

        super().save(*args, **kwargs)
