# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-23 13:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0005_auto_20161122_0434'),
    ]

    operations = [
        migrations.RenameField(
            model_name='study',
            old_name='description',
            new_name='study_description',
        ),
    ]
