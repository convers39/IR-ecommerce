
from core.celery import app

from order.models import Payment, Order


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


@app.task
def complete_orders():
    orders = Order.objects.filter(
        status__in=['SP', 'RT']).select_related('payment')
    for order in orders:
        if order.is_completed():
            order.complete()
            order.save()
