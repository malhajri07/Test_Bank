"""
Tests for practice app models.

Tests cover:
- UserTestSession score calculation
- UserAnswer correctness checking
- UserTestAccess validation
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import AnswerOption, Category, Question, TestBank
from practice.models import UserAnswer, UserTestAccess, UserTestSession

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
            difficulty_level='easy'
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
        from django.utils import timezone
        session = UserTestSession.objects.create(
            user=self.user,
            test_bank=self.test_bank,
            status='completed',
            completed_at=timezone.now()
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


class UserAnswerSnapshotTest(TestCase):
    """Ensure UserAnswer freezes question/option content at answer time.

    Guards against admin edits to a Question or AnswerOption silently
    rewriting what appears on a user's past results page.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='snapuser', email='snap@example.com', password='pw'
        )
        self.category = Category.objects.create(
            name='Snap Cat', slug='snap-cat', description='cat'
        )
        self.test_bank = TestBank.objects.create(
            category=self.category, title='Snap Bank', slug='snap-bank',
            description='bank desc', price=Decimal('0'), difficulty_level='easy',
        )
        self.question = Question.objects.create(
            test_bank=self.test_bank,
            question_text='Capital of France?',
            question_type='mcq_single',
            explanation='Paris is correct.',
            order=1,
        )
        self.opt_a = AnswerOption.objects.create(
            question=self.question, option_text='Paris', is_correct=True, order=1,
        )
        self.opt_b = AnswerOption.objects.create(
            question=self.question, option_text='London', is_correct=False, order=2,
        )
        self.session = UserTestSession.objects.create(
            user=self.user, test_bank=self.test_bank, total_questions=1,
        )

    def _answer_and_snapshot(self, selected):
        answer = UserAnswer.objects.create(
            session=self.session, question=self.question, is_correct=False,
        )
        answer.selected_options.set(selected)
        answer.is_correct = answer.check_correctness()
        answer.question_snapshot = answer.build_snapshot()
        answer.save()
        return answer

    def test_snapshot_captures_question_and_options(self):
        """Snapshot includes live question text, options, and flags."""
        answer = self._answer_and_snapshot([self.opt_a])
        snap = answer.question_snapshot
        self.assertEqual(snap['question_text'], 'Capital of France?')
        self.assertEqual(snap['question_type'], 'mcq_single')
        self.assertEqual(snap['explanation'], 'Paris is correct.')
        self.assertEqual(len(snap['options']), 2)
        self.assertEqual(snap['selected_option_ids'], [self.opt_a.id])
        self.assertEqual(snap['correct_option_ids'], [self.opt_a.id])

    def test_snapshot_survives_question_edit(self):
        """Editing the Question row after the fact must not change the snapshot."""
        answer = self._answer_and_snapshot([self.opt_a])
        original_text = answer.question_snapshot['question_text']

        # Admin rewrites the question after the user finished
        self.question.question_text = 'REWRITTEN: Capital of Spain?'
        self.question.explanation = 'REWRITTEN: Madrid.'
        self.question.save()

        answer.refresh_from_db()
        self.assertEqual(answer.question_snapshot['question_text'], original_text)
        self.assertEqual(answer.question_snapshot['explanation'], 'Paris is correct.')

    def test_snapshot_survives_option_correctness_flip(self):
        """Flipping AnswerOption.is_correct must not change past correctness."""
        answer = self._answer_and_snapshot([self.opt_a])
        self.assertTrue(answer.is_correct)

        # Admin "fixes" a question by flipping the correct flag
        self.opt_a.is_correct = False
        self.opt_a.save()
        self.opt_b.is_correct = True
        self.opt_b.save()

        answer.refresh_from_db()
        # Snapshot still records the opt_a was the correct one at answer time
        self.assertEqual(answer.question_snapshot['correct_option_ids'], [self.opt_a.id])
        # The cached is_correct on the row stays true (wasn't recomputed)
        self.assertTrue(answer.is_correct)

    def test_snapshot_captures_domain_name(self):
        """Snapshot freezes the QuestionDomain name for per-domain analytics."""
        from catalog.models import QuestionDomain
        domain = QuestionDomain.objects.create(
            test_bank=self.test_bank, name='Geography', slug='geography', order=0,
        )
        self.question.domain = domain
        self.question.save()

        answer = self._answer_and_snapshot([self.opt_a])
        self.assertEqual(answer.question_snapshot['domain_id'], domain.id)
        self.assertEqual(answer.question_snapshot['domain_name'], 'Geography')

        # Rename the domain after the fact — snapshot stays frozen
        domain.name = 'World Geography (renamed)'
        domain.save()
        answer.refresh_from_db()
        self.assertEqual(answer.question_snapshot['domain_name'], 'Geography')

    def test_snapshot_handles_missing_domain(self):
        """Questions without a domain still produce a valid snapshot."""
        # self.question.domain is None in setUp
        answer = self._answer_and_snapshot([self.opt_a])
        self.assertIsNone(answer.question_snapshot['domain_id'])
        self.assertIsNone(answer.question_snapshot['domain_name'])

