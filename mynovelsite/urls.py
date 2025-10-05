from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # 名前空間 'accounts' は accounts/urls.py 内で定義
    path('', include('home.urls')),  # home アプリケーション
    path('novels/', include('novels.urls')),  # novels アプリケーション
    path('games/', include('games.urls')),  # 'games.urls'はgamesアプリケーションのurls.pyファイルを指す
    path('game_same_title/', include(('game_same_title.urls', 'game_same_title'), namespace='game_same_title')),
    path('adminpanel/', include('adminpanel.urls')),  # adminpanelのURLを追加,
    path('game_maturi/', include('game_maturi.urls', namespace='game_maturi')),   
    path('announcements/', include('announcements.urls')),
    # 問い合わせ関連のURLを追加
    path('contacts/', include(('contacts.urls', 'contacts'), namespace='contacts')),
]
# if settings.DEBUG:
#     import debug_toolbar
    # urlpatterns = [
    #     path('__debug__/', include(debug_toolbar.urls)),
    # ] + urlpatterns