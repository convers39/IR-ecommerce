from django.db import models


class BaseModel(models.Model):
    """
    Base model inheritated by other models
    """
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='created')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='updated')
    is_deleted = models.BooleanField(default=False, verbose_name='deleted')

    class Meta:
        abstract = True
