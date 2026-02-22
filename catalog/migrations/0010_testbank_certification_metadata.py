# Generated manually for adding certification metadata fields

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0009_contactmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="testbank",
            name="domain",
            field=models.CharField(
                blank=True,
                help_text="Subject area or domain of the certification (e.g., Information Technology, Healthcare)",
                max_length=200,
                null=True,
                verbose_name="Domain",
            ),
        ),
        migrations.AddField(
            model_name="testbank",
            name="organization",
            field=models.CharField(
                blank=True,
                help_text="Organization or body that issues the certification (e.g., CompTIA, Microsoft, PMI)",
                max_length=200,
                null=True,
                verbose_name="Organization",
            ),
        ),
        migrations.AddField(
            model_name="testbank",
            name="official_url",
            field=models.URLField(
                blank=True,
                help_text="Official website URL for the certification or organization",
                max_length=500,
                null=True,
                verbose_name="Official URL",
            ),
        ),
        migrations.AddField(
            model_name="testbank",
            name="certification_details",
            field=models.TextField(
                blank=True,
                help_text="Additional details about the certification, requirements, or exam information",
                null=True,
                verbose_name="Certification Details",
            ),
        ),
    ]
