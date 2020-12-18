from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def merge_shopping_cart(sender, user, request,  **kwargs):
    """
    Check if there is items in shopping cart before login,
    merge guest shopping cart to user and remove cookie
    """
    return
