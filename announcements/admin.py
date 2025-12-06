from django.contrib import admin
from django import forms
from .models import Announcement
from accounts.models import User


class AnnouncementAdminForm(forms.ModelForm):
    """作者選択でニックネームを表示するカスタムフォーム"""
    created_by = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True),
        label='作成者',
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ニックネームで表示するようにlabel_from_instanceをオーバーライド
        self.fields['created_by'].label_from_instance = lambda obj: obj.nickname or obj.username

    class Meta:
        model = Announcement
        fields = '__all__'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    form = AnnouncementAdminForm
    list_display = ('title', 'is_pinned', 'created_at', 'is_active')
    list_editable = ('is_pinned', 'is_active')
    ordering = ('-is_pinned', '-created_at')

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_staff
