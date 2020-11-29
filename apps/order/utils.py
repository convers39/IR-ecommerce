import random
import string
from datetime import datetime


def random_string_generator(size=10, chars=string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def generate_order_number():
    order_number = random_string_generator()

    # Klass = instance.__class__

    # qs_exists = Klass.objects.filter(number=order_number).exists()
    # if qs_exists:
    #     return generate_order_number(instance)
    return datetime.now().strftime('%Y%m%d%H%M') + order_number
