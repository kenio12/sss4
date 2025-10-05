from django.urls import path
from . import views

app_name = 'game_same_title'
urlpatterns = [
    path('same_title/', views.same_title, name='same_title'),
    path('same_title/page/<int:page>/', views.same_title, name='same_title_paginated'),  # ページネーション用のURL
    path('proposals/create/', views.create_title_proposal, name='create_title_proposal'),
    path('entry/', views.entry_for_same_title, name='same_title_entry'),
    path('post_or_edit/', views.post_or_edit_same_title, name='post_or_edit_same_title'),
    path('post_or_edit/<int:novel_id>/', views.post_or_edit_same_title, name='post_or_edit_same_title_with_id'),
    path('auto_save/', views.auto_save, name='auto_save'),  # auto_saveのURLを追加
    path('all_same_title_novels/', views.all_same_title_novels, name='all_same_title_novels'),
    path('all_same_title_novels/page/<int:page>/', views.all_same_title_novels, name='all_same_title_novels_paginated'),
]