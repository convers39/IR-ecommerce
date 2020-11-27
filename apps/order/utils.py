import random
import string


def random_string_generator(size=10, chars=string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def generate_order_number(instance):
    order_number = random_string_generator()

    Klass = instance.__class__

    qs_exists = Klass.objects.filter(booking_id=order_number).exists()
    if qs_exists:
        return generate_order_number(instance)
    return order_number
