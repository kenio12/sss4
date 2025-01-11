import os
from celery import Celery
from celery.schedules import crontab

# Django設定モジュールを指定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mynovelsite.settings')

# Celeryアプリケーションの初期化
app = Celery('mynovelsite')

# REDIS_URLから接続情報を取得
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Celery設定
app.conf.update(
    broker_url=redis_url,
    result_backend='django-db',
    timezone='Asia/Tokyo',
    enable_utc=True,
    beat_schedule={
        'propose_titles_every_minute': {
            'task': 'game_same_title.tasks.propose_titles_task',
            'schedule': crontab(hour='0', minute='0'),
        },
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
