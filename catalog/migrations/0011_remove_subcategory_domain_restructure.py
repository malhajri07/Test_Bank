# Migration to remove SubCategory/Domain and restructure to Category -> Certification

from django.db import migrations, models
import django.db.models.deletion


def migrate_certifications_to_category(apps, schema_editor):
    """
    Migrate certifications from SubCategory to Category.
    For each certification, get its subcategory's category and assign it directly.
    """
    Certification = apps.get_model('catalog', 'Certification')
    SubCategory = apps.get_model('catalog', 'SubCategory')
    
    # Migrate certifications: subcategory -> category
    for cert in Certification.objects.all():
        if cert.subcategory:
            cert.category = cert.subcategory.category
            cert.save()


def migrate_testbanks(apps, schema_editor):
    """
    Migrate test banks:
    - If test bank has subcategory, set category from subcategory
    """
    TestBank = apps.get_model('catalog', 'TestBank')
    SubCategory = apps.get_model('catalog', 'SubCategory')
    
    for testbank in TestBank.objects.all():
        if testbank.subcategory and not testbank.category:
            testbank.category = testbank.subcategory.category
            testbank.save()


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0010_testbank_certification_metadata'),
    ]

    operations = [
        # Step 1: Add category field to Certification (nullable first)
        migrations.AddField(
            model_name='certification',
            name='category',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='certifications',
                to='catalog.category',
                verbose_name='Category',
            ),
        ),
        
        # Step 2: Migrate data
        migrations.RunPython(migrate_certifications_to_category, migrations.RunPython.noop),
        
        # Step 3: Make category field non-nullable
        migrations.AlterField(
            model_name='certification',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='certifications',
                to='catalog.category',
                verbose_name='Category',
            ),
        ),
        
        # Step 4: Update Certification unique_together BEFORE removing subcategory field
        migrations.AlterUniqueTogether(
            name='certification',
            unique_together={('category', 'slug')},
        ),
        
        # Step 5: Remove subcategory field from Certification (after updating unique_together)
        migrations.RemoveField(
            model_name='certification',
            name='subcategory',
        ),
        
        # Step 6: Migrate test banks
        migrations.RunPython(migrate_testbanks, migrations.RunPython.noop),
        
        # Step 7: Remove subcategory field from TestBank
        migrations.RemoveField(
            model_name='testbank',
            name='subcategory',
        ),
        
        # Step 8: Rename domain CharField to certification_domain in TestBank
        migrations.RenameField(
            model_name='testbank',
            old_name='domain',
            new_name='certification_domain',
        ),
        
        # Step 9: Remove index on subcategory for TestBank
        migrations.AlterIndexTogether(
            name='testbank',
            index_together=set(),
        ),
        
        # Step 10: Remove the subcategory index explicitly
        migrations.RunSQL(
            "DROP INDEX IF EXISTS catalog_tes_subcate_8f7ae7_idx;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
