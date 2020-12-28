
#!/bin/sh -ex
python manage.py migrate &
python manage.py collectstatic --noinput &
gunicorn --workers=2 --bind=0.0.0.0:8000 --env DJANGO_SETTINGS_MODULE=core.settings.prod core.wsgi:application &

tail -f /dev/null