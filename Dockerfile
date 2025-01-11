# Dockerfile
FROM python:3.9

ENV PYTHONUNBUFFERED 1

# 非rootユーザーを作成
RUN useradd -m -s /bin/bash celery_user

# 必要なディレクトリを作成
RUN mkdir /code
WORKDIR /code

# 依存関係のインストール
COPY requirements.txt /code/
RUN pip install -r requirements.txt
RUN pip install whitenoise django-widget-tweaks

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    postgresql-client \
    cron \
    && rm -rf /var/lib/apt/lists/*

# アプリケーションコードのコピー
COPY . /code/
COPY custom_timezone.py /app/custom_timezone.py

# cronの設定
COPY crontab /etc/cron.d/maturi-cron
RUN chmod 0644 /etc/cron.d/maturi-cron
RUN crontab /etc/cron.d/maturi-cron

# 所有権とパーミッションの設定
RUN chown -R celery_user:celery_user /code /app
RUN chmod -R 755 /code /app

# 非rootユーザーに切り替え
USER celery_user

# アプリケーションの起動
CMD gunicorn mynovelsite.wsgi:application --bind 0.0.0.0:${PORT:-8000}
