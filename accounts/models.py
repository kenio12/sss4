
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import Q

class UserQuerySet(models.QuerySet):
    def search(self, query=None, likes_matcha=None):
        qs = self
        if query is not None:
            or_lookup = (Q(nickname__icontains=query) | 
                         Q(profile__residence__icontains=query) | 
                         Q(profile__hobby__icontains=query))
            qs = qs.filter(or_lookup).distinct()
        if likes_matcha is not None:
            qs = qs.filter(profile__likes_matcha=likes_matcha)
        return qs

class CustomUserManager(BaseUserManager):
    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def search(self, query=None, likes_matcha=None):
        return self.get_queryset().search(query=query, likes_matcha=likes_matcha)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        username = email  # usernameにemailの値を設定
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

# このUserクラスは、プロジェクトのカスタムユーザーモデルとして定義されています。
# AbstractUserを継承しており、追加のフィールドやメソッドを通じてカスタマイズされています。
# settings.pyのAUTH_USER_MODEL設定により、Djangoのデフォルトユーザーモデルの代わりに使用されます。
class User(AbstractUser):
    # ユーザータイプの選択肢を更新
    PAID_MEMBER = 1  # 有料作家と有料読者を統合した有料会員
    FREE_MEMBER = 2
    VISITOR = 3
    OPERATOR = 4
    JUDGE = 5
    AI = 6
    CLASSIC_WRITER = 7
    MATURI_WRITER = 8  # 祭り作家用に8番を使用
    OLD_SSS_WRITER = 9

    USER_TYPE_CHOICES = (
        (PAID_MEMBER, '有料会員'),
        (FREE_MEMBER, '無料会員'),
        (VISITOR, '訪問者'),
        (OPERATOR, '運営者'),
        (JUDGE, '審査員'),
        (AI, 'AI'),
        (CLASSIC_WRITER, '昔の作家など'),
        (MATURI_WRITER, '祭り作家'),  # 追加
        (OLD_SSS_WRITER, '旧SSS作家'),
    )

    email_confirmed = models.BooleanField(default=False)  # 新しいフィールドを追加
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=FREE_MEMBER)  # デフォルト値を無料会員に変更
    email = models.EmailField('email address', unique=True)  # メールアドレスをユニークに設定
    nickname = models.CharField(max_length=50, unique=True, null=False, blank=False)
    
    # 新しく追加する色情報フィールド
    comment_color = models.CharField(
        max_length=7,  # #FFFFFFのような形式用
        default='',
        blank=True,
        help_text='コメント表示用の色（#RRGGBB形式）'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname']  # 'username'を削除し、'nickname'を追加

    def save(self, *args, **kwargs):
        if not self.comment_color:  # 色が設定されていない場合
            colors = [
                '#FF6B6B',  # 赤っぽい
                '#4ECDC4',  # ターコイズ
                '#45B7D1',  # 水色
                '#96CEB4',  # 薄緑
                '#FFEEAD',  # クリーム
                '#D4A5A5',  # ピンク
                '#9B59B6',  # 紫
                '#3498DB',  # 青
                '#1ABC9C',  # エメラルド
                '#F1C40F'   # 黄色
            ]
            # IDがある場合はIDを10で割った余りを使用、ない場合は0を使用
            color_index = (self.id % 10) if self.id else 0
            self.comment_color = colors[color_index]
        super().save(*args, **kwargs)


class Profile(models.Model):
    
    # 再アップ後にポップアップ出すために
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_login = models.BooleanField(default=True)  # 新規フィールドを追加
    selected_writer = models.ForeignKey(User, related_name='selected_novels', on_delete=models.SET_NULL, null=True, blank=True)

    AGE_CHOICES = [
        (10, 'だいたい10歳'),
        (20, 'だいたい20歳'),
        (30, 'だいたい30歳'),
        (40, 'だいたい40歳'),
        (50, 'だいたい50歳'),
        (60, 'だいたい60歳'),
        (70, 'だいたい70歳'),
        (80, 'だいたい80歳'),
        (90, 'だいたい90歳'),
        (100, 'だいたい100歳'),
        (110, 'だいたい110歳'),
        (120, 'だいたい120歳'),
        (130, 'だいたい130歳'),
    ]
    # 性別の選択肢を追加
    GENDER_CHOICES = [
        ('M', 'たぶん男'),
        ('F', 'たぶん女'),
        ('N', '男でも女でもない何か'),
    ]
    strengths = models.CharField(max_length=100, blank=True)  # 任意
    weaknesses = models.CharField(max_length=100, blank=True)  # 任意
    age = models.PositiveSmallIntegerField(choices=AGE_CHOICES, blank=True, null=True)  # 既に任意
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)  # 既に任意
    species = models.CharField(max_length=100, default='人間かも', blank=True)  # 任意に変更
    pet_peeve = models.CharField(max_length=100, blank=True)  # 任意
    habit = models.CharField(max_length=100, blank=True)  # 任意
    residence = models.CharField(max_length=100, blank=True)  # 任意
    likes_matcha = models.BooleanField(null=True, default=None)  # nullを許容
    hobby = models.CharField(max_length=100, blank=True)  # 任意
    current_trend = models.CharField(max_length=100, blank=True)  # 任意
    favorite_songs = models.CharField(max_length=100, blank=True)  # 任意
    favorite_dance = models.CharField(max_length=100, blank=True)  # 任意
    favorite_phrase = models.CharField(max_length=100, blank=True)  # 任意
    introduction = models.TextField(blank=True, default='')  # 既に任意

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)  # first_login defaults to True

class EmailNotificationSettings(models.Model):
    """
    メール通知設定モデル
    ユーザーごとの通知設定を管理
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )

    # 同タイトルイベント関連通知
    same_title_recruitment = models.BooleanField(
        default=True,
        verbose_name='同タイトル募集通知',
        help_text='月初（1日）に送信される同タイトル募集通知'
    )
    same_title_proposal = models.BooleanField(
        default=True,
        verbose_name='同タイトル提案通知',
        help_text='タイトル提案時に送信される通知'
    )
    same_title_decision = models.BooleanField(
        default=True,
        verbose_name='同タイトル決定通知',
        help_text='月の最初の投稿時に送信される通知'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'メール通知設定'
        verbose_name_plural = 'メール通知設定'

    def __str__(self):
        return f'{self.user.nickname} の通知設定'

@receiver(post_save, sender=User)
def create_notification_settings(sender, instance, created, **kwargs):
    """ユーザー作成時に通知設定を自動作成"""
    if created:
        EmailNotificationSettings.objects.create(user=instance)

