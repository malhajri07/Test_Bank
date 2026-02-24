"""
Context processors for catalog app.

Makes catalog data available globally across all templates.
"""

from django.db.models import Count, Q, Prefetch
from .models import Category, Certification, TestBank


def categories(request):
    """
    Context processor to add categories to all templates.
    
    Provides:
    - Top categories with test bank counts for navigation
    - Test banks prefetched for mega menu (up to 10 per category)
    """
    # Get top categories with test bank counts and prefetch test banks
    top_categories = Category.objects.annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
    ).filter(test_bank_count__gt=0).prefetch_related(
        Prefetch(
            'test_banks',
            queryset=TestBank.objects.filter(is_active=True).order_by('-created_at')
        )
    ).order_by('name')[:10]
    
    return {
        'categories': top_categories,
    }

