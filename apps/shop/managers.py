from datetime import datetime, timedelta, timezone
from django.db import models
from django.db.models import Q
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import (
    SearchQuery, SearchRank, SearchVector, TrigramSimilarity,
)
from django.db.models import Avg


class SKUManager(models.Manager):
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
        return self.get_queryset().filter(category=category).\
            exclude(id=current).order_by('sales', '-created_at')

    def filter_category_products(self, category, queryset):
        """
        Filter a queryset with a category, category can be parent category.
        """
        if category.get_descendant_count() > 0:
            qs = self.none()
            for cat in category.get_descendants():
                desc_qs = queryset.filter(category=cat)
                qs = qs.union(desc_qs)
            queryset = qs
        else:
            queryset = queryset.filter(category=category)
        return queryset

    def get_products_with_review(self):
        """
        Return a LIST of products sku which has a customer review.
        """
        products = self.get_queryset()
        order_products = []
        for product in products:
            order_products = order_products.extend(
                list(product.order_products.all()))
        return [i for i in order_products if i.is_reviewed]
        # return self.get_queryset().filter()

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
