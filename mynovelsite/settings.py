"""
Django settings for mynovelsite project.

Generated by 'django-admin startproject' using Django 3.2.24.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os  # osモジュールをインポート
from pathlib import Path
from dotenv import load_dotenv
import environ
import custom_timezone
import django.utils.timezone
from freezegun import freeze_time
import datetime

# .envファイルを読み込む（これ追加）
load_dotenv()

env = environ.Env()
environ.Env.read_env()  # .envファイルから環境変数を読み込む

django.utils.timezone = custom_timezone.custom_timezone

BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-secret-key-here')


# Debug設定
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'novels',  # novelsアプリケーションを追加
    'accounts',  # accountsアプリケーションを追加
    'home',  # homeアプリケーションを追加
    'django.contrib.humanize',
    'django_extensions',
    'games',
    'game_same_title',
    'adminpanel',
    'game_maturi',
    'widget_tweaks',  # この行を追加
    'novel_site',  # ← これを追加
    'announcements.apps.AnnouncementsConfig',
    'django_celery_beat',  # これを追加
    'contacts.apps.ContactsConfig',  # これを追加
    'django_celery_results',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ここに移動
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.RedirectMiddleware',  # しいスで追加
]

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'


ROOT_URLCONF = 'mynovelsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'novels.context_processors.latest_unread_novels',  # これだけ残す
            ],
        },
    },
]

WSGI_APPLICATION = 'mynovelsite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# 前々の短編小説会のデータも取り込むぜ！

import dj_database_url


# 環境変数から実行環境を取得（デフォルトは開発環境）
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    # Herokuの環境であれば、DATABASE_URLから設定を上書き
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
    }
else:
    # 開発環境のデータベース設定
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DEV_POSTGRES_DB', 'novel_site_db'),
            'USER': os.getenv('DEV_POSTGRES_USER', 'postgres'),
            'PASSWORD': os.getenv('DEV_POSTGRES_PASSWORD', 'your_password_here'),
            'HOST': os.getenv('DEV_POSTGRES_HOST', 'db'),
            'PORT': os.getenv('DEV_POSTGRES_PORT', '5432'),
        },
        'old_db': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('OLD_POSTGRES_DB', 'old_sss_novels'),
            'USER': os.getenv('OLD_POSTGRES_USER', 'postgres'),
            'PASSWORD': os.getenv('OLD_POSTGRES_PASSWORD', 'your_password_here'),
            'HOST': os.getenv('OLD_POSTGRES_HOST', 'old_db'),
            'PORT': os.getenv('OLD_POSTGRES_PORT', '5432'),
        }
    }

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'accounts.authentication.EmailOrNicknameBackend',  # カスタム認証バックエンド
    'django.contrib.auth.backends.ModelBackend',  # デフォルトの認証バックエンド
]

AUTH_USER_MODEL = 'accounts.User'

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'ja'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoiseの設定を変更
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'  # ここを変更

# WhiteNoiseのミドルウェア設定
if not DEBUG:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# 静的ファイルのディレクトリ設定
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# staticfilesディレクトリが存在することを確認
os.makedirs(os.path.join(BASE_DIR, 'static'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'staticfiles'), exist_ok=True)

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email configuration for production
EMAIL_BACKEND = 'utils.mail_backends.CustomEmailBackend'  # カスタムSMTPバックエンドを使用
EMAIL_HOST = 'smtp.gmail.com'  # メールサーバーのホスト名
EMAIL_PORT = 587  # メールサーバーのポート（TLSを使用する場合）
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'your_email@example.com')  # 環境変数からメールサーバーのユーザー名を取得
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'your_email_password_here')  # 環境変数からメールサーバーのパスワードを取得
EMAIL_USE_TLS = True  # TLSを用する
# EMAIL_USE_SSL = False  # SSLを使用しない（TLSとSSLの両方をTrueにすることはできません）

# メールで使用するベースURLの設定
# 開発環境では 'http://localhost:8000' など、本番環境では実際のドメインを設定
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')

# HTTPS環境でのみセッションCookieを送信
SESSION_COOKIE_SECURE = True
# ブラウザがJavaScriptを通じてセションCookieにアクセスするのを防ぐ
SESSION_COOKIE_HTTPONLY = True
# セッションCookieを送信するドメインを指定（必要に応じて）
# SESSION_COOKIE_DOMAIN = 'yourdomain.com'

# パスワードリセットトークンの有効期限を1分間に設定
PASSWORD_RESET_TIMEOUT = 300  # 秒単位で指定

# Docker環境での設定
import socket
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[:-1] + "1" for ip in ips]
# または、よりシンプルに設定する場合
# INTERNAL_IPS = ['127.0.0.1', '192.168.10.1']  # 192.168.10.1はDockerホストのIPアドレスの例

# Celery Configuration
if ENVIRONMENT == 'production':
    # 本番環境設定
    CELERY_BROKER_URL = 'django://'
    CELERY_RESULT_BACKEND = 'django-db'
else:
    # 開発環境設定
    # Redis関連の環境変数をクリア
    for key in ['REDIS_URL', 'CELERY_BROKER_URL', 'CELERY_RESULT_BACKEND']:
        if key in os.environ:
            del os.environ[key]
    
    # PostgreSQLを使用
    CELERY_BROKER_URL = 'django://'
    CELERY_RESULT_BACKEND = 'django-db'

# 共通のCelery設定
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tokyo'
CELERY_ENABLE_UTC = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# デバッグ用の設定
print(f"[DEBUG] Environment: {ENVIRONMENT}")
print(f"[DEBUG] CELERY_BROKER_URL: {CELERY_BROKER_URL}")
print(f"[DEBUG] CELERY_RESULT_BACKEND: {CELERY_RESULT_BACKEND}")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "local": {
            "format": '%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d %(message)s'
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "local"
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": True
    },
    "loggers": {
        'django': {
           'handlers': ['console'],
           'level': 'DEBUG',  # INFOからDEBUGに変更
           'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'game_same_title.views': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'game_maturi.views': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')

# # 開発環境でのみ日付を固定
# if DEBUG:
#     freeze_time("2024-12-16").start()

# セキュリティ設定
# 本番環境でのみ有効にする設定
if ENVIRONMENT == 'production':
    # HTTPS設定
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # CSRFとセッションのセキュリティ
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # HSTSの設定
    SECURE_HSTS_SECONDS = 31536000  # 1年
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    # 開発環境では無効
    SECURE_SSL_REDIRECT = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True  # これは開発環境でも有効にしておく