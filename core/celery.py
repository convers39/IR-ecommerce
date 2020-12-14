
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local')

app = Celery('core')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'expire-payments': {
        'task': 'order.tasks.expire_payments',
        # 'schedule': crontab(minute='0', hour='*')
        'schedule': crontab(minute='*/15')
    },
    'auto-cancel-orders': {
        'task': 'order.tasks.auto_cancel_orders',
        'schedule': crontab(minute='0', hour='*')
    }
}
# or every 30mins? crontab(minute='*/30')
app.conf.timezone = 'UTC'

# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
