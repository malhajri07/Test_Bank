"""
Tests for practice app views.

Tests cover:
- Starting practice (requires purchase)
- Preventing access when user has not purchased
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from catalog.models import Category, TestBank, Question, AnswerOption
from practice.models import UserTestAccess

User = get_user_model()


class PracticeViewsTest(TestCase):
    """Test practice views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
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
            price=Decimal('29.99'),
            difficulty_level='easy',
            is_active=True
        )
        
        self.question = Question.objects.create(
            test_bank=self.test_bank,
            question_text='Test Question',
            question_type='mcq_single',
            order=1,
            is_active=True
        )
        
        AnswerOption.objects.create(
            question=self.question,
            option_text='Option 1',
            is_correct=True,
            order=1
        )
    
    def test_start_practice_without_access(self):
        """Test starting practice without purchase access."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(f'/practice/start/{self.test_bank.slug}/')
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
    
    def test_start_practice_with_access(self):
        """Test starting practice with purchase access."""
        # Create access
        UserTestAccess.objects.create(
            user=self.user,
            test_bank=self.test_bank,
            is_active=True
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(f'/practice/start/{self.test_bank.slug}/')
        
        # Should redirect to practice session
        self.assertEqual(response.status_code, 302)
        self.assertIn('/practice/session/', response.url)

