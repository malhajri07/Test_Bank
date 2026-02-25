import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testbank_platform.settings')
django.setup()

from catalog.models import Category, Certification, TestBank
from django.utils.text import slugify

def create_category_data(name, cert_names):
    cat, created = Category.objects.get_or_create(
        name=name, 
        defaults={'slug': slugify(name), 'description': f'{name} category'}
    )
    if created:
        print(f"Created category: {name}")
    else:
        print(f"Category {name} already exists")

    for cert_name in cert_names:
        cert, created = Certification.objects.get_or_create(
            category=cat,
            name=cert_name,
            difficulty_level='easy',  # Default difficulty
            defaults={'slug': slugify(cert_name), 'description': f'{cert_name} certification'}
        )
        if created:
            print(f"  Created certification: {cert_name}")
        
        # Create a dummy test bank to ensure it shows up in navigation (due to count > 0 filter)
        tb, created = TestBank.objects.get_or_create(
            title=f"Test Bank for {cert_name}",
            defaults={
                'slug': slugify(f"test-bank-{cert_name}"),
                'category': cat,
                'certification': cert,
                'description': 'Dummy test bank',
                'is_active': True,
                'price': 10.00
            }
        )
        if created:
            print(f"    Created test bank: {tb.title}")

create_category_data('School', ['Math', 'Science', 'History'])
create_category_data('College', ['Engineering', 'Medicine', 'Law'])
