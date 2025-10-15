#!/usr/bin/env python
"""
既存ユーザーのemail_confirmedを更新するスクリプト

実メールアドレス（@example.com以外、user_で始まらない）: email_confirmed=True
仮メールアドレス（@example.com、user_で始まる）: email_confirmed=False
"""
import os
import sys
import django

# Djangoプロジェクトのパス設定
sys.path.insert(0, '/Users/keikeikun2/ai-try-programing/novel_site')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User

def update_email_confirmed():
    """既存ユーザーのemail_confirmedを更新"""

    # 実メールアドレスのユーザー（@example.com以外、user_で始まらない）
    real_email_users = User.objects.exclude(
        email__icontains='@example.com'
    ).exclude(
        email__startswith='user_'
    )

    # 仮メールアドレスのユーザー（@example.comまたはuser_で始まる）
    fake_email_users = User.objects.filter(
        email__icontains='@example.com'
    ) | User.objects.filter(
        email__startswith='user_'
    )

    print(f'実メールアドレスユーザー: {real_email_users.count()}人')
    print(f'仮メールアドレスユーザー: {fake_email_users.count()}人')

    # 実メールアドレスのユーザーをemail_confirmed=Trueに更新
    real_updated = real_email_users.update(email_confirmed=True)
    print(f'実メールアドレスユーザー更新完了: {real_updated}人')

    # 仮メールアドレスのユーザーをemail_confirmed=Falseに更新
    fake_updated = fake_email_users.update(email_confirmed=False)
    print(f'仮メールアドレスユーザー更新完了: {fake_updated}人')

    print('更新完了！')

if __name__ == '__main__':
    update_email_confirmed()
