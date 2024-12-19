from django.urls import path, include  # `include`を忘れずにインポートする
from . import views

app_name = 'games'  # ここでアプリケーションの名前空間を設定する

urlpatterns = [
    path('game_top/', views.game_top, name='game_top'),
]