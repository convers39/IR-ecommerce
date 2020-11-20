from django.contrib.postgres.search import SearchVector

from celery import shared_task

# from .models import ProductSKU

# app = Celery('apps.account.tasks', broker=settings.CELERY_BROKER_URL)


# @shared_task
# def update_search_vector(obj_id):
# product = ProductSKU.objects.get(id=obj_id)
# product.search_vector = (
#     SearchVector('name', weight='A')
#     + SearchVector('detail', weight='B')
#     + SearchVector('summary', weight='C')
# )
# print('search vector updated!')
