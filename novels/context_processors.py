from django.core.cache import cache
from django.db.models import Count, Q, Max
from django.contrib.auth import get_user_model
from .models import Novel, Comment
from contacts.models import Contact

# 現在使用されていない？ 要確認
# 全体の未読コメント数を計算する関数
# def get_unread_comments_count(user):
#     """ユーザーの全未読コメント数を返す"""
#     if not user.is_authenticated:
#         return 0
        
#     cache_key = f'total_unread_comments_{user.id}'
#     # キャッシュをクリアする部分を削除
#     # cache.delete(cache_key)  # この行を削除
    
#     count = Comment.objects.filter(
#         novel__author=user,  # 自分の小説
#         is_read=False,       # 未読
#         author__isnull=False # 作者不明は除外
#     ).count()
    
#     return count

# 現在使用されていない？ 要確認
# テンプレートで {{ unread_comments_count }} として使用可能
# def unread_comments_count_processor(request):
#     if request.user.is_authenticated:
#         count = get_unread_comments_count(request.user)
#         print(f"DEBUG: User: {request.user.username} (ID: {request.user.id})")
#         print(f"DEBUG: Unread Comments Count: {count}")
#         return {'unread_comments_count': count}
#     else:
#         return {'unread_comments_count': 0}

# base.htmlで使用中
# テンプレートで {% for novel in latest_unread_novels %} として使用
# 小説ごとの未読コメント数とその色を表示するために���用
def latest_unread_novels(request):
    if request.user.is_authenticated:
        novels = Novel.objects.filter(
            author=request.user,
            comments__is_read=False,
            comments__author__isnull=False
        ).annotate(
            unread_count=Count(
                'comments',
                filter=Q(
                    comments__is_read=False,
                    comments__author__isnull=False
                ) & ~Q(comments__author=request.user)
            )
        ).order_by('id').distinct()

        # unread_countが0のものを除外
        novels_with_colors = [
            {
                'id': novel.id,
                'unread_count': novel.unread_count,
                'color_index': novel.id % 10
            }
            for novel in novels
            if novel.unread_count > 0  # ここで未読数0のものを除外
        ]

        return {
            'latest_unread_novels': novels_with_colors
        }
    return {
        'latest_unread_novels': []
    }

# 管理者向けの非アクティブユーザー通知
def inactive_users_processor(request):
    """管理者向けに非アクティブユーザーの情報を提供"""
    if request.user.is_authenticated and request.user.is_superuser:
        User = get_user_model()
        inactive_users = User.objects.filter(
            is_active=False,
            email__isnull=False  # メールアドレスが設定されているユーザーのみ
        ).order_by('-date_joined')[:5]  # 最新5件まで表示
        
        return {
            'inactive_users': inactive_users
        }
    return {
        'inactive_users': []
    }

# 管理者向けのお問い合わせ通知を追加
def pending_contacts_processor(request):
    """管理者向けに未対応のお問い合わせ情報を提供"""
    if request.user.is_authenticated and request.user.is_staff:
        pending_contacts = Contact.objects.filter(
            status='pending'  # is_resolvedの代わりにstatusを使用
        ).order_by('-created_at')
        
        return {
            'pending_contacts': pending_contacts
        }
    return {
        'pending_contacts': []
    }

