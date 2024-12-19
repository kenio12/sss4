# Dockerfile
FROM python:3.8

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt

# Whitenoiseをインストール
RUN pip install whitenoise

# django-widget-tweaksをインストール
RUN pip install django-widget-tweaks

RUN apt-get update && apt-get install -y postgresql-client

COPY . /code/
COPY custom_timezone.py /app/custom_timezone.py
CMD gunicorn mynovelsite.wsgi:application --bind 0.0.0.0:${PORT:-8000}

# cronのインストール
RUN apt-get update && apt-get install -y cron

# cronジョブの設定
COPY crontab /etc/cron.d/maturi-cron
RUN chmod 0644 /etc/cron.d/maturi-cron
RUN crontab /etc/cron.d/maturi-cron
