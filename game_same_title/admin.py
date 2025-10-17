from django.contrib import admin
from .models import TitleProposal, MonthlySameTitleInfo, PendingNotification

class TitleProposalAdmin(admin.ModelAdmin):
    list_display = ('title', 'proposer', 'proposed_at', 'proposal_month')  # proposed_atを追加
    list_filter = ('proposed_at', 'proposal_month',)  # proposed_atを追加
    search_fields = ('title', 'proposer__username')

class MonthlySameTitleInfoAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_date', 'month','novel_id')  # 表示するフィールド
    list_filter = ('month',)  # フィルターに使うフィールド
    search_fields = ('title', 'author')  # 検索に使うフィールド

class PendingNotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'novel', 'rank', 'created_at', 'sent_at', 'is_sent')
    list_filter = ('notification_type', 'is_sent', 'created_at', 'sent_at')
    search_fields = ('novel__title',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

admin.site.register(TitleProposal, TitleProposalAdmin)
admin.site.register(MonthlySameTitleInfo, MonthlySameTitleInfoAdmin)
admin.site.register(PendingNotification, PendingNotificationAdmin)