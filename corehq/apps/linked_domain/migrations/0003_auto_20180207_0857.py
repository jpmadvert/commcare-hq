# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-07 08:57
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import migrations
from corehq.sql_db.operations import noop_migration


class Migration(migrations.Migration):

    dependencies = [
        ('linked_domain', '0002_migrate_linked_apps'),
    ]

    operations = [
        noop_migration()
    ]
