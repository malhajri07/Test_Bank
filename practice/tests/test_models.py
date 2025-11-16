"""
Tests for practice app models.

Tests cover:
- UserTestSession score calculation
- UserAnswer correctness checking
- UserTestAccess validation
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from catalog.models import Category, TestBank, Question, AnswerOption
from practice.models import UserTestAccess, UserTestSession, UserAnswer
from decimal import Decimal

User = get_user_model()


class UserTestSessionModelTest(TestCase):
    """Test UserTestSession model business logic."""
    
    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category and test bank
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='Test description'
        )
        
        self.test_bank = TestBank.objects.create(
            category=self.category,
            title='Test Bank',
            slug='test-bank',
            description='Test description',
            price=Decimal('29.99'),
            difficulty_level='beginner'
        )
        
        # Create questions and answers
        self.question1 = Question.objects.create(
            test_bank=self.test_bank,
            question_text='What is 2+2?',
            question_type='mcq_single',
            explanation='Basic math',
            order=1
        )
        
        self.correct_option1 = AnswerOption.objects.create(
            question=self.question1,
            option_text='4',
            is_correct=True,
            order=1
        )
        
        AnswerOption.objects.create(
            question=self.question1,
            option_text='3',
            is_correct=False,
            order=2
        )
    
    def test_calculate_score(self):
        """Test score calculation method."""
        # Create session
        session = UserTestSession.objects.create(
            user=self.user,
            test_bank=self.test_bank,
            total_questions=1,
            correct_answers=1
        )
        
        # Calculate score
        score = session.calculate_score()
        
        # Should be 100%
        self.assertEqual(score, Decimal('100.00'))
    
    def test_calculate_score_zero_questions(self):
        """Test score calculation with zero questions."""
        session = UserTestSession.objects.create(
            user=self.user,
            test_bank=self.test_bank,
            total_questions=0,
            correct_answers=0
        )
        
        score = session.calculate_score()
        
        # Should return None
        self.assertIsNone(score)
    
    def test_is_completed(self):
        """Test is_completed method."""
        session = UserTestSession.objects.create(
            user=self.user,
            test_bank=self.test_bank,
            status='completed'
        )
        
        self.assertTrue(session.is_completed())


class UserAnswerModelTest(TestCase):
    """Test UserAnswer model correctness checking."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.test_bank = TestBank.objects.create(
            category=self.category,
            title='Test Bank',
            slug='test-bank',
            description='Test',
            price=Decimal('29.99')
        )
        
        self.session = UserTestSession.objects.create(
            user=self.user,
            test_bank=self.test_bank
        )
        
        self.question = Question.objects.create(
            test_bank=self.test_bank,
            question_text='What is 2+2?',
            question_type='mcq_single',
            order=1
        )
        
        self.correct_option = AnswerOption.objects.create(
            question=self.question,
            option_text='4',
            is_correct=True,
            order=1
        )
        
        self.incorrect_option = AnswerOption.objects.create(
            question=self.question,
            option_text='3',
            is_correct=False,
            order=2
        )
    
    def test_check_correctness_single_correct(self):
        """Test correctness checking for MCQ single with correct answer."""
        answer = UserAnswer.objects.create(
            session=self.session,
            question=self.question
        )
        answer.selected_options.add(self.correct_option)
        
        is_correct = answer.check_correctness()
        self.assertTrue(is_correct)
    
    def test_check_correctness_single_incorrect(self):
        """Test correctness checking for MCQ single with incorrect answer."""
        answer = UserAnswer.objects.create(
            session=self.session,
            question=self.question
        )
        answer.selected_options.add(self.incorrect_option)
        
        is_correct = answer.check_correctness()
        self.assertFalse(is_correct)


class UserTestAccessModelTest(TestCase):
    """Test UserTestAccess model validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.test_bank = TestBank.objects.create(
            category=self.category,
            title='Test Bank',
            slug='test-bank',
            description='Test',
            price=Decimal('29.99')
        )
    
    def test_is_valid_active(self):
        """Test is_valid method for active access."""
        access = UserTestAccess.objects.create(
            user=self.user,
            test_bank=self.test_bank,
            is_active=True
        )
        
        self.assertTrue(access.is_valid())
    
    def test_is_valid_inactive(self):
        """Test is_valid method for inactive access."""
        access = UserTestAccess.objects.create(
            user=self.user,
            test_bank=self.test_bank,
            is_active=False
        )
        
        self.assertFalse(access.is_valid())

