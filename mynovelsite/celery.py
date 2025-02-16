"""
現在の問題点：
1. タスクの戻り値が常に1になってしまう問題が未解決
2. タスクのスケジュール（毎日0時0分）は正しく設定されているが、実行結果の確認が必要
3. 本番環境（Heroku）でのタスク実行状況の確認が必要

注意：上記の問題により、必要な場合は手動で実行する必要があります。
"""

import os
from celery import Celery
from celery.schedules import crontab

# Django設定モジュールを指定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mynovelsite.settings')

# Celeryアプリケーションの初期化
app = Celery('mynovelsite')

# REDIS_URLから接続情報を取得
redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

# SSL設定を修正
redis_options = {
    'ssl_cert_reqs': None
}  # 'ssl': Trueを削除

# Celery設定
app.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL', redis_url),
    broker_use_ssl=redis_options,  # 修正したSSL設定を使用
    result_backend='django-db',
    timezone='Asia/Tokyo',
    enable_utc=True,
    beat_schedule={
        'publish-scheduled-novels': {
            'task': 'game_maturi.tasks.publish_scheduled_novels',
            'schedule': crontab(hour='0', minute='0'),
        },
        'reveal-maturi-authors': {
            'task': 'game_maturi.tasks.reveal_maturi_authors',
            'schedule': crontab(hour='0', minute='0'),
        },
    }
)

# Django設定モジュールから設定を読み込む
app.config_from_object('django.conf:settings', namespace='CELERY')

# タスクの自動検出
app.autodiscover_tasks()

# アプリケーションのエクスポート
celery = app
