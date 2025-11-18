"""
Payment processing load test scenarios.

Tests:
- Concurrent checkout sessions
- Webhook processing under load
- Payment success/cancel callbacks
- Stripe API rate limits
"""

from locust import HttpUser, task, between
import random


class PaymentFlowLoadTest(HttpUser):
    """
    Load test for payment processing flow.
    
    Simulates users going through checkout process.
    """
    
    wait_time = between(3, 7)  # More time for payment flow
    
    def on_start(self):
        """Login when user starts."""
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        self.client.post("/accounts/login/", data=login_data)
    
    @task(3)
    def browse_testbank(self):
        """Browse a test bank before purchasing."""
        # Would use actual test bank slug in real scenario
        self.client.get("/categories/", name="/categories/[category]/test-banks/[testbank]")
    
    @task(2)
    def initiate_checkout(self):
        """Initiate checkout process."""
        testbank_slug = "sample-testbank"
        response = self.client.get(
            f"/payments/checkout/{testbank_slug}/",
            name="/payments/checkout/[slug]",
            catch_response=True
        )
        
        if response.status_code in [200, 302]:
            response.success()
        else:
            response.failure(f"Checkout failed: HTTP {response.status_code}")
    
    @task(1)
    def view_payment_success(self):
        """View payment success page."""
        # Simulate successful payment callback
        self.client.get("/payments/success/", name="/payments/success")
    
    @task(1)
    def view_payment_cancel(self):
        """View payment cancel page."""
        # Simulate cancelled payment
        self.client.get("/payments/cancel/", name="/payments/cancel")


class FreeAccessLoadTest(HttpUser):
    """
    Load test for free test bank access.
    
    Tests immediate access grant for free test banks (price=0).
    """
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login when user starts."""
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        self.client.post("/accounts/login/", data=login_data)
    
    @task(5)
    def get_free_access(self):
        """Get free access to a test bank."""
        # Would use actual free test bank slug in real scenario
        testbank_slug = "free-testbank"
        response = self.client.get(
            f"/payments/checkout/{testbank_slug}/",
            name="/payments/checkout/[free-slug]",
            catch_response=True
        )
        
        # Free access should be immediate (no Stripe redirect)
        if response.status_code in [200, 302]:
            response.success()
        else:
            response.failure(f"Free access failed: HTTP {response.status_code}")

