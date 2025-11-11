"""
同タイトルゲームのアクセスログミドルウェア
全てのアクセスをデータベースに記録する
"""
from django.utils import timezone
from .models import AccessLog


class SameTitleAccessLogMiddleware:
    """同タイトルゲーム関連ページへのアクセスを記録"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 同タイトルゲーム関連ページのパス
        target_paths = [
            '/game_same_title/post_or_edit/',
            '/game_same_title/novels/',
            '/game_same_title/propose_title/',
        ]

        # アクセスログ記録
        if any(request.path.startswith(path) for path in target_paths):
            AccessLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                path=request.path,
                method=request.METHOD,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                accessed_at=timezone.now()
            )

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """クライアントのIPアドレスを取得"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
