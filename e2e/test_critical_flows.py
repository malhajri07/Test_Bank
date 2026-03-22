"""
E2E tests for critical user flows.

Per 04_QA_Eng.md: signup, browse catalog, purchase, exam, attempt exhaustion.
"""

import pytest
from django.urls import reverse
from playwright.sync_api import Page, expect

from catalog.factories import CategoryFactory, CertificationFactory, TestBankFactory
from catalog.models import Question
from accounts.factories import UserFactory


@pytest.fixture
def catalog_data(db):
    """Create catalog data for E2E tests."""
    cat = CategoryFactory(name='AWS', slug='aws')
    cert = CertificationFactory(name='AWS SAA', slug='aws-saa', category=cat)
    tb = TestBankFactory(
        title='AWS SAA Practice',
        slug='aws-saa-practice',
        category=cat,
        is_active=True,
    )
    from catalog.models import AnswerOption
    q = Question.objects.create(
        test_bank=tb,
        question_text='What is AWS?',
        question_type='mcq_single',
        order=1,
        is_active=True,
    )
    AnswerOption.objects.create(question=q, option_text='Cloud provider', is_correct=True, order=1)
    AnswerOption.objects.create(question=q, option_text='Database', is_correct=False, order=2)
    return {'category': cat, 'certification': cert, 'test_bank': tb}


@pytest.mark.django_db
class TestLandingAndCatalog:
    """E2E: Landing page and catalog browse."""

    def test_landing_page_loads(self, page: Page, live_server):
        """Landing page loads and shows key content."""
        page.goto(live_server.url + '/')
        expect(page).to_have_title(/Exam Stellar/)
        expect(page.locator("body")).to_contain_text("Exam")

    def test_catalog_browse(self, page: Page, live_server, catalog_data):
        """User can browse categories and test banks."""
        page.goto(live_server.url + '/')
        page.goto(live_server.url + '/categories/')
        expect(page.locator("body")).to_contain_text("AWS")
        page.goto(live_server.url + '/test-banks/')
        expect(page.locator("body")).to_contain_text("AWS SAA Practice")


@pytest.mark.django_db
class TestAuthFlow:
    """E2E: Signup and login."""

    def test_login_page(self, page: Page, live_server):
        """Login page loads."""
        page.goto(live_server.url + reverse('accounts:login'))
        expect(page.locator("form")).to_be_visible()

    def test_login_success(self, page: Page, live_server):
        """User can log in."""
        user = UserFactory(username='e2euser', password='testpass123')
        page.goto(live_server.url + reverse('accounts:login'))
        page.fill('input[name="username"]', 'e2euser')
        page.fill('input[name="password"]', 'testpass123')
        page.click('button[type="submit"]')
        page.wait_for_url('**/dashboard/**', timeout=5000)
        expect(page.locator("body")).to_contain_text("Dashboard")


@pytest.mark.django_db
class TestExamInterface:
    """E2E: Test bank detail and exam access."""

    def test_testbank_detail_loads(self, page: Page, live_server, catalog_data):
        """Test bank detail page loads with expected content."""
        tb = catalog_data['test_bank']
        page.goto(live_server.url + reverse('catalog:testbank_detail', kwargs={'slug': tb.slug}))
        expect(page.locator("body")).to_contain_text("AWS SAA Practice")
