from django_ses.signals import bounce_received, delivery_received, complaint_received
from django.dispatch import receiver


@receiver(bounce_received)
def bounce_handler(sender, *args, **kwargs):
    print("This is bounce email object")
    print(kwargs.get('mail_obj'))


@receiver(delivery_received)
def delivery_handler(sender, *args, **kwargs):
    print("This is delivery email object")
    print(kwargs.get('mail_obj'))


@receiver(complaint_received)
def complaint_handler(sender, *args, **kwargs):
    print("This is complaint email object")
    print(kwargs.get('mail_obj'))
