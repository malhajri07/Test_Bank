"""
Catalog browsing load test scenarios.

Tests:
- High-frequency category browsing
- Test bank detail page views
- Search and filtering operations
- Caching effectiveness
"""

from locust import HttpUser, task, between
import random


class CatalogBrowsingLoadTest(HttpUser):
    """
    Load test for catalog browsing.
    
    Simulates users browsing categories and test banks.
    """
    
    wait_time = between(1, 3)  # Quick browsing
    
    @task(5)
    def browse_homepage(self):
        """Browse homepage."""
        self.client.get("/")
    
    @task(4)
    def browse_categories(self):
        """Browse category list."""
        self.client.get("/categories/")
    
    @task(3)
    def view_category_detail(self):
        """View category detail page."""
        # Would use actual category slugs in real scenario
        self.client.get("/categories/", name="/categories/[category]")
    
    @task(2)
    def view_testbank_detail(self):
        """View test bank detail page."""
        # Would use actual test bank slugs in real scenario
        self.client.get("/categories/", name="/categories/[category]/test-banks/[testbank]")
    
    @task(1)
    def browse_subcategories(self):
        """Browse subcategories."""
        self.client.get("/categories/", name="/categories/[category]/[subcategory]")


class AuthenticatedCatalogBrowsing(HttpUser):
    """
    Load test for authenticated catalog browsing.
    
    Includes dashboard access and personalized content.
    """
    
    wait_time = between(1, 4)
    
    def on_start(self):
        """Login when user starts."""
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        self.client.post("/accounts/login/", data=login_data)
    
    @task(3)
    def view_dashboard(self):
        """View user dashboard."""
        self.client.get("/accounts/dashboard/")
    
    @task(2)
    def browse_catalog(self):
        """Browse catalog while logged in."""
        self.client.get("/categories/")
    
    @task(1)
    def view_purchases(self):
        """View purchase list."""
        self.client.get("/payments/purchases/")

