"""
Security tests for catalog app.

Tests for:
- Rate limiting
- Input validation
- Authorization checks
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from catalog.models import TestBank, Category
import json

User = get_user_model()


class SecurityTestCase(TestCase):
    """Test security features."""
    
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
            title='Test Bank',
            slug='test-bank',
            description='Test description',
            category=self.category,
            price=10.00,
            is_active=True
        )
    
    def test_rate_test_bank_json_size_limit(self):
        """Test that JSON size limit is enforced."""
        self.client.login(username='testuser', password='testpass123')
        
        # Create a large JSON payload (> 1MB)
        large_data = {'rating': 5, 'data': 'x' * (1024 * 1024 + 1)}
        large_json = json.dumps(large_data)
        
        url = reverse('catalog:rate_test_bank', kwargs={'slug': self.test_bank.slug})
        response = self.client.post(
            url,
            data=large_json,
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 413)
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'error')
    
    def test_search_query_validation(self):
        """Test that search query validation works."""
        # Test empty query
        url = reverse('catalog:search')
        response = self.client.get(url, {'q': ''})
        self.assertEqual(response.status_code, 200)
        
        # Test query too short
        response = self.client.get(url, {'q': 'a'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        
        # Test valid query
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        # Error should be None for valid queries
        if 'error' in response.context:
            self.assertIsNone(response.context['error'])
