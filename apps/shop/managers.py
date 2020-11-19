from django.db import models
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import (
    SearchQuery, SearchRank, SearchVector, TrigramSimilarity,
)


class SKUManager(models.Manager):
    def get_queryset(self):
        """
        Only return products on the shelf, prefetch all images to avoid duplicate query.
        """
        return super().get_queryset().filter(status='ON').prefetch_related('images')

    def get_same_category_products(self, obj):
        """
        Return a queryset containing most popular and recent products 
        in the same category, exluding current product.
        """
        category = obj.category
        current = obj.id
        return self.get_queryset().filter(category=category).\
            exclude(id=current).order_by('sales', '-created_at')

    def search(self, search_text):
        """
        FTS for products
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
            # + SearchVector(
            #     StringAgg('summary', delimiter=' '),
            #     weight='C',
            #     config='english',
            # )
        )
        search_query = SearchQuery(
            search_text, config='english'
        )
        search_rank = SearchRank(search_vectors, search_query)
        trigram_similarity = TrigramSimilarity(
            'name', search_text
        )
        qs = (
            self.get_queryset()
            .filter(search_vector=search_query)
            .annotate(rank=search_rank + trigram_similarity)
            .order_by('-rank')
        )
        return qs
