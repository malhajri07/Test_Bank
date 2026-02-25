"""
Tests for catalog app views.

Tests cover:
- Browsing test banks (authenticated/unauthenticated)
- Test bank detail page access
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from catalog.models import Category, TestBank

User = get_user_model()


class CatalogViewsTest(TestCase):
    """Test catalog views."""
    
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
            slug='test-category',
            description='Test description'
        )
        
        self.test_bank = TestBank.objects.create(
            category=self.category,
            title='Test Bank',
            slug='test-bank',
            description='Test description',
            price=Decimal('29.99'),
            difficulty_level='easy',
            is_active=True
        )
    
    def test_index_view(self):
        """Test landing page view."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Exam Stellar')
    
    def test_category_list_view(self):
        """Test category list view."""
        response = self.client.get('/categories/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)
    
    def test_testbank_list_view(self):
        """Test test bank list view."""
        response = self.client.get(f'/categories/{self.category.slug}/test-banks/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_bank.title)
    
    def test_testbank_detail_view(self):
        """Test test bank detail view."""
        response = self.client.get(f'/test-bank/{self.test_bank.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_bank.title)
        self.assertContains(response, self.test_bank.description)

