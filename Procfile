release: python manage.py migrate
web: gunicorn mynovelsite.wsgi:application --log-file -
worker: celery -A sss4-redis worker -l info
beat: celery -A sss4-redis beat -l info