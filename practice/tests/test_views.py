"""
Tests for practice app views.

Tests cover:
- Starting practice (requires purchase)
- Preventing access when user has not purchased
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from catalog.models import AnswerOption, Category, Question, QuestionDomain, TestBank
from practice.models import UserAnswer, UserTestAccess, UserTestSession

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
        # Create access with attempts remaining
        UserTestAccess.objects.create(
            user=self.user,
            test_bank=self.test_bank,
            is_active=True,
            attempts_allowed=3,
            attempts_used=0,
        )

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(f'/practice/start/{self.test_bank.slug}/')

        # Should redirect to practice session
        self.assertEqual(response.status_code, 302)
        self.assertIn('/practice/session/', response.url)

    def test_start_practice_no_attempts_remaining(self):
        """Test that user cannot start practice when attempts exhausted."""
        UserTestAccess.objects.create(
            user=self.user,
            test_bank=self.test_bank,
            is_active=True,
            attempts_allowed=3,
            attempts_used=3,
        )

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(f'/practice/start/{self.test_bank.slug}/')

        # Should redirect back to test bank detail with error
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.test_bank.slug, response.url)


class PracticeResultsAnalyticsTest(TestCase):
    """Per-domain analytics on the results page."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='analuser', email='a@example.com', password='pw',
        )
        self.category = Category.objects.create(
            name='Ana Cat', slug='ana-cat', description='c',
        )
        self.test_bank = TestBank.objects.create(
            category=self.category, title='Ana Bank', slug='ana-bank',
            description='b', price=Decimal('0'), difficulty_level='easy',
            is_active=True,
        )
        UserTestAccess.objects.create(
            user=self.user, test_bank=self.test_bank, is_active=True,
            attempts_allowed=5, attempts_used=0,
        )

        # Two domains; questions are mixed between them with deliberately
        # different accuracy so the weak-areas logic has something to flag.
        self.domain_net = QuestionDomain.objects.create(
            test_bank=self.test_bank, name='Networking', slug='networking', order=0,
        )
        self.domain_sec = QuestionDomain.objects.create(
            test_bank=self.test_bank, name='Security', slug='security', order=1,
        )

        self.session = UserTestSession.objects.create(
            user=self.user, test_bank=self.test_bank, total_questions=0,
        )

        # 3 Networking questions — user gets all 3 wrong (0/3 = 0%, weak)
        for i in range(3):
            q = Question.objects.create(
                test_bank=self.test_bank, domain=self.domain_net,
                question_text=f'Net Q{i}', question_type='mcq_single',
                order=i, is_active=True,
            )
            correct = AnswerOption.objects.create(question=q, option_text='C', is_correct=True, order=1)
            wrong = AnswerOption.objects.create(question=q, option_text='W', is_correct=False, order=2)
            a = UserAnswer.objects.create(session=self.session, question=q)
            a.selected_options.set([wrong])
            a.is_correct = a.check_correctness()
            a.question_snapshot = a.build_snapshot()
            a.save()

        # 2 Security questions — user gets both right (2/2 = 100%, not weak)
        for i in range(2):
            q = Question.objects.create(
                test_bank=self.test_bank, domain=self.domain_sec,
                question_text=f'Sec Q{i}', question_type='mcq_single',
                order=10 + i, is_active=True,
            )
            correct = AnswerOption.objects.create(question=q, option_text='C', is_correct=True, order=1)
            AnswerOption.objects.create(question=q, option_text='W', is_correct=False, order=2)
            a = UserAnswer.objects.create(session=self.session, question=q)
            a.selected_options.set([correct])
            a.is_correct = a.check_correctness()
            a.question_snapshot = a.build_snapshot()
            a.save()

        # Finalize the session so /results/ will render it
        self.session.status = 'completed'
        self.session.total_questions = 5
        self.session.correct_answers = 2
        self.session.score = Decimal('40.00')
        from django.utils import timezone
        self.session.completed_at = timezone.now()
        self.session.save()

    def test_domain_breakdown_and_weak_areas(self):
        """Results page exposes per-domain breakdown and weak areas correctly."""
        self.client.login(username='analuser', password='pw')
        resp = self.client.get(f'/practice/results/{self.session.pk}/')
        self.assertEqual(resp.status_code, 200)

        breakdown = {row['domain']: row for row in resp.context['domain_breakdown']}
        self.assertEqual(breakdown['Networking']['total'], 3)
        self.assertEqual(breakdown['Networking']['correct'], 0)
        self.assertEqual(breakdown['Networking']['percentage'], 0.0)
        self.assertEqual(breakdown['Security']['total'], 2)
        self.assertEqual(breakdown['Security']['correct'], 2)
        self.assertEqual(breakdown['Security']['percentage'], 100.0)

        weak_names = {row['domain'] for row in resp.context['weak_areas']}
        self.assertIn('Networking', weak_names)
        self.assertNotIn('Security', weak_names)

    def test_renaming_domain_after_attempt_does_not_change_breakdown(self):
        """Snapshot freezes domain name — post-hoc rename doesn't reshape history."""
        self.client.login(username='analuser', password='pw')

        # Rename after the answers were recorded
        self.domain_net.name = 'Networking (v2)'
        self.domain_net.save()

        resp = self.client.get(f'/practice/results/{self.session.pk}/')
        breakdown = {row['domain']: row for row in resp.context['domain_breakdown']}
        # Frozen snapshot wins — we still see the original name
        self.assertIn('Networking', breakdown)
        self.assertNotIn('Networking (v2)', breakdown)

