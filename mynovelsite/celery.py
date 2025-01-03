# 自動で同タイトルを提案する

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mynovelsite.settings')

app = Celery('sss4-redis',
             broker=os.environ.get('REDIS_URL'),
             backend=os.environ.get('REDIS_URL'))

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'propose_titles_every_minute': {
        'task': 'game_same_title.tasks.propose_titles_task',
        'schedule': crontab(hour='0', minute='0'),  # 毎日0時0分
    },
    'publish-scheduled-novels': {
        'task': 'game_maturi.tasks.publish_scheduled_novels',
        'schedule': 60.0,  # 10秒ごとに実行（テスト用）
    },
    'reveal-maturi-authors': {
        'task': 'game_maturi.tasks.publish_scheduled_novels',  # 同じタスクを使用
        'schedule': 60.0,  # 10秒ごとに実行
    },
}

# Redisの接続URLを環境変数から取得
broker_url = os.environ.get('REDIS_URL')
print(f"[DEBUG] Using Redis URL: {broker_url}")  # デバッグ用

# Celeryの設定を更新
app.conf.update(
    broker_url=broker_url,
    result_backend=broker_url,
    task_track_started=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tokyo',
    enable_utc=True,
    worker_log_level='DEBUG',
    beat_log_level='DEBUG',
    broker_connection_retry_on_startup=True,
    beat_max_loop_interval=60,
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
)
# SSL設定
broker_use_ssl = {
    'ssl_cert_reqs': None
}
app.conf.broker_use_ssl = broker_use_ssl
app.conf.redis_backend_use_ssl = broker_use_ssl

celery = app
