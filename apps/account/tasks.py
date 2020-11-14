
from django.core.mail import send_mail
from django.conf import settings

from celery import shared_task

# app = Celery('apps.account.tasks', broker=settings.CELERY_BROKER_URL)


@shared_task
def send_activation_email(to_email, username, token):
    url = 'http://127.0.0.1:8080/account/activate/'
    subject = 'IR Ecommerce Account Activation'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = f'<h1>Hi {username}, Welcome to IR Ecommerce</h1><br/>\
    Please click this link to activate your account:<br/>\
    <a href="{url}{token}">Activate</a><br/>\
    This link will be valid during 24 hours.'

    send_mail(subject, message, sender, receiver, html_message=html_message)
    print(f'Email has been sent to {receiver[0]}')
