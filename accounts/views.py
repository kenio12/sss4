from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import CustomAuthenticationForm, UserCreationForm
from django.contrib.auth import login,get_user_model,logout
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from .models import Profile
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.views import generic
from .forms import UserCreationForm
from novels.models import Novel  # Novelモデルをインポート
from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.sites.shortcuts import get_current_site

import os

from django.core.mail import EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string

import logging

logger = logging.getLogger(__name__)

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'default_sender@example.com')

# メール送信機能
def send_confirmation_email(user, request):
    
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    subject = '超短編小説会Ⅳ からっす！'  # 件名を変更
    from_email = EMAIL_HOST_USER
    to = [user.email]
    text_content = 'This is an important message.'
    html_content = render_to_string('accounts/confirmation_email.html', {
        'user': user,
        'domain': domain,
        'uid': uid,
        'token': token,
        'protocol': protocol,
    })
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()



class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = CustomAuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        
        # アクティブでないユーザーの場合
        if not user.is_active:
            messages.warning(
                self.request,
                f'{user.nickname}さんはユーザー登録は済んでいますが、メールでの承認が済んでおらず、'
                'ログインできません。以下のボタンから認証メールを再送信してください。'
            )
            # メール再送信ページにリダイレクト（emailパラメータ付き）
            return redirect(f"{reverse('accounts:resend_activation')}?email={user.email}")
        
        # アクティブなユーザーの場合は通常のログイン処理
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('home:home')


from django.urls import reverse

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    template_name = 'accounts/signup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_contacts'] = []  # お問い合わせモーダル用
        
        # デバッグ用：フォームのエラーメッセージを確認
        if self.request.method == 'POST' and 'form' in context:
            print("Form errors:", context['form'].errors)
            if context['form'].errors.get('email'):
                print("Email errors:", context['form'].errors['email'])
        
        return context

    def dispatch(self, *args, **kwargs):
        if not self.request.session.get('agreed_to_terms', False):
            # 利用規約への同意がセッションに記録されていい場合は、利用規約ページにリダイレクト
            terms_url = reverse('home:terms')  # 'home:terms'は利用規約ページの名前空間とビュー名
            return redirect(f'{terms_url}?signup=true')  # クエリパラメータをURLに追加
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        send_confirmation_email(user, self.request)
        return redirect('accounts:email_confirmation_sent')

from django.shortcuts import redirect  # この行を追加
from django.http import HttpResponseRedirect

def terms_agreement(request):
    if request.method == 'POST':
        request.session['agreed_to_terms'] = True  # セッションに同意を記録
        return redirect('accounts:signup')  # サインアップページにリダイレクト
    else:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

# ビュー関数またはビュークラス内で、signupクエリパラメータが存在し、かつ'true'であるかどうかをチェックし、その結果をテンプレートコンテキストに追加します。
def some_view(request):
    signup = request.GET.get('signup', 'false').lower() == 'true'
    context = {'signup': signup}
    return render(request, 'home/terms.html', context)


# メール確認ビュー
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # デバッグログを追加
        logger.info(f"Activation attempt for user {user.email}")
        logger.info(f"Token valid: {default_token_generator.check_token(user, token)}")
        
        if user is not None and default_token_generator.check_token(user, token):
            # 確実にアクティブ化
            user.is_active = True
            user.save()
            
            # ログを残す
            logger.info(f"User {user.email} activated successfully. is_active: {user.is_active}")
            
            # ユーザーにメッセージを表示
            messages.success(request, 'メール認証が完了しました！ログインしてください。')
            
            return redirect('accounts:login')
        else:
            # 認証失敗時のログ
            logger.error(f"Activation failed for user {user.email} with token {token}")
            messages.error(request, '認証リンクが無効です。')
            return redirect('accounts:login')
            
    except Exception as e:
        # エラー時のログ
        logger.error(f"Activation error: {str(e)}")
        messages.error(request, '認証処理中にエラーが発生しました。')
        return redirect('accounts:login')

def email_confirmation_sent(request):
    # ユーザーに表示するメッセージ
    message = "確認メールを送信しました。メール内のリンクをクリックして登録を完了してください。もし受信ボックスにない場合、迷惑メールのボックスを見てください！"
    return HttpResponse(message)

# ポップアップ用のコードや！
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def update_first_login(request):
    # ログインしているユーザーのProfileを取得
    user_profile = request.user.profile
    # first_loginがTrueの場合のみFalseに更新
    if user_profile.first_login:
        user_profile.first_login = False
        user_profile.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

from django.utils.timezone import now

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)  # ユーザーをログアウトさせる
        
        # 現在の日時を取得
        current_time = now().strftime('%Y-%m%d%H%M%S')
        
        # メールアドレスを更新し、usernameにも同じ値を設定
        unique_value = f"deleted_{current_time}_{user.email}"
        user.email = unique_value
        user.username = unique_value  # usernameにも同じ値を設定
        
        user.is_active = False  # ユーザーを非アクティブにする
        user.save()  # 変更を保存
        
        messages.success(request, 'アカウントが正常に削除されました。ご利用ありがとうございました。')
        return redirect('home:home')  # ホームページにリダイレクト
    else:
        return render(request, 'accounts/delete_account.html')
    
