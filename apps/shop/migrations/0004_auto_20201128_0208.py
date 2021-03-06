# Generated by Django 3.1.3 on 2020-11-27 17:08

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_auto_20201123_1706'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name_plural': 'categories'},
        ),
        migrations.AlterModelOptions(
            name='productsku',
            options={'get_latest_by': ('created_at',), 'ordering': ('name',), 'verbose_name': 'SKU', 'verbose_name_plural': 'SKU'},
        ),
        migrations.AlterField(
            model_name='category',
            name='desc',
            field=ckeditor.fields.RichTextField(default='', max_length=250, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='origin',
            name='desc',
            field=models.CharField(default='', max_length=250, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='productsku',
            name='brand',
            field=models.CharField(default='', max_length=50, verbose_name='brand'),
        ),
        migrations.AlterField(
            model_name='productsku',
            name='detail',
            field=ckeditor.fields.RichTextField(default=''),
        ),
        migrations.AlterField(
            model_name='productsku',
            name='price',
            field=models.DecimalField(decimal_places=0, max_digits=9, verbose_name='price'),
        ),
        migrations.AlterField(
            model_name='productsku',
            name='summary',
            field=models.CharField(default='', max_length=250, verbose_name='summary'),
        ),
        migrations.AlterField(
            model_name='productspu',
            name='desc',
            field=models.CharField(default='', max_length=250, verbose_name='description'),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('slug', 'parent')},
        ),
    ]
