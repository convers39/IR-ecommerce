
import os

from celery import Celery
from celery.schedules import crontab

os.environ["DJANGO_SETTINGS_MODULE"] = os.getenv('DJANGO_SETTINGS_MODULE')
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.prod')

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
    },
    'auto-complete-orders': {
        'task': 'order.tasks.auto_complete_orders',
        'schedule': crontab(minute='0', hour='0')
    },
    'close-inactive-account': {
        'task': 'account.tasks.close_inactive_account',
        'schedule': crontab(minute='0', hour='*')
    }
}
# or every 30mins? crontab(minute='*/30')
app.conf.timezone = 'UTC'
