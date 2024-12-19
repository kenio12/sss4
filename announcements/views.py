from django.shortcuts import render, get_object_or_404
from .models import Announcement

def announcement_list(request):
    """お知らせ一覧を表示"""
    announcements = Announcement.objects.filter(
        is_active=True
    ).order_by('-is_pinned', '-created_at')
    return render(request, 'announcements/announcement_list.html', {
        'announcements': announcements
    })

def announcement_detail(request, pk):
    """お知らせ詳細を表示"""
    announcement = get_object_or_404(Announcement, pk=pk, is_active=True)
    
    # 全てのお知らせを取得（現在の記事も含む）
    announcements = Announcement.objects.filter(
        is_active=True
    ).order_by(
        '-is_pinned',
        '-created_at'
    )
    
    return render(request, 'announcements/announcement_detail.html', {
        'announcement': announcement,
        'announcements': announcements,
        'user': request.user,
    })

def get_latest_announcements():
    """ホーム画面用の最新お知らせを2件取得"""
    return Announcement.objects.filter(
        is_active=True
    ).order_by('-created_at')[:2]
