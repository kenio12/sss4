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
# 小説ごとの未読コメント数とその色を表示するために用
def latest_unread_novels(request):
    try:
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

            # デバッグ用のログ
            print(f"Debug - User: {request.user.username}")
            print(f"Debug - Novels query: {novels.query}")

            novels_with_colors = [
                {
                    'id': novel.id,
                    'unread_count': novel.unread_count,
                    'color_index': novel.id % 10
                }
                for novel in novels
                if novel.unread_count > 0
            ]

            # デバッグ用のログ
            print(f"Debug - Novels with colors: {novels_with_colors}")

            return {
                'latest_unread_novels': novels_with_colors
            }
    except Exception as e:
        # エラーが発生した場合でもサイトが動作するように
        print(f"Error in latest_unread_novels: {str(e)}")
        return {
            'latest_unread_novels': []
        }
    
    return {
        'latest_unread_novels': []
    }

