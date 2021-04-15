# Generated by Django 3.1.7 on 2021-04-15 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_auto_20210415_1222'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='balancedetail',
            name='end_turn_balance',
        ),
        migrations.RemoveField(
            model_name='balancedetail',
            name='fine',
        ),
        migrations.RemoveField(
            model_name='balancedetail',
            name='fixed_costs',
        ),
        migrations.RemoveField(
            model_name='balancedetail',
            name='logistics',
        ),
        migrations.RemoveField(
            model_name='balancedetail',
            name='raw_stuff_costs',
        ),
        migrations.RemoveField(
            model_name='balancedetail',
            name='sales_income',
        ),
        migrations.RemoveField(
            model_name='balancedetail',
            name='start_turn_balance',
        ),
        migrations.RemoveField(
            model_name='balancedetail',
            name='storage',
        ),
        migrations.RemoveField(
            model_name='balancedetail',
            name='variable_costs',
        ),
        migrations.AddField(
            model_name='balancedetail',
            name='data',
            field=models.CharField(default='', max_length=300),
        ),
    ]