@login_required
def create_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('accounts:view_profile')
    else:
        form = ProfileForm()
    return render(request, 'accounts/profile_form.html', {'form': form})

User = get_user_model()

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Profile
from novels.models import Novel
from django.db import models

@login_required
def view_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    selected_writer_id = None
    selected_writer_nickname = ""  # ニックネーム用の変数を初期化

    if request.method == 'POST':
        selected_writer_id = request.POST.get('selected_writer')
        if selected_writer_id:
            selected_writer = get_user_model().objects.get(id=selected_writer_id)
            profile.selected_writer = selected_writer
            profile.save()
            selected_writer_nickname = selected_writer.nickname  # 選択された作家のニックネームを取得
    else:
        if profile.selected_writer:
            selected_writer_id = profile.selected_writer.id
            selected_writer_nickname = profile.selected_writer.nickname  # 選択された作家のニックネームを取得

    # 新規ユーザーが初めてログインした場合にセッションにフラグを設定
    if profile.first_login:
        request.session['show_welcome_popup'] = True
        profile.first_login = False
        profile.save()
    else:
        request.session['show_welcome_popup'] = False

    # ユーザーの小説をステータスによって分ける（祭り小説も含める）
    drafts = Novel.objects.filter(
        models.Q(author=request.user) | models.Q(original_author=request.user),
        status='draft'
    ).order_by('-created_at')

    published = Novel.objects.filter(
        models.Q(author=request.user) | models.Q(original_author=request.user),
        status='published'
    ).order_by('-published_date')

    # 予約公開の小説を取得（祭りゲーム情報も含める）
    scheduled = Novel.objects.filter(
        models.Q(author=request.user) | models.Q(original_author=request.user),
        status='scheduled'
    ).prefetch_related(
        'maturi_games'  # ManyToManyフィールドなのでprefetch_relatedを使用
    ).order_by('-created_at')

    # 各小説の予約公開日を取得
    for novel in scheduled:
        game = novel.maturi_games.first()  # 関連する祭りゲームを取得
        if game:
            novel.scheduled_date = game.prediction_start_date  # 公開予定日を設定

    # OLD_SSS_WRITERタイプのユーザーを取得する
    old_sss_writers = get_user_model().objects.filter(user_type=get_user_model().OLD_SSS_WRITER).order_by('nickname')

    # 選択された作家の小説を取得する
    selected_writer_novels = Novel.objects.filter(author=profile.selected_writer, status='published').order_by('-published_date') if profile.selected_writer else None

    # ここで 'is_index_page' を追加する
    is_index_page = request.path == '/'  # トップページのパスに応じて変更するかもしれん

    # 🆕 イベント履歴データを取得（Step 3 & 4）
    # 一番槍獲得歴
    ichiban_yari_records = Novel.objects.filter(
        models.Q(author=request.user) | models.Q(original_author=request.user),
        is_first_post=True,
        event='同タイトル',
        status='published'
    ).order_by('-same_title_event_month')

    # 一番盾獲得歴（MonthlySameTitleInfoから取得）
    from game_same_title.models import MonthlySameTitleInfo
    ichiban_tate_records = MonthlySameTitleInfo.objects.filter(
        proposer=request.user
    ).order_by('-month')

    # 同タイトル崩れ歴
    same_title_failure_records = Novel.objects.filter(
        models.Q(author=request.user) | models.Q(original_author=request.user),
        is_same_title_failure=True,
        status='published'
    ).order_by('-same_title_event_month')

    # 祭り参加歴
    maturi_records = Novel.objects.filter(
        models.Q(author=request.user) | models.Q(original_author=request.user),
        event='祭り',
        status='published'
    ).order_by('-published_date')

    context = {
        'profile': profile,
        'drafts': drafts,
        'published': published,
        'scheduled': scheduled,  # 新しく追加
        'is_new_user': not profile.first_login,  # first_loginがFalseになった後なので、新規ユーザーではない
        'old_sss_writers': old_sss_writers,
        'selected_writer_novels': selected_writer_novels,
        'selected_writer_id': selected_writer_id,
        'selected_writer_nickname': selected_writer_nickname,
        'is_index_page': is_index_page,
        # 🆕 イベント履歴を追加
        'ichiban_yari_records': ichiban_yari_records,
        'ichiban_tate_records': ichiban_tate_records,
        'same_title_failure_records': same_title_failure_records,
        'maturi_records': maturi_records,
    }

    return render(request, 'accounts/view_profile.html', context)

@login_required
def edit_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)  # プロフィールが存在しない場合は新規作成

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('accounts:view_profile')  # プロフィールページにリダイレクト
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/profile_form.html', {'form': form})



