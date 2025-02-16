# release: python manage.py migrate
web: gunicorn mynovelsite.wsgi:application --log-file -
worker: celery -A mynovelsite worker -l info
beat: celery -A mynovelsite beat -l info --scheduler=celery.beat.PersistentScheduler