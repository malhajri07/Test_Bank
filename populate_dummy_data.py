import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testbank_platform.settings')
django.setup()

from catalog.models import Category, Certification, TestBank
from django.utils.text import slugify

def populate():
    print("Creating dummy data...")
    
    # Create a category
    cat, _ = Category.objects.get_or_create(
        name="Verification Category", 
        defaults={'slug': slugify("Verification Category"), 'description': "For testing labels"}
    )
    
    # Create certification
    cert, _ = Certification.objects.get_or_create(
        category=cat, 
        name="Test Certification",
        difficulty_level='easy',
        defaults={'slug': slugify("Test Certification"), 'description': "Test certification"}
    )
    
    # Create test banks with different difficulties
    difficulties = ['easy', 'medium', 'advanced']
    
    for diff in difficulties:
        title = f"Test Bank {diff.capitalize()}"
        TestBank.objects.get_or_create(
            title=title,
            slug=f"test-bank-{diff}",
            category=cat,
            certification=cert,
            defaults={
                'description': f"A {diff} test bank.",
                'price': 10.00,
                'difficulty_level': diff,
                'is_active': True
            }
        )
        print(f"Created {title}")

if __name__ == '__main__':
    populate()
