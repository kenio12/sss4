# 自動で同タイトルを提案する

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mynovelsite.settings')

# 開発環境では強制的にローカルのRedisを使用
if os.environ.get('ENVIRONMENT') != 'production':
    # 環境変数を完全にクリア
    for key in ['REDIS_URL', 'CELERY_BROKER_URL', 'CELERY_RESULT_BACKEND']:
        if key in os.environ:
            del os.environ[key]
    
    # Django設定を上書き
    from django.conf import settings
    settings.CELERY_BROKER_URL = 'redis://redis:6379/0'
    settings.CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
    print(f"[DEBUG] Forced local Redis in development")

# Celeryアプリケーションの初期化
app = Celery('mynovelsite')

# Django設定モジュールを指定
app.config_from_object('django.conf:settings', namespace='CELERY')

# 開発環境の場合は設定を強制
if os.environ.get('ENVIRONMENT') != 'production':
    app.conf.broker_url = 'redis://redis:6379/0'
    app.conf.result_backend = 'redis://redis:6379/0'
    app.conf.broker_transport_options = {}
    app.conf.redis_backend_transport_options = {}

print(f"[DEBUG] Final broker_url: {app.conf.broker_url}")
print(f"[DEBUG] Final result_backend: {app.conf.result_backend}")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'propose_titles_every_minute': {
        'task': 'game_same_title.tasks.propose_titles_task',
        'schedule': crontab(hour='0', minute='0'),  # 毎日0時0分
    },
    'publish-scheduled-novels': {
        'task': 'game_maturi.tasks.publish_scheduled_novels',
        'schedule': crontab(hour='0', minute='0'),  # 毎日0時0分
    },
    'reveal-maturi-authors': {
        'task': 'game_maturi.tasks.reveal_maturi_authors',  # 新しい分離したタスク
        'schedule': crontab(hour='0', minute='0'),  # 毎日0時0分
    },
}

# Redis接続設定を修正
app.conf.broker_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
app.conf.result_backend = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

# Upstash Redis用のSSL設定
if 'rediss://' in app.conf.broker_url:
    app.conf.broker_transport_options = {
        'ssl_cert_reqs': None,
        'ssl_ca_certs': None
    }
    app.conf.redis_backend_transport_options = {
        'ssl_cert_reqs': None,
        'ssl_ca_certs': None
    }

# タイムゾーン設定を追加
app.conf.timezone = 'Asia/Tokyo'
app.conf.enable_utc = True

celery = app
