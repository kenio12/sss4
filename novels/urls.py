from django.urls import path
from . import views
from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView

app_name = 'novels'

urlpatterns = [
    # 小説関連
        # ページネーション
    path('', RedirectView.as_view(url=reverse_lazy('novels:novels_paginated')), name='index'),
    path('novels-paginated/', views.novels_paginated, name='novels_paginated'),
    path('post/', views.post_or_edit_novel, name='post_novel'),
    path('<int:novel_id>/edit/', views.post_or_edit_novel, name='edit_novel'),
    path('<int:novel_id>/', views.novel_detail, name='novel_detail'),
    path('<int:novel_id>/delete/', views.delete_novel, name='delete'),
    path('<int:novel_id>/like/', views.like_novel, name='like_novel'),
    path('<int:novel_id>/unpublish/', views.unpublish_novel, name='unpublish_novel'),
    path('auto_save/', views.auto_save, name='auto_save'),
    
    # コメント投稿用のURLパターンを追加
    path('<int:novel_id>/comment/', views.post_comment, name='post_comment'),
    
    # 削除：古いコメント関連のパス
    # path('unread-comments-count/<int:novel_id>/', views.unread_comments_count, name='unread-comments-count'),
    # path('toggle-comment-read/<int:comment_id>/', views.toggle_comment_read_status, name='toggle_comment_read_status'),
    # path('mark-comments-as-read/', views.mark_comments_as_read, name='mark_comments_as_read'),
    # path('comments/<int:comment_id>/', views.comment_detail, name='comment_detail'),
    # path('api/latest-unread-novel-id/', views.latest_unread_novel_id, name='latest_unread_novel_id'),
    # path('api/novels/<int:novel_id>/unread-comment-page/', views.unread_comment_page, name='unread_comment_page'),
    # path('api/unread-comments/', views.unread_comments, name='unread_comments'),
    # path('check-unread-comments/<int:novel_id>/', views.check_unread_comments, name='check_unread_comments'),
    # path('<int:novel_id>/load_more_comments/', views.load_more_comments, name='load_more_comments'),
    path('comments/<int:comment_id>/toggle-read/', views.toggle_comment_read_status, name='toggle_comment_read'),
]
