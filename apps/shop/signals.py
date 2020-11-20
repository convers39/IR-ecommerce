from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.postgres.search import SearchVector

from .models import ProductSKU


@receiver(post_save, sender=ProductSKU)
def update_search_vector(sender, instance, **kwargs):
    instance.search_vector = (
        SearchVector('name', weight='A')
        + SearchVector('detail', weight='B')
        + SearchVector('summary', weight='C')
    )
    print('search vector updated!')
