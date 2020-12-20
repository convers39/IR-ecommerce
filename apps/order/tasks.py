
from core.celery import app
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from datetime import timezone

from order.models import Payment, Order

import logging

logger = logging.getLogger(__name__)

# @app.task(name='order.mark_expired_payments')


@app.task
def expire_payments():
    payments = Payment.objects.filter(status='PD').all()
    for payment in payments:
        if payment.is_expired():
            payment.expire_payment()
            payment.save()


# @app.task(name='order.mark_auto_canceled_orders')
@app.task
def auto_cancel_orders():
    # payments = Payment.objects.filter(status__in=['EX','PD']).all()
    orders = Order.objects.filter(status='NW').select_related('payment')
    for order in orders:
        if order.payment.is_auto_canceled():
            order.auto_cancel()
            order.save()
            order.restore_product_stock()


@app.task
def auto_complete_orders():
    orders = Order.objects.filter(status__in=['SP', 'RT'])
    for order in orders:
        if order.is_completed():
            order.complete()
            order.save()


def create_one_time_task():
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='30',
        hour='*',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone=timezone.utc
    )
    PeriodicTask.objects.create(
        crontab=schedule,
        name='Order expiration task',
        task='order.tasks.expire_payments',
        one_off=True,
    )
    logger.info('one time task created')
    print('one time task created')
