# Generated by Django 3.1.4 on 2020-12-20 08:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0005_auto_20201217_1804'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ('-created_at',), 'permissions': [('ship_order', 'can ship orders in admin page'), ('cancel_order', 'can cancel orders in admin page')]},
        ),
        migrations.AlterModelOptions(
            name='payment',
            options={'ordering': ('-created_at',), 'permissions': [('refund', 'can create a refund in admin page')]},
        ),
    ]
