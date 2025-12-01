from django import forms
from novels.models import Novel, GENRE_CHOICES  # Novel モデルとGENRE_CHOICESをインポート
from django.core.exceptions import ValidationError
from utils.constants import INITIAL_CHOICES  # 選択肢をインポート
from game_maturi.models import MaturiGame
import logging

logger = logging.getLogger(__name__)

class MaturiNovelForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={'id': 'titleInput'}),
        error_messages={'required': 'タイトルを入力してください。'}
    )
    initial = forms.ChoiceField(
        label='タイトルの頭文字のふりがな',
        choices=INITIAL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'max-width: 300px; font-size: 20px; height:50px'}),
        required=True,
        error_messages={'required': 'タイトルの頭文字のふりがなを入力してください。'}
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={'id': 'contentInput'}),
        error_messages={'required': '内容を入力してください。'}
    )
    # ジャンル選択フィールド（通常のジャンルから選択）
    genre = forms.ChoiceField(
        label='ジャンル',
        choices=GENRE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'max-width: 300px; font-size: 20px; height:50px'}),
        required=True,
        error_messages={'required': 'ジャンルを選択してください。'}
    )

    status = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        initial='draft'
    )

    class Meta:
        model = Novel
        fields = ['title', 'initial', 'content', 'genre']

    def __init__(self, *args, **kwargs):
        self.is_writing_period = kwargs.pop('is_writing_period', False)
        super().__init__(*args, **kwargs)

        # すべてのフィールドを必須に設定
        for field in self.fields.values():
            field.required = True

        # ステータスの初期値設定
        if self.instance.pk:
            self.initial['status'] = self.instance.status
        else:
            self.initial['status'] = 'draft'

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        
        # 既に公開済みの作品の場合はスキップ
        if self.instance and self.instance.pk and self.instance.status == 'published':
            return cleaned_data
            
        # 新規作成または下書きからの公開の場合のみチェック
        if status == 'published' and not self.is_writing_period:
            self.add_error('status', '執筆期間中のみステータスを公開に設定できます。')
            
        return cleaned_data

    # その他のフィールドはNovelFormから継承

