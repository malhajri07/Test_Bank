"""
Context processors for catalog app.

Makes catalog data available globally across all templates.
"""

from django.db.models import Count, Q, Prefetch
from .models import Category, SubCategory, Certification


def categories(request):
    """
    Context processor to add categories to all templates.
    
    Provides:
    - Top categories with test bank counts for navigation
    - Subcategories prefetched for mega menu
    - Certifications prefetched for mega menu
    """
    # Get top categories with test bank counts and prefetch subcategories
    top_categories = Category.objects.annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
    ).filter(test_bank_count__gt=0).prefetch_related(
        Prefetch(
            'subcategories',
            queryset=SubCategory.objects.annotate(
                test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
            ).prefetch_related(
                Prefetch(
                    'certifications',
                    queryset=Certification.objects.annotate(
                        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
                    ).filter(test_bank_count__gt=0).order_by('order', 'name')
                )
            ).order_by('order', 'name')
        )
    ).order_by('name')[:10]
    
    return {
        'categories': top_categories,
    }

