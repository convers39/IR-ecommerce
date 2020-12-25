#!/bin/sh -ex
celery -A core worker -l info &
celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler &
# celery -A core beat -l info &
tail -f /dev/null