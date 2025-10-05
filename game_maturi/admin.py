from django.contrib import admin
from .models import GamePrediction

# GamePrediction の管理画面設定
class GamePredictionAdmin(admin.ModelAdmin):
    list_display = ('maturi_game', 'novel', 'predictor', 'predicted_author', 'created_at')
    list_filter = ('maturi_game', 'predictor', 'predicted_author')
    search_fields = ('predictor__username', 'predicted_author__username', 'novel__title')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

# 新しいモデルだけを登録
admin.site.register(GamePrediction, GamePredictionAdmin)