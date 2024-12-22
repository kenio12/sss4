from django import forms
from django.conf import settings  # settingsをインポート
from game_maturi.models import MaturiGame, Phrase, generate_year_choices  # generate_year_choicesをインポート
import datetime
from django.contrib.auth import get_user_model  # get_user_modelをインポート
from django.core.exceptions import ValidationError

User = get_user_model()  # これを追加

class MaturiGameForm(forms.ModelForm):
    # models.pyで定義した選択肢を使用
    title = forms.ChoiceField(
        choices=generate_year_choices(),
        label="タイトル"
    )
    phrases = forms.ModelMultipleChoiceField(
        queryset=Phrase.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='語句選択'
    )

    # 12個の語句フィールドを追加（ラベルを完全に削除）
    phrase1 = forms.CharField(max_length=30, required=False, label='')
    phrase2 = forms.CharField(max_length=30, required=False, label='')
    phrase3 = forms.CharField(max_length=30, required=False, label='')
    phrase4 = forms.CharField(max_length=30, required=False, label='')
    phrase5 = forms.CharField(max_length=30, required=False, label='')
    phrase6 = forms.CharField(max_length=30, required=False, label='')
    phrase7 = forms.CharField(max_length=30, required=False, label='')
    phrase8 = forms.CharField(max_length=30, required=False, label='')
    phrase9 = forms.CharField(max_length=30, required=False, label='')
    phrase10 = forms.CharField(max_length=30, required=False, label='')
    phrase11 = forms.CharField(max_length=30, required=False, label='')
    phrase12 = forms.CharField(max_length=30, required=False, label='')

    maturi_start_date = forms.DateField(
        label='祭り開始日',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    maturi_end_date = forms.DateField(
        label='祭り終了日',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )

    class Meta:
        model = MaturiGame
        fields = [
            'title', 'description', 'start_date', 'end_date', 
            'prediction_start_date', 'prediction_end_date', 
            'entry_start_date', 'entry_end_date', 'entrants', 'phrases',
            'maturi_start_date', 'maturi_end_date', 'novel_publish_start_date'
        ] + [f'phrase{i}' for i in range(1, 13)]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'prediction_start_date': forms.DateInput(attrs={'type': 'date'}),
            'prediction_end_date': forms.DateInput(attrs={'type': 'date'}),
            'entry_start_date': forms.DateInput(attrs={'type': 'date', 'input_formats': ['%Y-%m-%d', '']}),
            'entry_end_date': forms.DateInput(attrs={'type': 'date', 'input_formats': ['%Y-%m-%d', '']}),
            'novel_publish_start_date': forms.DateInput(attrs={'type': 'date'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def clean_phrases(self):
        phrases = self.cleaned_data.get('phrases', [])  # デフォルト値を空リストに
        if not phrases:  # phrasesが空の場合はそのまま返す
            return phrases
        
        cleaned_phrases = []
        for phrase in phrases:
            if hasattr(phrase, 'text'):  # phraseがPhraseオブジェクトの場合
                cleaned_phrase = phrase.text.replace(' ', '')
                cleaned_phrases.append(phrase)
            else:  # phraseが文字列の場合
                cleaned_phrase = str(phrase).replace(' ', '')
                phrase_obj, _ = Phrase.objects.get_or_create(text=cleaned_phrase)
                cleaned_phrases.append(phrase_obj)
        
        return cleaned_phrases

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # フィールドの必須状態を設定
        self.fields['title'].required = True
        self.fields['description'].required = False
        self.fields['entrants'].required = False
        
        # 日付フィールドのフォーマットを指定
        date_fields = [
            'maturi_start_date', 'maturi_end_date',
            'entry_start_date', 'entry_end_date',
            'start_date', 'end_date',
            'prediction_start_date', 'prediction_end_date',
            'novel_publish_start_date'
        ]
        
        for field_name in date_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False
                self.fields[field_name].input_formats = ['%Y-%m-%d']
        
        if 'instance' in kwargs and kwargs['instance'] is not None:
            # 編集時の処理
            instance = kwargs['instance']
            
            # 既存の祭りのタイトルを取得
            used_titles = set(MaturiGame.objects.values_list('title', flat=True))
            print("\n=== デバッグ情報 ===")
            print("使用済みタイトル:", used_titles)
            
            # 選択肢を生成
            all_choices = generate_year_choices()
            print("生成された全選択肢:", [title for title, _ in all_choices])
            
            # 使用済みタイトルを除外
            choices = [
                (title, title) for title, _ in all_choices
                if title not in used_titles
            ]
            print("フィルタリング後の選択肢:", [title for title, _ in choices])
            print("==================\n")
            
            # 編集時は自分のタイトルを選択肢に追加
            if instance.pk:
                choices.append((instance.title, instance.title))
            
            self.fields['title'].choices = choices
            
            # 既存のphrasesを設定
            self.fields['phrases'].queryset = Phrase.objects.all()
            self.fields['phrases'].initial = instance.phrases.all()
            
            # 既存の日付を設定
            for field_name in date_fields:
                if hasattr(instance, field_name):
                    value = getattr(instance, field_name)
                    if value:
                        self.initial[field_name] = value
            
            # 語句フィールドの初期値を設定
            phrases = list(instance.phrases.all())
            for i in range(1, 13):
                field_name = f'phrase{i}'
                if i <= len(phrases):
                    self.fields[field_name].initial = phrases[i-1].text
                else:
                    self.fields[field_name].initial = ''
        else:
            # 新規作成時の処理
            used_titles = set(MaturiGame.objects.values_list('title', flat=True))
            choices = [
                (title, title) for title, _ in generate_year_choices()
                if title not in used_titles
            ]
            self.fields['title'].choices = choices
            self.fields['entrants'].queryset = User.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # フォームから送信されたデータ直接設定（phrases と entrants 以外）
        for field_name in self.cleaned_data:
            if field_name not in ['phrases', 'entrants'] and field_name in self.fields and self.cleaned_data[field_name] is not None:
                setattr(instance, field_name, self.cleaned_data[field_name])
        
        if commit:
            instance.save()
            
            # entrantsの保存
            if 'entrants' in self.cleaned_data:
                instance.entrants.set(self.cleaned_data['entrants'])
            
            # 既存のphrasesをクリア
            instance.phrases.clear()
            
            # 新しい語句の処理
            new_phrases = []
            for i in range(1, 13):
                phrase_text = self.cleaned_data.get(f'phrase{i}')
                if phrase_text:
                    phrase_text = phrase_text.strip()
                    phrase, created = Phrase.objects.get_or_create(text=phrase_text)
                    new_phrases.append(phrase)
            
            # 選択された���存のphrasesを追加
            if 'phrases' in self.cleaned_data and self.cleaned_data['phrases']:
                new_phrases.extend(self.cleaned_data['phrases'])
            
            # 重複を除去して保存
            unique_phrases = list(set(new_phrases))
            instance.phrases.set(unique_phrases)
        
        return instance
    def clean_title(self):
        title = self.cleaned_data.get('title')
        
        # 編集時は自分自身を除外してチェック
        if self.instance.pk:
            if MaturiGame.objects.exclude(pk=self.instance.pk).filter(title=title).exists():
                raise ValidationError(f"'{title}' はすでに存在する祭りタイトルです。")
        else:
            # 新規作成時は全件チェック
            if MaturiGame.objects.filter(title=title).exists():
                raise ValidationError(f"'{title}' はすでに存在する祭りタイトルです。")
        
        return title

