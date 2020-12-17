# Generated by Django 3.1.4 on 2020-12-17 09:04

from django.db import migrations, models
import django.db.models.deletion
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_auto_20201201_2211'),
        ('order', '0004_auto_20201215_0015'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviews', to='account.user', verbose_name='user'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=django_fsm.FSMField(choices=[('NW', 'New'), ('CF', 'Confirmed'), ('CL', 'Cancelling'), ('CX', 'Cancelled'), ('SP', 'Shipped'), ('RT', 'Returning'), ('CP', 'Completed')], default='NW', max_length=50, protected=True, verbose_name='order status'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(choices=[('CARD', 'Credit Card'), ('ALIPAY', 'Alipay')], default='CARD', max_length=10, verbose_name='payment method'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=django_fsm.FSMField(choices=[('PD', 'Pending'), ('SC', 'Succeeded'), ('EX', 'Expired'), ('RF', 'Refunded')], default='PD', max_length=50, protected=True, verbose_name='payment status'),
        ),
    ]
