"""
Performance benchmarks for Django views.

Tests measure:
- Response times for each view
- Query counts per request
- Template rendering performance
"""

import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from catalog.models import Category, TestBank, Question, AnswerOption
from practice.models import UserTestAccess, UserTestSession
from decimal import Decimal

User = get_user_model()


@pytest.fixture
def client():
    """Create test client."""
    return Client()


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def category(db):
    """Create test category."""
    return Category.objects.create(
        name='Test Category',
        slug='test-category',
        description='Test description'
    )


@pytest.fixture
def test_bank(db, category):
    """Create test bank with questions."""
    test_bank = TestBank.objects.create(
        category=category,
        title='Test Bank',
        slug='test-bank',
        description='Test description',
        price=Decimal('29.99'),
        difficulty_level='easy',
        is_active=True
    )
    
    # Create questions
    for i in range(10):
        question = Question.objects.create(
            test_bank=test_bank,
            question_text=f'Question {i+1}',
            question_type='mcq_single',
            explanation=f'Explanation {i+1}',
            order=i+1
        )
        # Create answer options
        for j in range(4):
            AnswerOption.objects.create(
                question=question,
                option_text=f'Option {j+1}',
                is_correct=(j == 0),
                order=j+1
            )
    
    return test_bank


@pytest.mark.benchmark
def test_homepage_performance(benchmark, client):
    """Benchmark homepage response time."""
    result = benchmark.pedantic(
        client.get,
        args=('/'),
        rounds=10,
        iterations=5
    )
    assert result.status_code == 200


@pytest.mark.benchmark
def test_category_list_performance(benchmark, client, category):
    """Benchmark category list view."""
    result = benchmark.pedantic(
        client.get,
        args=('/categories/'),
        rounds=10,
        iterations=5
    )
    assert result.status_code == 200


@pytest.mark.benchmark
def test_testbank_detail_performance(benchmark, client, test_bank):
    """Benchmark test bank detail view."""
    result = benchmark.pedantic(
        client.get,
        args=(f'/categories/{test_bank.category.slug}/test-banks/{test_bank.slug}/'),
        rounds=10,
        iterations=5
    )
    assert result.status_code == 200


@pytest.mark.benchmark
def test_dashboard_performance(benchmark, client, user, test_bank):
    """Benchmark user dashboard."""
    # Grant access
    UserTestAccess.objects.create(
        user=user,
        test_bank=test_bank,
        is_active=True
    )
    
    client.force_login(user)
    result = benchmark.pedantic(
        client.get,
        args=('/accounts/dashboard/'),
        rounds=10,
        iterations=5
    )
    assert result.status_code == 200


@pytest.mark.benchmark
def test_practice_session_performance(benchmark, client, user, test_bank):
    """Benchmark practice session view."""
    # Grant access
    access = UserTestAccess.objects.create(
        user=user,
        test_bank=test_bank,
        is_active=True
    )
    
    # Create session
    session = UserTestSession.objects.create(
        user=user,
        test_bank=test_bank,
        status='in_progress'
    )
    
    client.force_login(user)
    result = benchmark.pedantic(
        client.get,
        args=(f'/practice/session/{session.id}/'),
        rounds=10,
        iterations=5
    )
    assert result.status_code == 200


@pytest.mark.django_db
@pytest.mark.benchmark
def test_query_count_homepage(benchmark, client, category, test_bank):
    """Measure query count for homepage."""
    from django.test.utils import override_settings
    from django.db import connection
    
    with override_settings(DEBUG=True):
        connection.queries_log.clear()
        result = client.get('/')
        query_count = len(connection.queries)
        
        # Benchmark the query count
        benchmark(query_count)
        
        assert result.status_code == 200
        assert query_count < 20  # Should be optimized


@pytest.mark.django_db
@pytest.mark.benchmark
def test_query_count_category_list(benchmark, client, category, test_bank):
    """Measure query count for category list."""
    from django.test.utils import override_settings
    from django.db import connection
    
    with override_settings(DEBUG=True):
        connection.queries_log.clear()
        result = client.get('/categories/')
        query_count = len(connection.queries)
        
        benchmark(query_count)
        
        assert result.status_code == 200
        assert query_count < 10  # Should use select_related/prefetch_related

