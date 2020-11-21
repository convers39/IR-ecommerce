from django.contrib.postgres.search import SearchVector
from celery import shared_task
from .models import ProductSKU


@shared_task
def update_search_vector(obj_id):
    product = ProductSKU.objects.get(id=obj_id)
    product.search_vector = (
        SearchVector('name', weight='A')
        + SearchVector('detail', weight='B')
        + SearchVector('summary', weight='C')
    )
    print('search vector updated!')
