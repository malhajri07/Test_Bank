"""
Tests for payments app models.

Tests for Order, OrderItem, Coupon, CouponProduct.
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from catalog.models import Category, TestBank
from payments.models import Coupon, CouponProduct, Order, OrderItem


class OrderModelTest(TestCase):
    """Test Order and OrderItem models."""

    def setUp(self):
        self.category = Category.objects.create(name='Test', slug='test')
        self.test_bank = TestBank.objects.create(
            category=self.category,
            title='Test Bank',
            slug='test-bank',
            description='Test',
            price=Decimal('29.99'),
            is_active=True,
        )

    def test_order_creates_order_number(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user('u', 'u@t.com', 'p')
        order = Order.objects.create(user=user, subtotal=Decimal('10'), currency='usd')
        self.assertTrue(len(order.order_number) == 36)
        self.assertIn('-', order.order_number)

    def test_order_item_line_total(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user('u', 'u@t.com', 'p')
        order = Order.objects.create(user=user, subtotal=Decimal('30'), currency='usd')
        item = OrderItem.objects.create(
            order=order,
            test_bank=self.test_bank,
            quantity=2,
            unit_price=Decimal('15.00'),
        )
        self.assertEqual(item.line_total, Decimal('30.00'))


class CouponModelTest(TestCase):
    """Test Coupon validation."""

    def setUp(self):
        self.category = Category.objects.create(name='Test', slug='test')
        self.test_bank = TestBank.objects.create(
            category=self.category,
            title='Test Bank',
            slug='test-bank',
            description='Test',
            price=Decimal('100.00'),
            is_active=True,
        )

    def test_coupon_percentage_discount(self):
        coupon = Coupon.objects.create(
            code='SAVE10',
            discount_type='percentage',
            discount_value=Decimal('10'),
            is_active=True,
        )
        discount, err = coupon.validate_for_order(subtotal=Decimal('100'))
        self.assertIsNone(err)
        self.assertEqual(discount, Decimal('10.00'))

    def test_coupon_fixed_discount(self):
        coupon = Coupon.objects.create(
            code='FLAT20',
            discount_type='fixed',
            discount_value=Decimal('20'),
            is_active=True,
        )
        discount, err = coupon.validate_for_order(subtotal=Decimal('100'))
        self.assertIsNone(err)
        self.assertEqual(discount, Decimal('20'))

    def test_coupon_inactive_rejected(self):
        coupon = Coupon.objects.create(
            code='INACTIVE',
            discount_type='percentage',
            discount_value=Decimal('10'),
            is_active=False,
        )
        discount, err = coupon.validate_for_order(subtotal=Decimal('100'))
        self.assertIsNotNone(err)
        self.assertEqual(discount, Decimal('0'))

    def test_coupon_max_uses_reached(self):
        coupon = Coupon.objects.create(
            code='LIMITED',
            discount_type='percentage',
            discount_value=Decimal('10'),
            max_uses=1,
            current_uses=1,
            is_active=True,
        )
        discount, err = coupon.validate_for_order(subtotal=Decimal('100'))
        self.assertIsNotNone(err)
        self.assertEqual(discount, Decimal('0'))
