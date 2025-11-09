from django import forms
from .models import Novel
from .models import Comment

from django import forms
from .models import Novel
from utils.constants import INITIAL_CHOICES  # 正しいパスでインポート

class NovelForm(forms.ModelForm):
    # クラス変数として定義
    STATUS_CHOICES = {
        'draft': '作成中',
        'scheduled': '予約公開',
        'published': '公開'
    }

    def __init__(self, *args, is_writing_period=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_writing_period = is_writing_period
        # インスタンスが存在する場合（編集時）、ステータスの初期値を設定
        if self.instance and self.instance.status:
            self.initial.setdefault(
                'status',
                self.STATUS_CHOICES.get(self.instance.status, self.instance.status)
            )

    class Meta:
        model = Novel
        fields = ['genre', 'title', 'initial', 'content', 'status']  # initialをtitleの後に移動

    title = forms.CharField(
        label='タイトル：30字内',  # HTMLタグを使わずにラベルを設定
        max_length=30, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'wifont-size: 20px;'}),
        error_messages={'max_length': 'タイトルは30文字以内で入力してください。'}
    )

    initial = forms.ChoiceField(
        label='タイトルの頭文字のふりがな',  # HTMLタグを使わずにラベルを設定
        choices=INITIAL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'max-width: 300px; font-size: 58.5px;'}),
    )

    content = forms.CharField(
        label='内容：目安3000字ぐらいがBEST',  # HTMLタグを使わずにラベルを設定
        widget=forms.Textarea(attrs={'class': 'form-control', 'style': 'max-width: 600px; height: 300px; font-size: 36px;'}),
        max_length=30000, 
        error_messages={'max_length': '内容は10000文字以内で入力してください。'}
    )

    genre = forms.ChoiceField(
        label='ジャンル',  # HTMLタグを使わずにラベルを設定
        choices=[
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
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'max-width: 300px; font-size: 36px; height: 38px;'
        })
    )

    status = forms.ChoiceField(
        label='ステータス',
        choices=Novel.STATUS_CHOICES,
        disabled=True,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )

class CommentForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'コメント入れるならここやで！',
        'class': 'comment-textarea',  # CSSクラスを追加
        'maxlength': '1000',  # 最大文字数を1000に設定
    }), max_length=1000)  # ここにもmax_lengthを設定

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'コメントを入力してください'
            })
        }
