# Migration to remove SubCategory and Domain models

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0011_remove_subcategory_domain_restructure'),
    ]

    operations = [
        # Remove SubCategory model
        migrations.DeleteModel(
            name='SubCategory',
        ),
        # Note: Domain model was never created in migrations, so no need to delete it
    ]
