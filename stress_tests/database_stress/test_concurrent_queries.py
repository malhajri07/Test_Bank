"""
Concurrent database query stress tests.

Tests:
- Concurrent database operations
- Transaction isolation
- Connection pool effectiveness
- Database locks and deadlocks
"""

import pytest
import threading
from django.db import transaction
from django.contrib.auth import get_user_model
from catalog.models import Category, TestBank, Question, AnswerOption
from practice.models import UserTestAccess, UserTestSession, UserAnswer
from decimal import Decimal
import time

User = get_user_model()


@pytest.fixture
def test_bank_with_questions(db):
    """Create test bank with questions."""
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
    for i in range(50):
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


@pytest.mark.django_db
def test_concurrent_session_creation(test_bank_with_questions):
    """Test concurrent session creation."""
    users = []
    for i in range(10):
        user = User.objects.create_user(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='testpass123'
        )
        users.append(user)
        
        # Grant access
        UserTestAccess.objects.create(
            user=user,
            test_bank=test_bank_with_questions,
            is_active=True
        )
    
    sessions_created = []
    errors = []
    
    def create_session(user):
        try:
            session = UserTestSession.objects.create(
                user=user,
                test_bank=test_bank_with_questions,
                status='in_progress'
            )
            sessions_created.append(session.id)
        except Exception as e:
            errors.append(str(e))
    
    # Create sessions concurrently
    threads = []
    for user in users:
        thread = threading.Thread(target=create_session, args=(user,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    # All sessions should be created successfully
    assert len(sessions_created) == 10
    assert len(errors) == 0


@pytest.mark.django_db
def test_concurrent_answer_saving(test_bank_with_questions):
    """Test concurrent answer saving."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Grant access and create session
    UserTestAccess.objects.create(
        user=user,
        test_bank=test_bank_with_questions,
        is_active=True
    )
    
    session = UserTestSession.objects.create(
        user=user,
        test_bank=test_bank_with_questions,
        status='in_progress'
    )
    
    questions = list(Question.objects.filter(test_bank=test_bank_with_questions)[:20])
    answers_created = []
    errors = []
    
    def save_answer(question):
        try:
            correct_option = AnswerOption.objects.filter(
                question=question,
                is_correct=True
            ).first()
            
            if correct_option:
                answer = UserAnswer.objects.create(
                    session=session,
                    question=question,
                    selected_options=[correct_option]
                )
                answers_created.append(answer.id)
        except Exception as e:
            errors.append(str(e))
    
    # Save answers concurrently
    threads = []
    for question in questions:
        thread = threading.Thread(target=save_answer, args=(question,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    # All answers should be saved successfully
    assert len(answers_created) == len(questions)
    assert len(errors) == 0


@pytest.mark.django_db
def test_transaction_isolation(test_bank_with_questions):
    """Test transaction isolation."""
    user1 = User.objects.create_user(
        username='user1',
        email='user1@example.com',
        password='testpass123'
    )
    
    user2 = User.objects.create_user(
        username='user2',
        email='user2@example.com',
        password='testpass123'
    )
    
    # Grant access
    UserTestAccess.objects.create(
        user=user1,
        test_bank=test_bank_with_questions,
        is_active=True
    )
    
    UserTestAccess.objects.create(
        user=user2,
        test_bank=test_bank_with_questions,
        is_active=True
    )
    
    # Create sessions in transactions
    session1_id = None
    session2_id = None
    
    def create_session1():
        nonlocal session1_id
        with transaction.atomic():
            session = UserTestSession.objects.create(
                user=user1,
                test_bank=test_bank_with_questions,
                status='in_progress'
            )
            session1_id = session.id
            time.sleep(0.1)  # Simulate some processing
    
    def create_session2():
        nonlocal session2_id
        with transaction.atomic():
            session = UserTestSession.objects.create(
                user=user2,
                test_bank=test_bank_with_questions,
                status='in_progress'
            )
            session2_id = session.id
            time.sleep(0.1)  # Simulate some processing
    
    # Create sessions concurrently
    thread1 = threading.Thread(target=create_session1)
    thread2 = threading.Thread(target=create_session2)
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
    
    # Both sessions should be created
    assert session1_id is not None
    assert session2_id is not None
    assert session1_id != session2_id


@pytest.mark.django_db
def test_connection_pool_effectiveness(test_bank_with_questions):
    """Test database connection pool effectiveness."""
    users = []
    for i in range(50):
        user = User.objects.create_user(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='testpass123'
        )
        users.append(user)
        
        UserTestAccess.objects.create(
            user=user,
            test_bank=test_bank_with_questions,
            is_active=True
        )
    
    sessions_created = []
    errors = []
    
    def create_session(user):
        try:
            session = UserTestSession.objects.create(
                user=user,
                test_bank=test_bank_with_questions,
                status='in_progress'
            )
            sessions_created.append(session.id)
        except Exception as e:
            errors.append(str(e))
    
    # Create many sessions concurrently
    threads = []
    for user in users:
        thread = threading.Thread(target=create_session, args=(user,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    # Connection pool should handle concurrent requests
    assert len(sessions_created) == len(users)
    assert len(errors) == 0

