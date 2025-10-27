from django.conf import settings
from django.db import models
from novels.models import Novel
from novels.models import Comment  # 修正したインポート文
from django.utils import timezone
from datetime import datetime

def current_month():
    return timezone.localtime(timezone.now()).date().replace(day=1)

class TitleProposal(models.Model):
    title = models.CharField(max_length=100, verbose_name="タイトル")
    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="提案者")
    proposed_at = models.DateTimeField(default=timezone.now, verbose_name="提案日時")
    proposal_month = models.DateField(default=current_month, verbose_name="提案月")  # defaultに関数を指定

    def __str__(self):
        return f"{self.title} ({self.proposal_month.strftime('%Y-%m')})"


from django.db import models

class MonthlySameTitleInfo(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, verbose_name="関連小説")
    title = models.CharField(max_length=255)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="作者")
    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="提案者", related_name="proposed_titles")
    published_date = models.DateField()
    month = models.CharField(max_length=7, unique=True)  #


    def __str__(self):
        return f"{self.month}: {self.title} by {self.author}"


class PendingNotification(models.Model):
    """
    メール通知予約テーブル
    投稿時に即座送信せず、指定時刻に一斉送信するための予約データ
    - 提案通知：翌日12時（正午）
    - 決定通知・追随通知：翌日17時（午後5時）
    """
    NOTIFICATION_TYPES = [
        ('提案', 'タイトル提案通知'),
        ('決定', '同タイトル決定通知（一番槍）'),
        ('追随', '同タイトル追随通知（2番目以降）'),
        ('same_title_recruitment', '同タイトル募集通知（月初）'),
    ]

    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, verbose_name="通知タイプ")
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, null=True, blank=True, verbose_name="関連小説")
    proposal = models.ForeignKey('TitleProposal', on_delete=models.CASCADE, null=True, blank=True, verbose_name="関連タイトル提案")
    rank = models.IntegerField(null=True, blank=True, verbose_name="順位（追随通知用）")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="予約日時")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="送信日時")
    is_sent = models.BooleanField(default=False, verbose_name="送信済み")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "メール通知予約"
        verbose_name_plural = "メール通知予約"
        constraints = [
            # 追随通知の重複防止（同じ小説・同じ順位で1つだけ）
            models.UniqueConstraint(
                fields=['notification_type', 'novel', 'rank'],
                name='unique_follower_notification',
                condition=models.Q(notification_type='追随')
            ),
            # 一番槍通知の重複防止（同じ小説で1つだけ）
            models.UniqueConstraint(
                fields=['notification_type', 'novel'],
                name='unique_decision_notification',
                condition=models.Q(notification_type='決定')
            ),
            # 提案通知の重複防止（同じ提案で1つだけ）
            models.UniqueConstraint(
                fields=['notification_type', 'proposal'],
                name='unique_proposal_notification',
                condition=models.Q(notification_type='提案')
            ),
        ]

    def __str__(self):
        type_display = dict(self.NOTIFICATION_TYPES).get(self.notification_type, self.notification_type)
        if self.novel:
            return f"{type_display} - {self.novel.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
        return f"{type_display} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

