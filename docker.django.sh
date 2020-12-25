
#!/bin/sh -ex
python manage.py migrate &
python manage.py collectstatics &
gunicorn --workers=2 --bind=0.0.0.0:8000 core.wsgi:application &

# Select one of the following application gateway server commands
# gunicorn --bind=0.0.0.0:80 --forwarded-allow-ips="*" core.wsgi
# uvicorn --host=0.0.0.0 --port=8000 core.asgi:application

tail -f /dev/null