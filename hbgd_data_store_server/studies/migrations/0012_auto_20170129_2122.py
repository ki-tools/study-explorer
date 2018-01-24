# -*- coding: utf-8 -*-
from django.db import migrations


def cache_count_codes(apps, schema_editor):
    Count = apps.get_model("studies", "Count")
    for count in Count.objects.all():
        count.save()


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0011_countcodescache'),
    ]

    operations = [
        migrations.RunPython(cache_count_codes),
    ]
