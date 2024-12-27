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
        
        # 既存のコンテキスト
        context['now'] = now.strftime('%m')
        context['announcements'] = Announcement.objects.filter(
            is_pinned=True,
            is_active=True
        ).order_by('-created_at')[:3]
        
        # 現在開催中の祭りを取得（日付で判定）
        context['current_maturi_game'] = MaturiGame.objects.filter(
            start_date__lte=now,
            end_date__gte=now
        ).first()

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
            status='published'
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

def home(request):
    # お知らせを取得（固定表示を優先、最新2件）
    announcements = Announcement.objects.filter(
        is_active=True
    ).order_by('-created_at')[:2]  # 最新2件に変更
    
    latest_novels = Novel.objects.filter(
        status='published'
    ).select_related(
        'author'  # authorを事前に取得
    ).order_by('-published_date')[:6]
    
    print("\n=== デバッグ情報 ===")
    for novel in latest_novels:
        print(f"""
        小説ID: {novel.id}
        タイトル: {novel.title}
        作者ID: {novel.author_id}
        作者オブジェクト: {novel.author}
        作者のID: {getattr(novel.author, 'id', 'None')}
        作者のニックネーム: {getattr(novel.author, 'nickname', 'None')}
        ステータス: {novel.status}
        公開日: {novel.published_date}
        """)
    print("=== デバッグ終了 ===\n")
    
    context = {
        'latest_novels': latest_novels,
        'announcements': announcements,
    }
    return render(request, 'home/home.html', context)

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

