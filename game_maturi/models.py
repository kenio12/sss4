from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from collections import Counter
from django import template
from novels.models import Novel  # Novelモデルをインポート
from freezegun import freeze_time  # これを追加！


register = template.Library()

def generate_year_choices():
    start_year = 2024
    end_year = 2124
    
    # 全ての可能な年度の選択肢を生成
    choices = []
    for year in range(start_year, end_year):
        title = f'{year}年〜{year+1}年の祭り'
        choices.append((title, title))
    
    return tuple(choices)

# クラス内で使用するための定数として定義
YEAR_CHOICES = generate_year_choices()

class MaturiGame(models.Model):
    title = models.CharField(max_length=200, verbose_name="タイトル", unique=True)  # 一意性を保証
    description = models.TextField(verbose_name="説明")
    start_date = models.DateField(verbose_name="開始日")# 執筆期の開始日
    end_date = models.DateField(verbose_name="終了日")# 執筆間の終了日
    phrases = models.ManyToManyField('Phrase', blank=True, verbose_name="語句")
    prediction_start_date = models.DateField(verbose_name="作者予想の開始日")
    prediction_end_date = models.DateField(verbose_name="作者予想の終了日")
    entry_start_date = models.DateField(null=True, blank=True)
    entry_end_date = models.DateField(null=True, blank=True)
    entrants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name="エントリー参加者", related_name='entered_games')
    maturi_start_date = models.DateField(verbose_name="祭り開始日", null=True, blank=True)
    maturi_end_date = models.DateField(verbose_name="祭り終了日", null=True, blank=True)
    maturi_novels = models.ManyToManyField(
        Novel,
        blank=True,
        verbose_name="祭りの小説",
        related_name='maturi_games',
        limit_choices_to={'genre': '祭り'}  # ここを追加
    )
    dummy_author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dummy_maturi_games'
    )

    year = models.CharField(
        max_length=100,
        verbose_name='開催年度',
        editable=False  # 管理画面での編集を無効化
    )

    # 新しい追加する日程フィールド
    novel_publish_start_date = models.DateTimeField('小説公開開始日')
    
    is_author_revealed = models.BooleanField(
        default=False,
        verbose_name="作者公開済み",
        help_text="作者が公開済みの場合はTrue"
    )
    

    
    @staticmethod
    def get_current_time():
        """現在のローカル日時を返す"""
        return timezone.localtime(timezone.now())
    
    @staticmethod
    def find_current_games():
        now = timezone.localtime(timezone.now()).date()
        return MaturiGame.objects.filter(
            maturi_start_date__lte=now,
            maturi_end_date__gte=now
        )
    
    # 現在のゲームを見つける
    @classmethod
    def find_current_game(cls):
        now = timezone.localtime(timezone.now()).date()
        return cls.objects.filter(
            maturi_start_date__lte=now,
            maturi_end_date__gte=now
        ).first()
    
    # 次のゲームを見つける
    @classmethod
    def find_next_game(cls):
        now = timezone.localtime(timezone.now()).date()
        return cls.objects.filter(
            is_prediction_period_finished,
            maturi_start_date__gt=now
        ).order_by('maturi_start_date').first()

    def is_entry_period(self):
        now = timezone.localtime(timezone.now()).date()
        return self.entry_start_date <= now <= self.entry_end_date

    def is_writing_period(self):
        """
        執筆期間の判定
        """
        now = timezone.localtime(timezone.now()).date()
        return (self.start_date <= now <= self.end_date)

    # @freeze_time("2024-12-20 12:00:00")
    def is_prediction_period(self):
        now = timezone.now().date()
        print(f"Checking prediction period:")
        print(f"Now: {now}")
        print(f"Start: {self.prediction_start_date}")
        print(f"End: {self.prediction_end_date}")
        return self.prediction_start_date <= now <= self.prediction_end_date

    def __str__(self):
        return self.title


    def is_user_entered(self, user):
        """指定されたユーザーがこのゲームにエントリーしているかどうかをチェックする"""
        return self.entrants.filter(id=user.id).exists()

    def get_current_maturi_phrases(self):
        """現在の祭りの語句を取得する"""
        return self.phrases.all()

    def check_required_phrases(self, content):
        """
        必要な語句が含まれているかチェックする
        戻り値: (bool, list) - (チェック結果, 不足している語句のリスト)
        """
        if not content:  # コンテンツが空の場合のチェック
            return False, list(self.phrases.values_list('text', flat=True))
            
        # 全ての必要な語句を取得
        required_phrases = set(self.phrases.values_list('text', flat=True))
        content_lower = content.lower()
        
        # 使用されている語句を確認（重複なしで）
        used_phrases = set()
        for phrase in required_phrases:
            if phrase.lower() in content_lower:
                used_phrases.add(phrase)
        
        # 不足している語句のリストを作成
        missing_phrases = required_phrases - used_phrases
        
        # 異なる5つの語句が含まれているかチェック
        is_valid = len(used_phrases) >= 5
        
        return is_valid, list(missing_phrases)

    def clean(self):
        """モデルのバリデーションをカスタマイズする"""
        super().clean()
        
        # タイトルの重複チェックを追加
        if MaturiGame.objects.exclude(pk=self.pk).filter(title=self.title).exists():
            raise ValidationError({'title': f"'{self.title}' はすでに存在する祭りタイトルです。"})
        
        import re
        year_match = re.match(r"(\d{4})年〜(\d{4})年の祭り", self.title)
        if not year_match:
            raise ValidationError("タイトルは 'YYYY年〜YYYY年の祭り' の形式でなければなりません。")

        start_year, end_year = map(int, year_match.groups())
        # 期間が指定された年の範囲内にあるか確認
        if not (start_year <= self.start_date.year <= end_year):
            raise ValidationError("祭りの開始日はタイトルの年の範囲内である必要がありす。")
        if not (start_year <= self.end_date.year <= end_year):
            raise ValidationError("祭りの終了日はタイトルの年の範囲内である必要があります。")
        
                # 祭りの全体的な期間がすべてのゲーム期間よりも長いことを確認
        if self.maturi_start_date and self.entry_start_date and self.maturi_start_date > self.entry_start_date:
            raise ValidationError("祭りの開始日はエントリー開始日よりも前でなければなりません。")

        if self.maturi_end_date and self.prediction_end_date and self.maturi_end_date < self.prediction_end_date:
            raise ValidationError("祭りの終了日は作者予想期間の終了日よりも後でなければなりません。")

        if self.pk is not None:  # インスタンスが保存されている場合のみ実行
            if self.phrases.exists():
                phrase_ids = self.phrases.values_list('id', flat=True)
                phrase_count = Counter(phrase_ids)
                duplicate_phrases = [
                    self.phrases.get(id=phrase_id).text 
                    for phrase_id, count in phrase_count.items() 
                    if count > 1
                ]
                if duplicate_phrases:
                    raise ValidationError(
                        f"同じ語句を複数使用することはできません。重複している語句: {', '.join(duplicate_phrases)}"
                    )

    def save(self, *args, **kwargs):
        """
        保存時にyearフィールドをタイトルから自動設定
        """
        self.clean()  # 既存のバリデーション
        
        # タイトルから年度を抽出して設定
        import re
        year_match = re.match(r"(\d{4})年〜(\d{4})年の祭り", self.title)
        if year_match:
            start_year = year_match.group(1)
            self.year = f"{start_year}年度"
        
        # prediction_start_dateから自動的にnovel_publish_start_dateを設定
        if self.prediction_start_date:
            self.novel_publish_start_date = self.prediction_start_date
        
        super().save(*args, **kwargs)

    def assign_dummy_author(self):
        """祭り期間中の匿名ユーザーを設定"""
        User = get_user_model()
        dummy_user, created = User.objects.get_or_create(
            email='maturi_writer@example.com',
            defaults={
                'username': 'maturi_writer',
                'nickname': '祭り作家',
                'user_type': User.MATURI_WRITER,  # AIからMATURI_WRITERに変更
                'email_confirmed': True,
            }
        )
        if created:
            dummy_user.set_password(User.objects.make_random_password())
            dummy_user.save()
        
        self.dummy_author = dummy_user
        self.save()

    def reveal_true_authors(self):
        """予想期間終了後に本来の著者を表示する"""
        # 祭り作家のIDは保持したまま、authorだけを変更
        maturi_writer = get_user_model().objects.get(nickname='祭り作家')
        
        for novel in self.maturi_novels.all():
            novel.author = novel.original_author
            novel.save()
            
        # 祭り作家のIDは削除せず保持
        self.dummy_author = maturi_writer
        self.save()

    # @freeze_time("2024-12-20")  # これを追加
    def is_prediction_period_finished(self):
        """
        予想期間が終了してるかどうかを判定
        """
        now = timezone.now().date()
        return now > self.prediction_end_date


    def is_novel_publish_period(self):
        now = timezone.now()
        return self.novel_publish_start_date <= now

    def can_publish_novel(self):
        """
        小説を公開できるかどうかを判定
        予想期間中のみTrueを返す
        """
        now = timezone.now().date()
        # 執筆期間中で、かつ予想期間が始まっている場合は即時公開可能
        return (self.start_date <= now <= self.end_date and 
                now >= self.prediction_start_date)

    def get_publish_restriction_message(self):
        """
        公開できない場合のメッセージを返す
        """
        now = timezone.localtime(timezone.now()).date()
        if now < self.prediction_start_date:
            return f'小説の公開は{self.prediction_start_date.strftime("%Y年%m月%d日")}からです！'
        elif now > self.end_date:
            return f'申し訳ありませんが、執筆期間（{self.end_date.strftime("%Y年%m月%d日")}まで）が終了しています。'
        return None

    @classmethod
    def get_last_finished_game(cls):
        """最後に終了したゲームを取得するクラスメソッド"""
        return cls.objects.filter(
            maturi_end_date__lt=timezone.now()
        ).order_by('-maturi_end_date').first()

    def is_finished(self):
        """ゲーム終了しているかどうかを判定するメソッド"""
        return self.maturi_end_date and self.maturi_end_date < timezone.now()

    def has_scheduled_novels(self):
        """予約投稿された小説があるかどうかを確認"""
        return self.maturi_novels.filter(
            status='scheduled',
            scheduled_at__isnull=False
        ).exists()




