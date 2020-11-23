
from django.db import models
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.search import SearchVectorField
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager
from ckeditor.fields import RichTextField
from mptt.models import MPTTModel, TreeForeignKey

from db.base_model import BaseModel
from .managers import SKUManager
# from .tasks import update_search_vector


class Category(MPTTModel):
    parent = TreeForeignKey('self', verbose_name=_('parent'), on_delete=models.CASCADE,
                            null=True, blank=True, related_name='children')
    name = models.CharField(_("name"), max_length=50, unique=True)
    slug = models.SlugField(_("slug"), max_length=50,
                            unique=True, null=True, blank=True)
    desc = RichTextField(_("description"), max_length=250)
    image = models.ImageField(
        _("image"), upload_to='media/category/', blank=True, null=True)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='created')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='updated')

    class MPTTMeta:
        unique_together = ('slug', 'parent',)
        order_insertion_by = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_full_category_name(self):
        full_name = [self.name]
        parent = self.parent
        while parent is not None:
            full_name.append(parent.name)
            parent = parent.parent
        return '/'.join(full_name[::-1])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super(Category, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:category-list", kwargs={"category_slug": self.slug})


class Origin(BaseModel):
    """
    use HASC code for prefectures in Japan
    """
    name = models.CharField(_("name"), max_length=50, unique=True)
    desc = models.CharField(_("description"), max_length=250)

    def __str__(self):
        return self.name


class ProductSPU(BaseModel):
    name = models.CharField(_("name"), max_length=50, unique=True)
    desc = models.CharField(_("description"), max_length=250)

    class Meta:
        verbose_name = 'SPU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class ProductSKU(BaseModel):

    class Status(models.TextChoices):
        ON = 'ON', _('On the shelf')
        OFF = 'OFF', _('Off the shelf')

    name = models.CharField(_("name"), max_length=50)
    slug = models.SlugField(_("slug"), max_length=50,
                            unique=True, null=True, blank=True)
    summary = models.CharField(_("summary"), max_length=250)
    detail = RichTextField(blank=True, null=True)
    unit = models.CharField(_("unit"), max_length=50)
    price = models.DecimalField(_("price"), max_digits=9, decimal_places=2)
    stock = models.PositiveIntegerField(
        _("stock"), default=1, validators=[MaxValueValidator(999)])
    sales = models.PositiveIntegerField(_("sales"),  default=0)
    brand = models.CharField(
        _("brand"), max_length=50, blank=True, null=True)
    cover_img = models.ImageField(
        _("cover image"), upload_to='media/sku_cover/', blank=True, null=True)
    tags = TaggableManager(_("tags"))
    status = models.CharField(
        _("shelf status"), choices=Status.choices, default=Status.ON, max_length=3)
    origin = models.ForeignKey(Origin, verbose_name=_(
        "place of origin"), default='Japan', on_delete=models.SET_DEFAULT, related_name='sku')
    category = models.ForeignKey(Category, verbose_name=_(
        "category"), on_delete=models.CASCADE, related_name='sku')
    spu = models.ForeignKey(ProductSPU, verbose_name=_(
        "SPU"), on_delete=models.CASCADE, related_name='sku')
    search_vector = SearchVectorField(null=True)
    # future update for promotion discount
    # promotion = models.ForeignKey("app.Model", verbose_name=_(""), on_delete=models.CASCADE)

    objects = SKUManager()

    class Meta:
        ordering = ('name',)
        verbose_name = 'SKU'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['name', ]),
            models.Index(fields=['summary', 'detail', ]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super(ProductSKU, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:product-detail", kwargs={"pk": self.pk, 'slug': self.slug})

    @property
    def tax_in_price(self):
        """
        Use this property to set extra tax on product price
        """
        tax_rate = 0.1
        tax_in_price = self.price * (1+tax_rate)
        return float('{0:.2f}'.format(tax_in_price))

    # @property
    # def sku_number(self):
    #     """
    #     Generate a sku number for each product
    #     """
    #     sku_no = 'self.category-self.origin-self.spu-self.id'
    #     # Food-Kyoto-manjiya rice cracker-002 -> FD-KY-RC-002
    #     # Drink-yamaguchi-dassai sake-003 -> DR-YM-DS
    #     return sku_no

    # def get_discounted_price(self):
    #     """
    #     calculate the discounted price with price and discount rate
    #     """
    #     pass

    # def get_product_label(self):
    #     """
    #     Return a label from SALE, SOLD, NEW, HOT, or empty
    #     """
    #     pass


class Image(BaseModel):
    sku = models.ForeignKey(ProductSKU, verbose_name=_(
        "SKU"), on_delete=models.CASCADE, related_name='images')
    name = models.CharField(_("name"), max_length=50)
    image = models.ImageField(_("image"), upload_to='media/sku_image/')

    def __str__(self):
        return f'{self.sku}-{self.name}'


class HomeBanner(BaseModel):
    sku = models.ForeignKey(ProductSKU, verbose_name=_(
        "SKU"), on_delete=models.CASCADE)
    index = models.IntegerField(_("index no."), validators=[
        MaxValueValidator(10), MinValueValidator(1)])
    image = models.ImageField(_("image"), upload_to='media/banner/')

    def __str__(self):
        return self.sku
