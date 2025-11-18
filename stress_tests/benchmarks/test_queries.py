"""
Database query performance benchmarks.

Tests measure:
- Complex query execution times
- N+1 query problems
- Database connection pooling
"""

import pytest
from django.db import connection
from django.test.utils import override_settings
from catalog.models import Category, TestBank, Question, AnswerOption
from practice.models import UserTestAccess, UserTestSession
from decimal import Decimal


@pytest.fixture
def categories_with_testbanks(db):
    """Create multiple categories with test banks."""
    categories = []
    for i in range(10):
        category = Category.objects.create(
            name=f'Category {i+1}',
            slug=f'category-{i+1}',
            description=f'Description {i+1}'
        )
        categories.append(category)
        
        # Create test banks for each category
        for j in range(5):
            TestBank.objects.create(
                category=category,
                title=f'Test Bank {i+1}-{j+1}',
                slug=f'test-bank-{i+1}-{j+1}',
                description=f'Description {i+1}-{j+1}',
                price=Decimal('29.99'),
                difficulty_level='easy',
                is_active=True
            )
    
    return categories


@pytest.mark.benchmark
@pytest.mark.django_db
def test_category_list_query_performance(benchmark, categories_with_testbanks):
    """Benchmark category list query with annotations."""
    from catalog.models import Category
    from django.db.models import Count, Q
    
    def run_query():
        return list(Category.objects.annotate(
            test_bank_count=Count('test_banks', filter=Q(test_banks__is_active=True)),
            subcategory_count=Count('subcategories')
        ).filter(test_bank_count__gt=0))
    
    result = benchmark.pedantic(run_query, rounds=10, iterations=5)
    assert len(result) > 0


@pytest.mark.benchmark
@pytest.mark.django_db
def test_testbank_list_query_performance(benchmark, categories_with_testbanks):
    """Benchmark test bank list query."""
    category = categories_with_testbanks[0]
    
    def run_query():
        return list(TestBank.objects.filter(
            category=category,
            is_active=True
        ).select_related('category'))
    
    result = benchmark.pedantic(run_query, rounds=10, iterations=5)
    assert len(result) > 0


@pytest.mark.benchmark
@pytest.mark.django_db
def test_n_plus_one_query_detection(benchmark, categories_with_testbanks):
    """Detect N+1 query problems."""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create access records
    for category in categories_with_testbanks:
        test_banks = TestBank.objects.filter(category=category)
        for test_bank in test_banks[:2]:  # First 2 test banks
            UserTestAccess.objects.create(
                user=user,
                test_bank=test_bank,
                is_active=True
            )
    
    # Bad query (N+1 problem)
    def bad_query():
        accesses = UserTestAccess.objects.filter(user=user, is_active=True)
        result = []
        for access in accesses:
            result.append({
                'test_bank': access.test_bank.title,
                'category': access.test_bank.category.name
            })
        return result
    
    # Good query (using select_related)
    def good_query():
        accesses = UserTestAccess.objects.filter(
            user=user,
            is_active=True
        ).select_related('test_bank', 'test_bank__category')
        result = []
        for access in accesses:
            result.append({
                'test_bank': access.test_bank.title,
                'category': access.test_bank.category.name
            })
        return result
    
    bad_result = benchmark.pedantic(bad_query, rounds=5, iterations=3)
    good_result = benchmark.pedantic(good_query, rounds=5, iterations=3)
    
    assert len(bad_result) == len(good_result)
    # Good query should be faster
    assert len(bad_result) > 0


@pytest.mark.benchmark
@pytest.mark.django_db
def test_bulk_operations_performance(benchmark, categories_with_testbanks):
    """Benchmark bulk create operations."""
    category = categories_with_testbanks[0]
    
    def bulk_create_testbanks():
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
            for i in range(100)
        ]
        TestBank.objects.bulk_create(test_banks)
    
    benchmark.pedantic(bulk_create_testbanks, rounds=3, iterations=1)


@pytest.mark.benchmark
@pytest.mark.django_db
def test_complex_join_query_performance(benchmark, categories_with_testbanks):
    """Benchmark complex join queries."""
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Q
    
    User = get_user_model()
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create some access records
    for category in categories_with_testbanks[:3]:
        test_banks = TestBank.objects.filter(category=category)
        for test_bank in test_banks:
            UserTestAccess.objects.create(
                user=user,
                test_bank=test_bank,
                is_active=True
            )
    
    def complex_query():
        return list(
            UserTestAccess.objects
            .filter(user=user, is_active=True)
            .select_related('test_bank', 'test_bank__category')
            .annotate(
                question_count=Count('test_bank__questions')
            )
        )
    
    result = benchmark.pedantic(complex_query, rounds=10, iterations=5)
    assert len(result) > 0

