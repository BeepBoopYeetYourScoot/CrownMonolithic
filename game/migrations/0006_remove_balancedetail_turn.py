# Generated by Django 3.1.7 on 2021-04-15 08:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_balancedetail'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='balancedetail',
            name='turn',
        ),
    ]