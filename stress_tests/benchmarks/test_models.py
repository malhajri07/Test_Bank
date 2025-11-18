"""
Model operation performance benchmarks.

Tests measure:
- Bulk operations
- Session creation and answer saving
- Score calculation performance
- Access validation queries
"""

import pytest
from django.contrib.auth import get_user_model
from catalog.models import Category, TestBank, Question, AnswerOption
from practice.models import UserTestAccess, UserTestSession, UserAnswer
from decimal import Decimal
import random

User = get_user_model()


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_bank_with_questions(db):
    """Create test bank with many questions."""
    category = Category.objects.create(
        name='Test Category',
        slug='test-category',
        description='Test description'
    )
    
    test_bank = TestBank.objects.create(
        category=category,
        title='Test Bank',
        slug='test-bank',
        description='Test description',
        price=Decimal('29.99'),
        difficulty_level='easy',
        is_active=True
    )
    
    # Create 50 questions
    questions = []
    for i in range(50):
        question = Question.objects.create(
            test_bank=test_bank,
            question_text=f'Question {i+1}',
            question_type='mcq_single',
            explanation=f'Explanation {i+1}',
            order=i+1
        )
        questions.append(question)
        
        # Create 4 answer options per question
        for j in range(4):
            AnswerOption.objects.create(
                question=question,
                option_text=f'Option {j+1}',
                is_correct=(j == 0),
                order=j+1
            )
    
    return test_bank, questions


@pytest.mark.benchmark
@pytest.mark.django_db
def test_session_creation_performance(benchmark, user, test_bank_with_questions):
    """Benchmark session creation."""
    test_bank, questions = test_bank_with_questions
    
    # Grant access
    UserTestAccess.objects.create(
        user=user,
        test_bank=test_bank,
        is_active=True
    )
    
    def create_session():
        # Randomize question order
        question_ids = [q.id for q in questions]
        random.shuffle(question_ids)
        
        session = UserTestSession.objects.create(
            user=user,
            test_bank=test_bank,
            status='in_progress',
            question_order=question_ids
        )
        return session
    
    result = benchmark.pedantic(create_session, rounds=10, iterations=5)
    assert result.id is not None


@pytest.mark.benchmark
@pytest.mark.django_db
def test_answer_saving_performance(benchmark, user, test_bank_with_questions):
    """Benchmark answer saving operation."""
    test_bank, questions = test_bank_with_questions
    
    # Grant access and create session
    UserTestAccess.objects.create(
        user=user,
        test_bank=test_bank,
        is_active=True
    )
    
    session = UserTestSession.objects.create(
        user=user,
        test_bank=test_bank,
        status='in_progress'
    )
    
    question = questions[0]
    correct_option = AnswerOption.objects.filter(
        question=question,
        is_correct=True
    ).first()
    
    def save_answer():
        answer = UserAnswer.objects.create(
            session=session,
            question=question
        )
        answer.selected_options.set([correct_option])
    
    benchmark.pedantic(save_answer, rounds=20, iterations=10)


@pytest.mark.benchmark
@pytest.mark.django_db
def test_score_calculation_performance(benchmark, user, test_bank_with_questions):
    """Benchmark score calculation."""
    test_bank, questions = test_bank_with_questions
    
    # Grant access and create session
    UserTestAccess.objects.create(
        user=user,
        test_bank=test_bank,
        is_active=True
    )
    
    session = UserTestSession.objects.create(
        user=user,
        test_bank=test_bank,
        status='in_progress'
    )
    
    # Answer all questions
    for question in questions[:20]:  # Answer first 20 questions
        correct_option = AnswerOption.objects.filter(
            question=question,
            is_correct=True
        ).first()
        if correct_option:
            answer = UserAnswer.objects.create(
                session=session,
                question=question
            )
            answer.selected_options.set([correct_option])
    
    def calculate_score():
        return session.calculate_score()
    
    result = benchmark.pedantic(calculate_score, rounds=10, iterations=5)
    assert result is not None


@pytest.mark.benchmark
@pytest.mark.django_db
def test_access_validation_performance(benchmark, user, test_bank_with_questions):
    """Benchmark access validation query."""
    test_bank, questions = test_bank_with_questions
    
    # Grant access
    UserTestAccess.objects.create(
        user=user,
        test_bank=test_bank,
        is_active=True
    )
    
    def validate_access():
        access = UserTestAccess.objects.filter(
            user=user,
            test_bank=test_bank,
            is_active=True
        ).first()
        return access and access.is_valid()
    
    result = benchmark.pedantic(validate_access, rounds=20, iterations=10)
    assert result is True


@pytest.mark.benchmark
@pytest.mark.django_db
def test_bulk_answer_creation_performance(benchmark, user, test_bank_with_questions):
    """Benchmark bulk answer creation."""
    test_bank, questions = test_bank_with_questions
    
    # Grant access and create session
    UserTestAccess.objects.create(
        user=user,
        test_bank=test_bank,
        is_active=True
    )
    
    session = UserTestSession.objects.create(
        user=user,
        test_bank=test_bank,
        status='in_progress'
    )
    
    def bulk_create_answers():
        answers = []
        options_map = {}
        for question in questions[:30]:
            correct_option = AnswerOption.objects.filter(
                question=question,
                is_correct=True
            ).first()
            if correct_option:
                answer = UserAnswer(
                    session=session,
                    question=question
                )
                answers.append(answer)
                options_map[id(answer)] = [correct_option]
        
        created_answers = UserAnswer.objects.bulk_create(answers)
        # Set many-to-many relationships after creation
        for answer in created_answers:
            if id(answer) in options_map:
                answer.selected_options.set(options_map[id(answer)])
    
    benchmark.pedantic(bulk_create_answers, rounds=5, iterations=2)

