# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0013_add_difficulty_to_certification"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="certification",
            unique_together={("category", "slug", "difficulty_level")},
        ),
        migrations.AddIndex(
            model_name="certification",
            index=models.Index(
                fields=["category", "difficulty_level"],
                name="catalog_cer_categor_diffic_idx"
            ),
        ),
    ]
