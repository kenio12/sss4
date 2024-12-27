from django.db import models
from django.utils import timezone
from django.conf import settings

class Contact(models.Model):
    SOURCE_CHOICES = [
        ('terms', '利用規約ページ'),
        ('signup', 'サインアップページ'),
        ('login', 'ログインページ'),
        ('other', 'その他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '未対応'),
        ('resolved', '対応済み'),
    ]

    email = models.EmailField('メールアドレス')
    name = models.CharField('お名前', max_length=100)
    subject = models.CharField('件名', max_length=200)
    message = models.TextField('お問い合わせ内容')
    source = models.CharField('問い合わせ元', max_length=20, choices=SOURCE_CHOICES, default='other')
    created_at = models.DateTimeField('送信日時', default=timezone.now)
    status = models.CharField('対応状況', max_length=20, choices=STATUS_CHOICES, default='pending')
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='対応者',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_contacts'
    )
    response_text = models.TextField(blank=True, null=True, verbose_name='対応内容')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='対応日時')
    responded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responded_contacts',
        verbose_name='対応者'
    )

    class Meta:
        verbose_name = 'お問い合わせ'
        verbose_name_plural = 'お問い合わせ'
        ordering = ['-created_at']  # 新しい順に並べる

    def __str__(self):
        return f"{self.subject} - {self.name} ({self.get_source_display()})" 