"""Tests for testbank_platform (health endpoints)."""

from django.test import Client, TestCase


class HealthEndpointsTest(TestCase):
    """Test health check endpoints."""

    def test_healthz_returns_200(self):
        """Liveness probe returns 200."""
        response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_readyz_returns_200_when_db_ok(self):
        """Readiness probe returns 200 when DB is connected."""
        response = self.client.get('/readyz/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['database'], 'connected')
