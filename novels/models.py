from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

# ジャンルの選択肢
GENRE_CHOICES = [
    ('レジェンド小説', 'レジェンド小説'),
    ('初めましての挨拶', '初めましての挨拶'),
    ('ジョーク', 'ジョーク'),
    ('シリーズ', 'シリーズ'),
    ('サスペンス', 'サスペンス'),
    ('ファンタジー', 'ファンタジー'),
    ('同タイトル', '同タイトル'),
    ('恋愛', '恋愛'),
    ('日常', '日常'),
    ('祭り', '祭り'),
    ('雑談', '雑談'),
    ('ミステリー', 'ミステリー'),
    ('ノンフィクション', 'ノンフィクション'),
    ('ホラー', 'ホラー'),
    ('時代', '時代'),
    ('未分類', '未分類'),
    ('バトル', 'バトル'),
    ('大会', '大会'),
    ('コメディ', 'コメディ'),
    ('オフ会', 'オフ会'),
    ('歴史', '歴史'),
    ('私小説', '私小説'),
    ('官能', '官能'),
    ('三題噺', '三題噺'),
    ('旧祭���', '旧祭り'),
    ('旧同タイトル', '旧同タイトル'),
]

# ジャンルごとの色と文字色を定義
GENRE_STYLES = {
    'レジェンド小説': {'bg': '#FF4500', 'text': 'white'},  # オレンジレッド
    '初めましての挨拶': {'bg': '#20B2AA', 'text': 'white'},  # ライトシーグリーン
    'ジョーク': {'bg': '#FFD700', 'text': 'black'},  # ゴールド
    'シリーズ': {'bg': '#4169E1', 'text': 'white'},  # ロイヤルブルー
    'サスペンス': {'bg': '#800000', 'text': 'white'},  # マルーン
    'ファンタジー': {'bg': '#9370DB', 'text': 'white'},  # ミディアムパープル
    '同タイトル': {'bg': '#2E8B57', 'text': 'white'},  # シーグリーン
    '恋愛': {'bg': '#FF69B4', 'text': 'white'},  # ホットピンク
    '日常': {'bg': '#3CB371', 'text': 'white'},  # ミディアムシーグリーン
    '祭り': {'bg': '#FF8C00', 'text': 'black'},  # ダークオレンジ
    '雑談': {'bg': '#808080', 'text': 'white'},  # グレー
    'ミステリー': {'bg': '#483D8B', 'text': 'white'},  # ダークスレートブルー
    'ノンフィクション': {'bg': '#556B2F', 'text': 'white'},  # ダークオリーブグリーン
    'ホラー': {'bg': '#8B0000', 'text': 'white'},  # ダークレッド
    '時代': {'bg': '#8B4513', 'text': 'white'},  # サドブラウン
    '未分類': {'bg': '#A9A9A9', 'text': 'white'},  # ダークグレー
    'バトル': {'bg': '#B22222', 'text': 'white'},  # ファイアーブリック
    '大会': {'bg': '#DAA520', 'text': 'black'},  # ゴールデンロッド
    'コメディ': {'bg': '#FF69B4', 'text': 'white'},  # ホットピンク
    'オフ会': {'bg': '#32CD32', 'text': 'black'},  # ライムグリーン
    '歴史': {'bg': '#CD853F', 'text': 'white'},  # ペルー
    '私小説': {'bg': '#9932CC', 'text': 'white'},  # ダークオーキッド
    '官能': {'bg': '#DC143C', 'text': 'white'},  # クリムゾン
    '三題噺': {'bg': '#6B8E23', 'text': 'white'},  # オリーブドラブ
    '旧祭り': {'bg': '#FFA500', 'text': 'black'},  # オレンジ
    '旧同タイトル': {'bg': '#228B22', 'text': 'white'},  # フォレストグリーン
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
    genre = models.CharField(max_length=100, choices=GENRE_CHOICES, default='未分類')
    word_count = models.IntegerField(default=0, editable=False)  # 文字数（自動計算）
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Like', related_name='liked_novels')
    is_same_title_game = models.BooleanField(default=False)
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
        小説IDに基づいて0-9の色イン���ックスを返す
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
        
        # 同タイトルゲームの処理（既存のコード）
        if self.is_same_title_game and self.status == 'published' and not self.same_title_event_month:
            self.same_title_event_month = now.strftime('%Y-%m')
            
        if self.is_same_title_game:
            self.genre = '同タイトル'  # 同タイトルゲームの場合は必ずジャンルを設定
            
            # 新規作成時のみ月を設定（既存の月は変更しない）
            if not self.pk and not self.same_title_event_month:  # 新規作成時のみ
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
            # 祭りの小説の場合
            if self.novel.genre == '祭り':
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
