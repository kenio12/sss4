from django.contrib import admin
from .models import SameTitleEntry, TitleProposal, MonthlySameTitleInfo

class SameTitleEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'created_at')
    list_filter = ('month',)
    search_fields = ('user__username',)

class TitleProposalAdmin(admin.ModelAdmin):
    list_display = ('title', 'proposer', 'proposed_at', 'proposal_month')  # proposed_atを追加
    list_filter = ('proposed_at', 'proposal_month',)  # proposed_atを追加
    search_fields = ('title', 'proposer__username')

class MonthlySameTitleInfoAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_date', 'month','novel_id')  # 表示するフィールド
    list_filter = ('month',)  # フィルターに使うフィールド
    search_fields = ('title', 'author')  # 検索に使うフィールド

admin.site.register(SameTitleEntry, SameTitleEntryAdmin)
admin.site.register(TitleProposal, TitleProposalAdmin)
admin.site.register(MonthlySameTitleInfo, MonthlySameTitleInfoAdmin)