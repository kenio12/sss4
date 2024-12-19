from django.contrib import admin
from .models import Novel
from .models import Comment  # ここで、.modelsはCommentモデルが定義されている場所によって変わります

class NovelAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_date', 'status', 'genre', 'word_count', 'is_same_title_game', 'created_at', 'updated_at')  # 表示したい項目を追加
    list_filter = ('status', 'genre', 'is_same_title_game', 'published_date')  # フィルターに使いたい項目を追加
    search_fields = ('title', 'author__username', 'content')  # 検索に使いたい項目を追加

admin.site.register(Novel, NovelAdmin)  # NovelモデルをAdminサイトに登録



class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'content', 'is_read')  # 'text'を'content'に修正
# Commentモデルをカスタムの管理オプションで管理画面に登録
admin.site.register(Comment, CommentAdmin)
