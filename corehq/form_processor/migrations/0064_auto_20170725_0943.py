# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-07-25 09:43
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('form_processor', '0063_auto_20160908_0954'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ledgervalue',
            name='last_modified',
            field=models.DateTimeField(db_index=True),
        ),
    ]
