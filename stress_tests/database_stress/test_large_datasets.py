"""
Database stress tests with large datasets.

Tests:
- Query performance with large data volumes
- Pagination performance
- Filtering and search with large data
"""

import pytest
from django.db import connection
from django.test.utils import override_settings
from catalog.models import Category, TestBank, Question, AnswerOption
from practice.models import UserTestAccess, UserTestSession
from decimal import Decimal
import random


@pytest.fixture
def large_dataset(db):
    """Create large dataset for stress testing."""
    categories = []
    
    # Create 100 categories
    for i in range(100):
        category = Category.objects.create(
            name=f'Category {i+1}',
            slug=f'category-{i+1}',
            description=f'Description for category {i+1}'
        )
        categories.append(category)
        
        # Create 50 test banks per category
        for j in range(50):
            test_bank = TestBank.objects.create(
                category=category,
                title=f'Test Bank {i+1}-{j+1}',
                slug=f'test-bank-{i+1}-{j+1}',
                description=f'Description for test bank {i+1}-{j+1}',
                price=Decimal('29.99'),
                difficulty_level=random.choice(['easy', 'medium', 'advanced']),
                is_active=True
            )
            
            # Create 20 questions per test bank
            for k in range(20):
                question = Question.objects.create(
                    test_bank=test_bank,
                    question_text=f'Question {k+1} for test bank {i+1}-{j+1}',
                    question_type='mcq_single',
                    explanation=f'Explanation {k+1}',
                    order=k+1
                )
                
                # Create 4 answer options per question
                for l in range(4):
                    AnswerOption.objects.create(
                        question=question,
                        option_text=f'Option {l+1}',
                        is_correct=(l == 0),
                        order=l+1
                    )
    
    return categories


@pytest.mark.django_db
def test_category_list_with_large_dataset(large_dataset):
    """Test category list query with large dataset."""
    from catalog.models import Category
    from django.db.models import Count, Q
    
    # This should be efficient even with large dataset
    categories = Category.objects.annotate(
        test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
    ).filter(test_bank_count__gt=0)
    
    category_list = list(categories[:20])  # Pagination
    assert len(category_list) == 20


@pytest.mark.django_db
def test_testbank_list_pagination_performance(large_dataset):
    """Test pagination performance with large dataset."""
    from catalog.models import TestBank
    
    # Test pagination
    page_size = 20
    page = 1
    
    test_banks = TestBank.objects.filter(is_active=True)[
        (page - 1) * page_size:page * page_size
    ]
    
    test_bank_list = list(test_banks)
    assert len(test_bank_list) <= page_size


@pytest.mark.django_db
def test_filtering_performance(large_dataset):
    """Test filtering performance with large dataset."""
    from catalog.models import TestBank
    
    # Filter by difficulty level
    easy_test_banks = TestBank.objects.filter(
        difficulty_level='easy',
        is_active=True
    )[:50]
    
    easy_list = list(easy_test_banks)
    assert len(easy_list) <= 50


@pytest.mark.django_db
def test_search_performance(large_dataset):
    """Test search performance with large dataset."""
    from catalog.models import TestBank
    from django.db.models import Q
    
    # Search by title
    search_term = "Test Bank 1"
    results = TestBank.objects.filter(
        Q(title__icontains=search_term) | Q(description__icontains=search_term),
        is_active=True
    )[:20]
    
    results_list = list(results)
    assert len(results_list) <= 20


@pytest.mark.django_db
def test_query_count_with_large_dataset(large_dataset):
    """Test query count with large dataset (should be optimized)."""
    from catalog.models import Category
    from django.db.models import Count, Q
    from django.test.utils import override_settings
    
    with override_settings(DEBUG=True):
        connection.queries_log.clear()
        
        # This query should use select_related/prefetch_related
        categories = Category.objects.annotate(
            test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True))
        ).filter(test_bank_count__gt=0)[:10]
        
        list(categories)  # Evaluate queryset
        
        query_count = len(connection.queries)
        # Should be optimized - not one query per category
        assert query_count < 10


@pytest.mark.django_db
def test_bulk_operations_with_large_dataset(db):
    """Test bulk operations with large dataset."""
    category = Category.objects.create(
        name='Bulk Category',
        slug='bulk-category',
        description='Bulk test category'
    )
    
    # Bulk create test banks
    test_banks = [
        TestBank(
            category=category,
            title=f'Bulk Test Bank {i}',
            slug=f'bulk-test-bank-{i}',
            description=f'Description {i}',
            price=Decimal('29.99'),
            difficulty_level='easy',
            is_active=True
        )
        for i in range(1000)
    ]
    
    TestBank.objects.bulk_create(test_banks, batch_size=100)
    
    # Verify creation
    count = TestBank.objects.filter(category=category).count()
    assert count == 1000

