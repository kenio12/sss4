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

class HomePageView(TemplateView):
    template_name = 'home/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        novels_list = Novel.objects.all().order_by('-published_date')
        
        # ページネーションの設定
        paginator = Paginator(novels_list, 5)  # 1ページあたり5項目を表示
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # コンテキストにページオブジェクトを追加
        context['page_obj'] = page_obj

        # 現在の月をコンテキストに追加（文字列に変換）
        context['now'] = str(datetime.now().month)
        
        # 最新の公開済み小説を6件に制限
        context['latest_novels'] = Novel.objects.filter(
            status='published'
        ).select_related('author').order_by(
            '-published_date'
        )[:2]  # ここを4から2に変更
        
        # お知らせを取得（固定表示を優先、最新2件）
        context['announcements'] = Announcement.objects.filter(
            is_active=True
        ).order_by('-is_pinned', '-created_at')[:2]
        
        return context


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

