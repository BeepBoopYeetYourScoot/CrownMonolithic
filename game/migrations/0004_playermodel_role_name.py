# Generated by Django 3.1.7 on 2021-04-14 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0003_auto_20210408_1017'),
    ]

    operations = [
        migrations.AddField(
            model_name='playermodel',
            name='role_name',
            field=models.CharField(default='unassigned', max_length=20, verbose_name='Игровое имя'),
        ),
    ]
