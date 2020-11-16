
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager
from ckeditor.fields import RichTextField

from db.base_model import BaseModel

# TODO: check all image field setting, blank and null,
# set up S3 bucket for upload


class Category(BaseModel):
    name = models.CharField(_("name"), max_length=50)
    desc = models.CharField(_("description"), max_length=250)
    image = models.ImageField(_("image"), upload_to=None,
                              height_field=None, width_field=None, max_length=None)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Region(BaseModel):
    name = models.CharField(_("name"), max_length=50)
    desc = models.CharField(_("description"), max_length=250)

    def __str__(self):
        return self.name


class ProductSPU(BaseModel):
    name = models.CharField(_("name"), max_length=50)
    desc = models.CharField(_("description"), max_length=250)

    class Meta:
        verbose_name = 'SPU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class ProductSKU(BaseModel):
    name = models.CharField(_("name"), max_length=50, db_index=True)
    slug = models.SlugField(_("slug"), max_length=50, db_index=True)
    desc = models.CharField(_("description"), max_length=250, db_index=True)
    detail = RichTextField(blank=True, null=True)
    unit = models.CharField(_("unit"), max_length=50)
    price = models.DecimalField(_("price"), max_digits=9, decimal_places=2)
    stock = models.IntegerField(_("stock"), validators=[
                                MaxValueValidator(999), MinValueValidator(0)])
    sales = models.IntegerField(_("sales"), validators=[MinValueValidator(0)])
    discount = models.DecimalField(_("discount rate"), max_digits=3, decimal_places=2, default=1.00,
                                   validators=[MaxValueValidator(1), MinValueValidator(0)])
    cover_img = models.ImageField(_("cover image"), upload_to=None, height_field=None,
                                  width_field=None, max_length=None, blank=True, null=True)
    tags = TaggableManager(_("tags"), blank=True, null=True)

    class Meta:
        verbose_name = 'SKU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def get_discounted_price(self):
        '''
        calculate the discounted price with price and discount rate
        '''
        pass

    def get_product_label(self):
        '''
        Return a label from SALE, SOLD, NEW, HOT, or empty
        '''
        pass


class Image(BaseModel):
    sku_id = models.ForeignKey(ProductSKU, verbose_name=_(
        "Product SKU"), on_delete=models.CASCADE)
    image = models.ImageField(_("image"), upload_to=None,
                              height_field=None, width_field=None, max_length=None)

    def __str__(self):
        return self.name


class IndexBanner(BaseModel):
    sku_id = models.ForeignKey(ProductSKU, verbose_name=_(
        "Product SKU"), on_delete=models.CASCADE)
    index = models.IntegerField(_("index no."), validators=[
                                MaxValueValidator(10), MinValueValidator(1)])
    image = models.ImageField(_("image"), upload_to=None,
                              height_field=None, width_field=None, max_length=None)

    def __str__(self):
        return self.name
