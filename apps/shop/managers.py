from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import (
    SearchQuery, SearchRank, SearchVector, TrigramSimilarity,
)
from django.db.models import Manager, Q, Avg
from django.db.models.expressions import ExpressionWrapper
from django.db.models.fields import BooleanField

from datetime import datetime, timedelta, timezone

from django_redis import get_redis_connection


class SKUManager(Manager):
    def get_queryset(self):
        """
        Only return products on the shelf, prefetch all images,to avoid duplicate queries.
        """
        return super().get_queryset().filter(status='ON').prefetch_related('images')

    def get_related_products(self, obj):
        """
        Return a queryset containing most popular and recent products
        in the same category, exluding current product.
        """
        category = obj.category
        current = obj.id
        queryset = self.get_queryset().filter(category=category)\
            .exclude(id=current).order_by('sales', '-created_at')
        return queryset

    def filter_category_products(self, category, queryset):
        """
        Filter a queryset with a category, category can be parent category.
        """
        if category.get_descendant_count() > 0:
            queryset = queryset.filter(category__in=category.get_descendants())
        else:
            queryset = queryset.filter(category=category)
        return queryset

    def filter_wishlisted_products(self, user_id, queryset):
        conn = get_redis_connection('cart')
        wishlisted = conn.smembers(f'wish_{user_id}')
        wishlisted = [int(i) for i in wishlisted]

        queryset = queryset.annotate(wishlist=ExpressionWrapper(
            Q(id__in=wishlisted),
            output_field=BooleanField(),
        ),)
        # NOTE: alternative solution:
        # queryset = queryset.annotate(wishlist=Case(
        #     When(id__in=wishlisted, then=Value(True)),
        #     default=Value(False),
        #     output_field=BooleanField(),
        # ))
        return queryset

    def get_products_with_review(self):
        """
        Return a LIST of products sku which has a customer review.
        """
        products = self.get_queryset().prefetch_related(*
                                                        ['order_products', 'order_products__review'])
        order_products = []
        for product in products:
            order_products = order_products.extend(
                list(product.order_products.all()))
        return [i for i in order_products if i.is_reviewed]

    def get_trending_products(self):
        """
        Return products with most sales or new items
        """
        avg_sales = self.aggregate(Avg('sales'))
        date_range = (datetime.now(tz=timezone.utc)-timedelta(days=14))
        return self.get_queryset().filter(
            Q(created_at__lt=date_range) |
            Q(sales__gt=avg_sales['sales__avg'])
        )

    def search(self, search_text):
        """
        FTS for products, search in name, summary and detail.
        """
        search_vectors = (
            SearchVector(
                'name', weight='A', config='english'
            )
            + SearchVector(
                StringAgg('detail', delimiter=' '),
                weight='B',
                config='english',
            )
            + SearchVector(
                StringAgg('summary', delimiter=' '),
                weight='C',
                config='english',
            )
        )
        search_query = SearchQuery(
            search_text, config='english'
        )
        search_rank = SearchRank(search_vectors, search_query)
        trigram_similarity = TrigramSimilarity(
            'name', search_text
        )
        queryset = self.get_queryset()\
            .annotate(search=search_vectors)\
            .filter(search=search_query)\
            .annotate(rank=search_rank+trigram_similarity).order_by('-rank')
        return queryset
        # not working when fiter search_vector with search_query,
        # better to make use of vector field instead of on the fly
        # qs = (
        #     self.get_queryset()
        #     .filter(search_vector=search_query)
        #     .annotate(rank=search_rank + trigram_similarity)
        #     .order_by('-rank')
        # )