class Phrase(models.Model):
    text = models.CharField(max_length=100, verbose_name="語句")

    def __str__(self):
        return self.text

User = get_user_model()

class GamePrediction(models.Model):
    maturi_game = models.ForeignKey(
        'MaturiGame', 
        on_delete=models.CASCADE, 
        related_name='predictions',
        verbose_name="祭りゲーム",
        default=1
    )
    novel = models.ForeignKey(
        'novels.Novel', 
        on_delete=models.CASCADE, 
        related_name='predictions',
        verbose_name="小説"
    )
    predictor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='made_predictions',
        verbose_name="予想者"
    )
    predicted_author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_predictions',
        verbose_name="予想された作者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '保留中'),
            ('correct', '正解'),
            ('incorrect', '不正解')
        ],
        default='pending',  # デフォルト値を設定
        verbose_name='状態'
    )

    def is_correct(self):
        """予測が正解かどうかを判定"""
        return self.predicted_author_id == self.novel.original_author_id

    @classmethod
    def get_user_stats(cls, game, user):
        """ユーザーの予測統計を取得"""
        predictions = cls.objects.filter(
            maturi_game=game,
            predictor=user
        ).select_related('novel', 'novel__original_author')
        
        total = predictions.count()
        correct = sum(1 for p in predictions if p.is_correct())
        
        return {
            'total': total,
            'correct': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0
        }

    class Meta:
        unique_together = ['maturi_game', 'novel', 'predictor']
        verbose_name = "祭り予想"
        verbose_name_plural = "祭り予想一覧"
# Create your models here.

