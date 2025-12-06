import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testbank_platform.settings')
django.setup()

from catalog.models import Category

def cleanup_data():
    deleted_count, _ = Category.objects.all().delete()
    print(f"Deleted {deleted_count} categories and their related objects (SubCategories, TestBanks, Questions, etc.).")

if __name__ == '__main__':
    cleanup_data()
