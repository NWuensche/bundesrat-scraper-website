# Generated by Django 3.0.7 on 2020-08-04 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Json',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('county', models.TextField(default='', verbose_name='County')),
                ('json', models.TextField(default='', verbose_name='JSON')),
            ],
        ),
        migrations.CreateModel(
            name='JsonCountyPDFLinks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('county', models.TextField(default='', verbose_name='County')),
                ('json', models.TextField(default='', verbose_name='JSON')),
            ],
        ),
    ]
