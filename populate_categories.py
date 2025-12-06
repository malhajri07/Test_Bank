import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testbank_platform.settings')
django.setup()

from catalog.models import Category, SubCategory, Certification, TestBank
from django.utils.text import slugify

def create_category_data(name, subcats):
    cat, created = Category.objects.get_or_create(
        name=name, 
        defaults={'slug': slugify(name), 'description': f'{name} category'}
    )
    if created:
        print(f"Created category: {name}")
    else:
        print(f"Category {name} already exists")

    for sub_name in subcats:
        sub, created = SubCategory.objects.get_or_create(
            category=cat,
            name=sub_name,
            defaults={'slug': slugify(sub_name), 'description': f'{sub_name} subcategory'}
        )
        if created:
            print(f"  Created subcategory: {sub_name}")
        
        # Create a dummy test bank to ensure it shows up in navigation (due to count > 0 filter)
        tb, created = TestBank.objects.get_or_create(
            title=f"Test Bank for {sub_name}",
            defaults={
                'slug': slugify(f"test-bank-{sub_name}"),
                'category': cat,
                'subcategory': sub,
                'description': 'Dummy test bank',
                'is_active': True,
                'price': 10.00
            }
        )
        if created:
            print(f"    Created test bank: {tb.title}")

create_category_data('School', ['Math', 'Science', 'History'])
create_category_data('College', ['Engineering', 'Medicine', 'Law'])