@require_POST
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('accounts:login'))  # ログアウト後にリダイレクトするページを指定



from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from .models import Profile
from novels.models import Novel  # Novelモデルをインポート

def view_other_profile(request, user_id):
    User = get_user_model()
    profile_user = get_object_or_404(User, pk=user_id)
    profile = Profile.objects.filter(user=profile_user).first()

    # profile_user が書いた公開小説を取得する
    novels = Novel.objects.filter(author=profile_user, status='published').order_by('-published_date')

    context = {
        'profile_user': profile_user,
        'profile': profile,  # プロフィール情報を context に追加
        'novels': novels,  # ここで取得した小説をテンプレートに渡す
    }

    return render(request, 'accounts/view_other_profile.html', context)

from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset_form.html'  # パスワードリセットフォームのテンプレート
    email_template_name = 'accounts/password_reset_email.html'  # パスワードリセットメールのテンプレート
    subject_template_name = 'accounts/password_reset_subject.txt'  # メールの件名のテンプレート
    success_url = reverse_lazy('accounts:password_reset_done')  # パスワードリセット完了後のリダイレクト先

    def get_email_context(self, **kwargs):
        context = super().get_email_context(**kwargs)
        user = context.get('user')
        if user:
            context['uid'] = urlsafe_base64_encode(force_bytes(user.pk))
            context['token'] = default_token_generator.make_token(user)
                    # セッションからメールアドレスを取得する例
            context['email'] = self.request.session.get('user_email')
            # PASSWORD_RESET_TIMEOUTが未定義の場合は1分（60秒）のデフォルト値を使用
            password_reset_timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 300)
            context['expiration_minutes'] = password_reset_timeout // 60  # 分単位で計算

        return context
    

from django.core.paginator import Paginator
from .models import User
from django.views import generic

class MemberListView(generic.ListView):
    model = User
    template_name = 'accounts/member_list.html'  # テンプレート名を修正
    context_object_name = 'users'
    paginate_by = 10  # 1ページあたり10件表示

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        likes_matcha = self.request.GET.get('likes_matcha', '')
        if likes_matcha == 'None':
            queryset = User.objects.search(query=query, likes_matcha=None).order_by('-date_joined')
        elif likes_matcha:
            queryset = User.objects.search(query=query, likes_matcha=likes_matcha).order_by('-date_joined')
        else:
            queryset = User.objects.search(query=query).order_by('-date_joined')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['likes_matcha'] = self.request.GET.get('likes_matcha', '')
        return context
    

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:view_profile')  # 全てのユーザーをプロフィールページへ

    def form_valid(self, form):
        # パスワード変更成功時のメッセージ
        messages.success(self.request, 'パスワードを変更しました。')
        return super().form_valid(form)

    def get_success_url(self):
        # 念のため、ここでも設定（動的なURLが必要な場合用）
        return reverse('accounts:view_profile')
    

def resend_activation(request):
    # GETパラメータからメールアドレスを取得
    email = request.GET.get('email')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, is_active=False)
            send_confirmation_email(user, request)
            messages.success(
                request, 
                f'{user.nickname}さんに認証メールを再送信しました。'
                'メールをご確認の上、認証を完了してください。'
            )
            return redirect('accounts:login')
            
        except User.DoesNotExist:
            messages.error(
                request, 
                'このメールアドレスは登録されていないか、既に認証済みです。'
            )
            return redirect('accounts:login')
    
    # GETリクエストの場合、フォームを表示
    return render(request, 'accounts/resend_activation.html', {'email': email})


def unsubscribe(request, token):
    """
    メール配信停止ビュー
    署名付きトークンを検証して通知設定を全てFalseにする
    """
    from django.core import signing

    try:
        # 署名付きトークンを検証（24時間有効）
        user_id = signing.loads(token, salt='email_unsubscribe', max_age=86400)
        user = User.objects.get(id=user_id)

        # EmailNotificationSettingsが存在しない場合は作成
        from .models import EmailNotificationSettings
        settings, created = EmailNotificationSettings.objects.get_or_create(user=user)

        # 全ての通知をオフ
        settings.same_title_recruitment = False
        settings.same_title_proposal = False
        settings.same_title_decision = False
        settings.save()

        # 個人情報保護: メールアドレスをマスキング
        masked_email = user.email[:3] + '***'
        logger.info(f'配信停止完了: {masked_email}')

        return render(request, 'accounts/unsubscribe_complete.html', {
            'user': user
        })

    except signing.SignatureExpired:
        logger.error('配信停止失敗: トークンの有効期限が切れています')
        return HttpResponse('配信停止リンクの有効期限が切れています（24時間）', status=400)

    except signing.BadSignature:
        logger.error('配信停止失敗: 無効なトークンです')
        return HttpResponse('無効な配信停止リンクです', status=400)

    except User.DoesNotExist:
        logger.error(f'配信停止失敗: ユーザーが見つかりません')
        return HttpResponse('ユーザーが見つかりません', status=404)

