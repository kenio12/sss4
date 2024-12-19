from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Profile  # Profileモデルをインポート

# カスタムユーザーモデルを取得
User = get_user_model()

from django.utils.safestring import mark_safe

class UserCreationForm(forms.ModelForm):
    email = forms.EmailField(label='メールアドレス', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    nickname = forms.CharField(
    label='ニックネーム', 
    widget=forms.TextInput(attrs={'class': 'form-control'}),  
    required=True  
    )
    # user_type フィールドの選択肢を「無料会員」のみに限定
    user_type = forms.ChoiceField(label='ユーザータイプ', choices=[(User.FREE_MEMBER, '無料会員')], widget=forms.Select(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='パスワード', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='パスワード確認', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('email', 'nickname', 'user_type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        # user_type フィールドのデフォルト値を「無料会員」に設定
        self.fields['user_type'].initial = User.FREE_MEMBER

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("パスワードが一致しません。")
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.username = self.cleaned_data["email"]  # usernameフィールドにメールアドレスを設定
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("このメールアドレスは既に使用されています。")
        return email

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if not nickname:
            raise forms.ValidationError("ニックネームは必須です。")
        if User.objects.filter(nickname=nickname).exists():
            raise forms.ValidationError("このニックネームは既に使用されています。")
        return nickname
    
    

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'nickname', 'user_type')

# 入力データを検証するための関数
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        nickname = cleaned_data.get('nickname')
        # Free WriterまたはFree Readerの場合、ニックネームを必須とする
        if user_type == User.FREE_MEMBER and not nickname:
            raise ValidationError("Free WriterまたはFree Readerの場合、ニックネームは必須です。")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
    

class CustomAuthenticationForm(AuthenticationForm):
    # ユーザー名フィールドを「メールアドレスまたはニックネーム」として定義
    username = forms.CharField(label='メアドorニックネーム')

    def clean(self):
        # 入力されたユーザー名とパスワードを取得
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        # メールアドレスまたはニックネームでユーザーを検索
        user = User.objects.filter(email=username).first() or User.objects.filter(nickname=username).first()
        
        # ユーザーが見つからない場合はエラーを発生させる
        if not user:
            raise ValidationError("指定されたユーザーは存在しません。")

        # パスワードが一致しない場合はエラーを発生させる
        if not user.check_password(password):
            raise ValidationError("パスワードが正しくありません。")

        # ユーザーを認証済みとしてマーク
        self.user_cache = user
        return self.cleaned_data

from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    # ageフィールドをChoiceFieldとして定義し、ProfileモデルからAGE_CHOICESを選択肢として設定
    age = forms.ChoiceField(choices=Profile.AGE_CHOICES, required=False, label='だいたいの年齢', widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Profile
        fields = ['age', 'strengths', 'weaknesses', 'gender', 'species', 'pet_peeve', 'habit', 'residence', 'likes_matcha', 'hobby', 'current_trend', 'favorite_songs', 'favorite_dance', 'favorite_phrase', 'introduction']
        labels = {
            'strengths': '長所',
            'weaknesses': '短所',
            'age': 'だいたいの年齢',
            'gender': '性別',
            'species': '生物名',
            'pet_peeve': '逆鱗',
            'habit': '癖',
            'residence': '都道府県',
            'likes_matcha': '抹茶が好きか',
            'hobby': '趣味',
            'current_trend': 'マイブーム',
            'favorite_songs': '好きな曲',
            'favorite_dance': '好きなダンス',
            'favorite_phrase': '好きな言葉',
            'introduction': '自己紹介',
        }
        widgets = {
            'strengths': forms.TextInput(attrs={'class': 'form-control'}),
            'weaknesses': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'species': forms.TextInput(attrs={'class': 'form-control'}),
            'pet_peeve': forms.TextInput(attrs={'class': 'form-control'}),
            'habit': forms.TextInput(attrs={'class': 'form-control'}),
            'residence': forms.Select(attrs={'class': 'form-control'}),
            'likes_matcha': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hobby': forms.TextInput(attrs={'class': 'form-control'}),
            'current_trend': forms.TextInput(attrs={'class': 'form-control'}),
            'favorite_songs': forms.TextInput(attrs={'class': 'form-control'}),
            'favorite_dance': forms.TextInput(attrs={'class': 'form-control'}),
            'favorite_phrase': forms.TextInput(attrs={'class': 'form-control'}),
            'introduction': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def clean(self):
        # 必要に応じてクリーンメソッドでカスタム検証を追加
        cleaned_data = super().clean()
        return cleaned_data