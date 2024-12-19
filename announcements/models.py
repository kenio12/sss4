from django.db import models
from django.utils import timezone

class Announcement(models.Model):
    title = models.CharField('タイトル', max_length=200)
    content = models.TextField('内容')
    created_at = models.DateTimeField('作成日時', default=timezone.now)
    created_by = models.ForeignKey('accounts.User', verbose_name='作成者', on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField('公開状態', default=True)
    is_pinned = models.BooleanField('固定表示', default=False)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = 'お知らせ'
        verbose_name_plural = 'お知らせ'

    def __str__(self):
        return self.title
