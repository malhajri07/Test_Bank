"""
Tests for payments app views.

Tests for:
- Payment success handling
- Error handling
- Security checks
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from catalog.models import TestBank, Category
from payments.models import Payment
import json

User = get_user_model()


class PaymentViewsTestCase(TestCase):
    """Test payment views."""
    
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
            title='Test Bank',
            slug='test-bank',
            description='Test description',
            category=self.category,
            price=10.00,
            is_active=True
        )
    
    def test_payment_success_no_session_id(self):
        """Test payment success view without session_id."""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('payments:payment_success')
        response = self.client.get(url)
        
        # Should redirect to dashboard with error message
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:dashboard'))
