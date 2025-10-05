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


from django.conf import settings
from django.db import models

class SameTitleEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ユーザー")
    month = models.DateField(verbose_name="エントリー月")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="エントリー日時")


    class Meta:
        unique_together = ('user', 'month')

    def __str__(self):
        return f"{self.user}が{self.month}にエントリー"


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

