from django.db import models


class SKUManager(models.Manager):
    def get_queryset(self):
        """
        Only return products on the shelf
        """
        return super().get_queryset().filter(status='ON')

    def get_same_category_products(self, obj):
        """
        Return a queryset containing products in the same category, exluding current product.
        """
        category = obj.category
        current = obj.id
        return self.get_queryset().filter(category=category).exclude(id=current)
