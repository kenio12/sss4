from django import forms
from django.forms import ModelForm, CharField, Textarea, BooleanField, CheckboxInput
from django.utils import timezone
from datetime import timedelta
from .models import Comment, TitleProposal, MonthlySameTitleInfo
from novels.models import Novel

from django.forms import ModelForm
from .models import Novel, TitleProposal
from django import forms
from django.utils import timezone
from datetime import timedelta
from utils.constants import INITIAL_CHOICES

class NovelForm(ModelForm):
    initial = forms.ChoiceField(choices=INITIAL_CHOICES, label='イニシャル', required=False)
    is_same_title_game = forms.BooleanField(label='同タイトル', required=False, initial=True)
    status = forms.CharField(widget=forms.HiddenInput(), required=False, initial='published')

    def clean(self):
        """バリデーション時に同タイトル設定を強制"""
        cleaned_data = super().clean()
        # 同タイトルフラグを強制的に True に
        cleaned_data['is_same_title_game'] = True
        # ジャンルも '同タイトル' に固定
        cleaned_data['genre'] = '同タイトル'
        return cleaned_data

    def save(self, commit=True):
        """保存時に同タイトル関連の設定を強制"""
        novel = super().save(commit=False)
        novel.is_same_title_game = True
        novel.genre = '同タイトル'
        
        # 新規作成時のみ月を設定（既存の月は変更しない）
        if not novel.pk and not novel.same_title_event_month:
            novel.same_title_event_month = timezone.now().strftime('%Y-%m')
            
            # 公開状態かつ一番槍の場合はMonthlySameTitleInfoも作成
            if novel.status == 'published' and not MonthlySameTitleInfo.objects.filter(month=novel.same_title_event_month).exists():
                novel.save()  # 先にnovelを保存
                MonthlySameTitleInfo.objects.create(
                    novel=novel,
                    title=novel.title,
                    author=novel.author,
                    proposer=novel.author,  # 一番槍の場合は作者が提案者
                    published_date=timezone.now().date(),
                    month=novel.same_title_event_month
                )
        
        if commit:
            novel.save()
        
        return novel

    class Meta:
        model = Novel
        fields = ['title', 'content', 'is_same_title_game', 'initial', 'status']


class CommentForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'コメント入れるならここやで！',
        'class': 'comment-textarea',
        'maxlength': '1000',
    }), max_length=1000)

    class Meta:
        model = Comment
        fields = ['content']