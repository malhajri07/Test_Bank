"""
Tests for API views.

Uses factory_boy for test data.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from catalog.factories import CategoryFactory, CertificationFactory, TestBankFactory


@pytest.fixture
def api_client():
    """Return API client."""
    return APIClient()


@pytest.mark.django_db
class TestCategoryListAPI:
    """Tests for /api/v1/categories/."""

    def test_list_categories_empty(self, api_client):
        """Empty list returns 200."""
        response = api_client.get('/api/v1/categories/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert results == []

    def test_list_categories_with_data(self, api_client):
        """List returns categories."""
        CategoryFactory(name='AWS', slug='aws')
        response = api_client.get('/api/v1/categories/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 1
        assert results[0]['name'] == 'AWS'
        assert results[0]['slug'] == 'aws'


@pytest.mark.django_db
class TestCertificationListAPI:
    """Tests for /api/v1/certifications/."""

    def test_list_certifications_empty(self, api_client):
        """Empty list returns 200."""
        response = api_client.get('/api/v1/certifications/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert results == []

    def test_list_certifications_with_data(self, api_client):
        """List returns certifications."""
        CertificationFactory(name='AWS SAA', slug='aws-saa')
        response = api_client.get('/api/v1/certifications/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
        names = [c['name'] for c in results]
        assert 'AWS SAA' in names


@pytest.mark.django_db
class TestTestBankListAPI:
    """Tests for /api/v1/test-banks/."""

    def test_list_testbanks_empty(self, api_client):
        """Empty list returns 200."""
        response = api_client.get('/api/v1/test-banks/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert results == []

    def test_list_testbanks_with_data(self, api_client):
        """List returns active test banks."""
        TestBankFactory(title='PMP Practice', slug='pmp-practice', is_active=True)
        response = api_client.get('/api/v1/test-banks/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 1
        titles = [t['title'] for t in results]
        assert 'PMP Practice' in titles

    def test_list_excludes_inactive(self, api_client):
        """Inactive test banks are excluded."""
        TestBankFactory(title='Inactive Bank', slug='inactive-bank', is_active=False)
        response = api_client.get('/api/v1/test-banks/')
        results = response.data.get('results', response.data)
        titles = [t['title'] for t in results]
        assert 'Inactive Bank' not in titles


@pytest.mark.django_db
class TestTestBankDetailAPI:
    """Tests for /api/v1/test-banks/<slug>/."""

    def test_detail_returns_200(self, api_client):
        """Detail returns test bank by slug."""
        tb = TestBankFactory(title='CCNA Practice', slug='ccna-practice', is_active=True)
        response = api_client.get('/api/v1/test-banks/ccna-practice/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'CCNA Practice'
        assert response.data['slug'] == 'ccna-practice'

    def test_detail_404_for_invalid_slug(self, api_client):
        """Invalid slug returns 404."""
        response = api_client.get('/api/v1/test-banks/nonexistent/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
