from django.urls import path
from .views import CustomLoginView, SignUpView, activate
from django.contrib.auth.views import LogoutView
from .views import email_confirmation_sent, delete_account
from .views import create_profile
from . import views
from .views import edit_profile  # edit_profile ビューをインポート
from .views import view_profile  # view_profile ビューをインポート
from .views import update_first_login  # この行を追加
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .views import CustomPasswordResetView  # カスタムビューをインポート
from .views import MemberListView  # 名前を修正
from .views import CustomPasswordChangeView

app_name = 'accounts'  # この行を追加

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),  
    path('activate/<uidb64>/<token>/', activate, name='activate'),
    path('email-confirmation-sent/', email_confirmation_sent, name='email_confirmation_sent'),
    path('delete-account/', delete_account, name='delete_account'),
    path('create_profile/', create_profile, name='create_profile'),
    path('edit_profile/', edit_profile, name='edit_profile'),  # プロフィール編集ページへのURL
    path('profile/', views.view_profile, name='view_profile'),  # 自分のプロファイルページへのURL
    path('profile/<int:user_id>/', views.view_other_profile, name='view_other_profile'),  # 他人のプロファイルページへのURL 
    path('logout/', views.logout_view, name='logout_view'),
    path('terms_agreement/', views.terms_agreement, name='terms_agreement'),
    path('update_first_login/', update_first_login, name='update_first_login'),  # 正しく追加
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
    template_name='accounts/password_reset_confirm.html',
    success_url=reverse_lazy('accounts:password_reset_complete')  # 成功時のリダイレクト先を指定
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
    path('members/', MemberListView.as_view(), name='member_list'),
    path('password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
]