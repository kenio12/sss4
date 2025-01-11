import os
import ssl
from celery import Celery
from celery.schedules import crontab
from urllib.parse import urlparse

# Django設定モジュールを指定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mynovelsite.settings')

# Celeryアプリケーションの初期化
app = Celery('mynovelsite',
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
        'ssl_ca_certs': '/path/to/ca.pem',
        'ssl_certfile': '/path/to/client-cert.pem',
        'ssl_keyfile': '/path/to/client-key.pem'
    },
    redis_backend_use_ssl={
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
        'ssl_ca_certs': '/path/to/ca.pem',
        'ssl_certfile': '/path/to/client-cert.pem',
        'ssl_keyfile': '/path/to/client-key.pem'
    }
)

# Django設定モジュールから設定を読み込む
app.config_from_object('django.conf:settings', namespace='CELERY')

# タスクの自動検出
app.autodiscover_tasks()

# Redis URL設定（SSL対応）
redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
if redis_url.startswith('rediss://'):
    # URLをパースしてホスト、ポート、パスワードを取得
    parsed = urlparse(redis_url)
    redis_url = f"redis://{parsed.hostname}:{parsed.port}"
    app.conf.broker_transport_options = {
        'ssl': True,
        'password': parsed.password
    }
    app.conf.redis_backend_transport_options = {
        'ssl': True,
        'password': parsed.password
    }

# Celery設定
app.conf.update(
    broker_url=redis_url,
    result_backend=redis_url,
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

# アプリケーションのエクスポート
celery = app
