from django.core.paginator import Paginator
from django.views.generic import TemplateView
from novels.models import Novel
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from novels.models import Novel
from django.core.paginator import Paginator
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView
from announcements.models import Announcement
from game_maturi.models import MaturiGame
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from contacts.models import Contact

class HomePageView(ListView):
    model = Novel
    template_name = 'home/home.html'
    context_object_name = 'latest_novels'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        # Asia/Tokyoに変換してから月を取得
        local_now = timezone.localtime(now)

        # 先頭の0を取り除いた月を設定
        context['now'] = str(local_now.month)

        # お知らせを取得（固定と通常を分けて取得）
        # 固定のお知らせを直近投稿順に取得
        fixed_announcements = Announcement.objects.filter(
            is_active=True,
            is_pinned=True
        ).order_by('-created_at')

        # 通常のお知らせを直近投稿順に取得（固定以外）
        normal_announcements = Announcement.objects.filter(
            is_active=True,
            is_pinned=False
        ).order_by('-created_at')

        # 残り表示可能な件数を計算
        remaining_count = 5 - fixed_announcements.count()
        if remaining_count > 0:
            normal_announcements = normal_announcements[:remaining_count]
        else:
            normal_announcements = []

        # 固定と通常のお知らせを結合
        context['announcements'] = list(fixed_announcements) + list(normal_announcements)
        
        # 現在開催中の祭りを取得
        context['current_maturi_game'] = MaturiGame.find_current_games().first()

        # 管理者用の追加情報
        if self.request.user.is_staff:
            # 未対応のお問い合わせを取得
            context['pending_contacts'] = Contact.objects.filter(
                status='pending'
            ).order_by('-created_at')

            # 非アクティブユーザーを取得
            User = get_user_model()
            context['inactive_users'] = User.objects.filter(
                is_active=False,
                email__isnull=False
            ).order_by('-date_joined')[:5]

        return context

    def get_queryset(self):
        return Novel.objects.filter(
            status='published',
            published_date__isnull=False
        ).order_by('-published_date')


def novels_list_ajax(request):
    novels_list = Novel.objects.all().order_by('-published_date')
    paginator = Paginator(novels_list, 5)  # 1ページあたり5項目を表示
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    html = render_to_string('novels/novels_list.html', {'page_obj': page_obj}, request=request)

    return JsonResponse({'html': html})    

def home_view(request):
    # 現在の月を取得
    now = timezone.now().month
    # テンプレートに渡すコンテキストに 'now' を追加
    context = {'now': now}
    return render(request, 'home/home.html', context)

from django.shortcuts import render

from django.shortcuts import render

def terms(request):
    # クエリパラメータ'signup'が'true'であるかどうかをチェック
    signup = request.GET.get('signup', 'false').lower() == 'true'
    # 'signup'変数をテンプレートに渡す
    return render(request, 'home/terms.html', {'signup': signup})

def main_view(request):
    return render(request, 'home/main.html')

# def home(request):
#     # お知らせを取得（固定表示を優先、最新2件）
#     announcements = Announcement.objects.filter(
#         is_active=True
#     ).order_by('-created_at')[:2]
    
#     # 公開済みの小説を公開日の降順で取得
#     latest_novels = Novel.objects.filter(
#         status='published',
#         published_date__isnull=False  # published_dateがNullでないものを取得
#     ).select_related(
#         'author'
#     ).order_by('-published_date')[:6]
    
#     print("\n=== デバッグ情報 ===")
#     for novel in latest_novels:
#         print(f"""
#         小説ID: {novel.id}
#         タイトル: {novel.title}
#         作者ID: {novel.author_id}
#         作者オブジェクト: {novel.author}
#         作者のID: {getattr(novel.author, 'id', 'None')}
#         作者のニックネーム: {getattr(novel.author, 'nickname', 'None')}
#         ステータス: {novel.status}
#         公開日: {novel.published_date}
#         """)
#     print("=== デバッグ終了 ===\n")
    
#     context = {
#         'latest_novels': latest_novels,
#         'announcements': announcements,
#     }
#     return render(request, 'home/home.html', context)

def announcement_detail(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id, is_active=True)
    return render(request, 'home/announcement_detail.html', {
        'announcement': announcement,
    })

def announcements_list(request):
    announcements = Announcement.objects.filter(
        is_active=True
    ).order_by('-created_at')
    return render(request, 'home/announcements_list.html', {
        'announcements': announcements,
    })

@user_passes_test(lambda u: u.is_staff)
def admin_home(request):
    # 未対応のお問い合わせを取得
    pending_contacts = Contact.objects.filter(
        status='pending'
    ).order_by('-created_at')

    # 非アクティブユーザーを取得
    User = get_user_model()
    inactive_users = User.objects.filter(
        is_active=False,
        email__isnull=False
    ).order_by('-date_joined')[:5]

    context = {
        'pending_contacts': pending_contacts,
        'inactive_users': inactive_users,
    }
    
    return render(request, 'home/admin_home.html', context)

