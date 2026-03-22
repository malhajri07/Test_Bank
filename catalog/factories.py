"""
Factory Boy factories for catalog app.
"""

from decimal import Decimal

import factory
from catalog.models import AnswerOption, Category, Certification, Question, TestBank


class CategoryFactory(factory.django.DjangoModelFactory):
    """Factory for Category."""

    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category {n}')
    slug = factory.Sequence(lambda n: f'category-{n}')


class CertificationFactory(factory.django.DjangoModelFactory):
    """Factory for Certification."""

    class Meta:
        model = Certification

    name = factory.Sequence(lambda n: f'Certification {n}')
    slug = factory.Sequence(lambda n: f'cert-{n}')
    category = factory.SubFactory(CategoryFactory)
    difficulty_level = 'easy'


class TestBankFactory(factory.django.DjangoModelFactory):
    """Factory for TestBank."""

    class Meta:
        model = TestBank

    title = factory.Sequence(lambda n: f'Test Bank {n}')
    slug = factory.Sequence(lambda n: f'test-bank-{n}')
    description = 'Test bank description'
    category = factory.SubFactory(CategoryFactory)
    price = Decimal('29.99')
    difficulty_level = 'easy'
    is_active = True


class QuestionFactory(factory.django.DjangoModelFactory):
    """Factory for Question."""

    class Meta:
        model = Question

    test_bank = factory.SubFactory(TestBankFactory)
    question_text = factory.Sequence(lambda n: f'Question {n}?')
    question_type = 'mcq_single'
    order = factory.Sequence(lambda n: n)
    is_active = True


class AnswerOptionFactory(factory.django.DjangoModelFactory):
    """Factory for AnswerOption."""

    class Meta:
        model = AnswerOption

    question = factory.SubFactory(QuestionFactory)
    option_text = factory.Sequence(lambda n: f'Option {n}')
    is_correct = False
    order = factory.Sequence(lambda n: n)
