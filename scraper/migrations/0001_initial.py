# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Mytest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('myfield', models.DateTimeField(auto_now_add=True, verbose_name=b'my field')),
            ],
        ),
        migrations.CreateModel(
            name='Number',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thenumber', models.IntegerField(verbose_name=b'the number')),
            ],
        ),
        migrations.CreateModel(
            name='Json',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('county', models.TextField(verbose_name="Coutry")),
                ('json', models.TextField(verbose_name="JSON")),
            ],
        ),
    ]
