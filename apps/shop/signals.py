from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.postgres.search import SearchVector

from .models import ProductSKU
from .tasks import update_search_vector


@receiver(post_save, sender=ProductSKU)
def update_sku(sender, instance, **kwargs):
    update_search_vector.delay(instance.id)
