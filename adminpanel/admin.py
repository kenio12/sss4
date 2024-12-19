from django.contrib import admin
from game_maturi.models import MaturiGame, Phrase  # 必要なモデルをインポート
from django.contrib.auth import get_user_model

from django.contrib.admin.widgets import FilteredSelectMultiple

class MaturiGameAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'maturi_start_date', 'entry_start_date', 'entry_end_date', 'start_date', 'end_date', 'prediction_start_date', 'prediction_end_date', 'maturi_end_date', 'get_maturi_novels_titles')
    search_fields = ('title',)
    filter_horizontal = ('entrants', 'phrases')  # phrasesも追加

    # フィールドセットを定義して、フィールドの順序と表示方法を制御
    fieldsets = (
        (None, {
            'fields': ('title', 'description')
        }),
        ('イベント期間', {
            'fields': ('maturi_start_date', 'maturi_end_date')
        }),
        ('エントリー期間', {
            'fields': ('entry_start_date', 'entry_end_date')
        }),
        ('執筆期間', {
            'fields': ('start_date', 'end_date')
        }),
        ('予想期間', {
            'fields': ('prediction_start_date', 'prediction_end_date')
        }),
        ('参加者', {
            'fields': ('entrants',)
        }),
        ('語句', {  # 新しいセクションを追加
            'fields': ('phrases',)
        }),
        ('祭りの小説', {
            'fields': ('maturi_novels',)
        }),
    )

    def get_maturi_novels_titles(self, obj):
        return ", ".join([novel.title for novel in obj.maturi_novels.all()])
    get_maturi_novels_titles.short_description = '祭りの小説タイトル'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ["entrants", "phrases", "maturi_novels"]:
            kwargs['widget'] = FilteredSelectMultiple(
                verbose_name=db_field.verbose_name,
                is_stacked=False
            )
            if db_field.name == "entrants":
                kwargs['widget'].attrs.update({
                    'verbose_name_available': 'まだエントリーしてない人',
                    'verbose_name_chosen': 'エントリーしている人'
                })
            elif db_field.name == "phrases":
                kwargs['widget'].attrs.update({
                    'verbose_name_available': '使用可能な語句',
                    'verbose_name_chosen': '選択された語句'
                })
            elif db_field.name == "maturi_novels":
                kwargs['widget'].attrs.update({
                    'verbose_name_available': '使用可能な小説',
                    'verbose_name_chosen': '選択された小説'
                })
        return super().formfield_for_manytomany(db_field, request, **kwargs)

# ここでMaturiGameモデルを一度だけ登録
admin.site.register(MaturiGame, MaturiGameAdmin)

# Phraseモデルもアドミンに登録
class PhraseAdmin(admin.ModelAdmin):
    list_display = ('text',)
    search_fields = ('text',)

admin.site.register(Phrase, PhraseAdmin)
