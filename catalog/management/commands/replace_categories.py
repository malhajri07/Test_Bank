"""
Management command to replace all existing categories with new industry categories.

This command:
1. Deletes all existing categories (and their related subcategories, certifications, test banks via CASCADE)
2. Creates 21 new industry categories

Usage:
    python manage.py replace_categories
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import Category


class Command(BaseCommand):
    help = 'Replace all existing categories with new industry categories'

    def handle(self, *args, **options):
        self.stdout.write('Starting category replacement...')
        
        # List of new categories from the image
        new_categories = [
            'IT',
            'Cybersecurity',
            'Cloud',
            'Telecommunications',
            'Data, Analytics & AI',
            'Project Management',
            'Finance, Accounting & Banking',
            'Marketing & Product',
            'Strategy',
            'Human Resources',
            'Supply Chain & Logistics',
            'Engineering',
            'Healthcare & Medical Support',
            'Oil & Gas / Energy',
            'Aviation & Aerospace',
            'Hospitality & Tourism',
            'Automotive & Mechanics',
            'Education & Training',
            'Food, Health & Safety',
            'Creative, Media & Content',
            'Retail, Customer Service & Operations',
        ]
        
        # Count existing categories
        existing_count = Category.objects.count()
        self.stdout.write(f'Found {existing_count} existing categories')
        
        # Delete all existing categories (CASCADE will handle related data)
        if existing_count > 0:
            self.stdout.write('Deleting existing categories...')
            deleted_count, _ = Category.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing categories and related data'))
        
        # Create new categories
        self.stdout.write('Creating new categories...')
        created_categories = []
        
        for category_name in new_categories:
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    'slug': slugify(category_name),
                    'description': f'Test banks and certifications for {category_name}'
                }
            )
            
            if created:
                created_categories.append(category_name)
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {category_name}'))
            else:
                self.stdout.write(f'  - Already exists: {category_name}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Successfully replaced categories! Created {len(created_categories)} new categories.'
        ))
        self.stdout.write('')
        self.stdout.write('New categories:')
        for cat in created_categories:
            self.stdout.write(f'  • {cat}')

