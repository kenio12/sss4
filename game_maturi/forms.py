from django import forms
from novels.models import Novel  # Novel モデルをインポート
from django.core.exceptions import ValidationError
from utils.constants import INITIAL_CHOICES  # 選択肢をインポート
from game_maturi.models import MaturiGame
import logging

logger = logging.getLogger(__name__)

# 🔥🔥🔥 祭り小説で使用可能なジャンル（通常小説と同じ）🔥🔥🔥
# ※ 以下のジャンルは祭り小説では使用禁止：
#   - レジェンド小説、バトル、大会、オフ会、官能、三題噺
# ※ 通常小説（novels/forms.py）と同じ選択肢を使うこと！
MATURI_GENRE_CHOICES = [
    ('', 'ジャンルを選択'),
    ('初めましての挨拶', '初めましての挨拶'),
    ('ジョーク', 'ジョーク'),
    ('サスペンス', 'サスペンス'),
    ('シリーズ', 'シリーズ'),
    ('ファンタジー', 'ファンタジー'),
    ('恋愛', '恋愛'),
    ('日常', '日常'),
    ('雑談', '雑談'),
    ('ミステリー', 'ミステリー'),
    ('ノンフィクション', 'ノンフィクション'),
    ('ホラー', 'ホラー'),
    ('時代', '時代'),
    ('コメディ', 'コメディ'),
    ('歴史', '歴史'),
    ('私小説', '私小説'),
    ('未分類', '未分類'),
    ('運用相談', '運用相談'),
]

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
        error_messages={'required': '内容を入力してください。'},
        strip=False  # 先頭・末尾のスペースを保持
    )
    # 🔥 ジャンル選択フィールド（祭り小説用・通常小説と同じ選択肢）🔥
    # ※ GENRE_CHOICESは使わない！禁止ジャンルが含まれてるから！
    genre = forms.ChoiceField(
        label='ジャンル',
        choices=MATURI_GENRE_CHOICES,
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

