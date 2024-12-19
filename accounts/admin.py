from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User  # ここでモデルをインポート

class UserAdmin(BaseUserAdmin):
    # ユーザーの詳細画面のフィールドセットをカスタマイズ
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('nickname',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('nickname', 'email')  # ニックネームを一番上に表示
    search_fields = ('email', 'nickname')  # 検索フィールドに追加

admin.site.register(User, UserAdmin)  # UserモデルをカスタムAdminで登録

