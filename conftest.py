"""
Pytest configuration and shared fixtures.

Uses factory_boy for test data generation.
"""

import pytest
from decimal import Decimal

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
    )


@pytest.fixture
def category(db):
    """Create a test category."""
    from catalog.models import Category
    return Category.objects.create(
        name='Test Category',
        slug='test-category',
        description='Test category description',
    )


@pytest.fixture
def test_bank(db, category):
    """Create a test bank."""
    from catalog.models import TestBank
    return TestBank.objects.create(
        category=category,
        title='Test Bank',
        slug='test-bank',
        description='Test bank description',
        price=Decimal('29.99'),
        difficulty_level='easy',
        is_active=True,
    )


@pytest.fixture
def question(db, test_bank):
    """Create a test question with answer options."""
    from catalog.models import Question, AnswerOption
    q = Question.objects.create(
        test_bank=test_bank,
        question_text='What is 2 + 2?',
        question_type='mcq_single',
        order=1,
        is_active=True,
    )
    AnswerOption.objects.create(question=q, option_text='3', is_correct=False, order=1)
    AnswerOption.objects.create(question=q, option_text='4', is_correct=True, order=2)
    return q
