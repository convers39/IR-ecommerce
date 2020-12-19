from django.core.mail import send_mail
from django.conf import settings
from django.template import loader

from celery import shared_task
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
# app = Celery('apps.account.tasks', broker=settings.CELERY_BROKER_URL)
domain = 'http://127.0.0.1:8080'


@shared_task
def send_activation_email(to_email, username, user_id):

    serializer = Serializer(settings.SECRET_KEY, 3600*24)
    info = {'activate_user': user_id}
    token = serializer.dumps(info)  # bytes
    token = token.decode()

    activation_url = f'{domain}/account/activate/{token}'
    print(activation_url)
    subject = 'IR Ecommerce Account Activation'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = loader.render_to_string('email/activation.html', {
        'username': username,
        'activation_url': activation_url,
        'domain': domain
    })
    # html_message = f'<h1>Hi {username}, Welcome to IR Ecommerce</h1><br/>\
    # Please click this link to activate your account:<br/>\
    # <a href="{url}{token}">Activate</a><br/>\
    # This link will be valid during 24 hours.'

    send_mail(subject, message, sender, receiver, html_message=html_message)
    print(f'Email has been sent to {receiver[0]}')


# TODO: be careful on order status in fsm function, check the status
@shared_task
def send_order_email(to_email, username, order_number, order_status):
    url = f'{domain}/account/order/'
    customer = username
    if username[:6] == 'guest_':
        customer = 'Customer'
        url = f'{domain}/order/search/?email={to_email}&order_number={order_number}'
    number = order_number
    sender = settings.EMAIL_FROM

    if order_status == 'NW':
        subject = 'IR Ecommerce Order Placed'
        title = 'Thank you for your order!'
        text = f'Your order {number} has been placed, click to check your order detail and continue to make payment.'
    elif order_status == 'CF':
        subject = 'IR Ecommerce Order Payment Confirmed'
        title = 'Thank you for your business!'
        text = f'Your order {number} has been confirmed, items will be shipped in 48hrs.\
         Click here to check your order detail.'
    elif order_status == 'SP':
        subject = 'IR Ecommerce Order Shipped'
        title = 'Order has been shipped!'
        text = f'Click here to check your order detail and track the shipment.'
    elif order_status == 'CX':
        subject = 'IR Ecommerce Order Cancelled'
        title = 'Order has been cancelled!'
        text = f'Thank you for using IR Ecommerce! You can still find your order detail here within 30 days.'
    elif order_status == 'CP':
        subject = 'IR Ecommerce Order Completed'
        title = 'Your order is completed!'
        # review currently only available for registered user
        text = f'Thank you for using IR Ecommerce! Please feel free to share your thoughts with us, click to write a review.'
    else:
        subject = title = text = ''
    message = ''
    receiver = [to_email, ]
    html_message = loader.render_to_string('email/ordermail.html', {
        'customer': customer,
        'url': url,
        'domain': domain,
        'title': title,
        'text': text,
    })

    send_mail(subject, message, sender, receiver, html_message=html_message)
    print(f'Order {order_status} email has been sent to {receiver[0]}')


@shared_task
def async_send_email(subject, message, sender, recipient):
    send_mail(subject, message, sender, recipient)
