from django.urls import path
from . import views

app_name = 'game_same_title'
urlpatterns = [
    path('same_title/', views.same_title, name='same_title'),
    path('same_title/page/<int:page>/', views.same_title, name='same_title_paginated'),  # ページネーション用のURL
    path('proposals/create/', views.create_title_proposal, name='create_title_proposal'),
    # エントリー制廃止により entry_for_same_title URL を削除
    path('post_or_edit/', views.post_or_edit_same_title, name='post_or_edit_same_title'),
    path('post_or_edit/<int:novel_id>/', views.post_or_edit_same_title, name='post_or_edit_same_title_with_id'),
    path('auto_save/', views.auto_save, name='auto_save'),  # auto_saveのURLを追加
    path('all_same_title_novels/', views.all_same_title_novels, name='all_same_title_novels'),
    path('all_same_title_novels/page/<int:page>/', views.all_same_title_novels, name='all_same_title_novels_paginated'),
    # 来月提案の編集・削除
    path('proposals/<int:proposal_id>/edit/', views.edit_title_proposal, name='edit_title_proposal'),
    path('proposals/<int:proposal_id>/delete/', views.delete_title_proposal, name='delete_title_proposal'),
]