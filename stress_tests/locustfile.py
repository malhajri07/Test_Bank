"""
Locust load testing scenarios for Exam Stellar Django application.

This file defines user behaviors and load test scenarios for:
- Anonymous browsing
- Authenticated user flows
- Practice exam sessions
- Payment processing

Usage:
    locust -f locustfile.py --host=http://localhost:8000
    locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=5 --run-time=10m
"""

from locust import HttpUser, task, between, SequentialTaskSet
import random
import json


class AnonymousBrowsingUser(HttpUser):
    """
    Simulates anonymous users browsing the catalog.
    
    Behavior:
    - Browse homepage
    - View category list
    - View test bank detail pages
    """
    
    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks
    
    @task(3)
    def browse_homepage(self):
        """Browse the homepage."""
        self.client.get("/")
    
    @task(2)
    def browse_categories(self):
        """Browse category list."""
        self.client.get("/categories/")
    
    @task(1)
    def view_category_detail(self):
        """View a category detail page."""
        # This would need actual category slugs - simplified for now
        self.client.get("/categories/", name="/categories/[category]")
    
    @task(1)
    def view_testbank_detail(self):
        """View a test bank detail page."""
        # This would need actual test bank slugs - simplified for now
        self.client.get("/categories/", name="/categories/[category]/test-banks/[testbank]")


class AuthenticatedUser(HttpUser):
    """
    Simulates authenticated users performing various actions.
    
    Behavior:
    - Login
    - Browse dashboard
    - View test banks
    - Start practice sessions
    """
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login when user starts."""
        # Create or use test user credentials
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/accounts/login/", data=login_data)
        if response.status_code == 200:
            # Extract CSRF token if needed
            pass
    
    @task(3)
    def view_dashboard(self):
        """View user dashboard."""
        self.client.get("/accounts/dashboard/")
    
    @task(2)
    def browse_catalog(self):
        """Browse catalog while logged in."""
        self.client.get("/categories/")
    
    @task(1)
    def view_profile(self):
        """View user profile."""
        # Would need actual user ID
        self.client.get("/accounts/profile/1/")


class PracticeExamUser(HttpUser):
    """
    Simulates users taking practice exams.
    
    Behavior:
    - Start practice session
    - View questions
    - Save answers (high frequency)
    - Submit exam
    - View results
    """
    
    wait_time = between(1, 2)
    session_id = None
    testbank_slug = None
    
    def on_start(self):
        """Login and start a practice session."""
        # Login
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        self.client.post("/accounts/login/", data=login_data)
        
        # Start practice session (would need actual testbank slug)
        # For now, we'll simulate the flow
        self.testbank_slug = "sample-testbank"
    
    @task(1)
    def start_practice(self):
        """Start a new practice session."""
        if self.testbank_slug:
            response = self.client.get(f"/practice/start/{self.testbank_slug}/", name="/practice/start/[slug]")
            if response.status_code == 302:
                # Extract session ID from redirect
                location = response.headers.get("Location", "")
                if "session" in location:
                    parts = location.split("/")
                    for i, part in enumerate(parts):
                        if part == "session" and i + 1 < len(parts):
                            self.session_id = parts[i + 1]
                            break
    
    @task(5)
    def view_practice_session(self):
        """View practice session page."""
        if self.session_id:
            self.client.get(f"/practice/session/{self.session_id}/", name="/practice/session/[id]")
    
    @task(10)
    def save_answer(self):
        """Save an answer (high frequency AJAX call)."""
        if self.session_id:
            # Simulate saving an answer
            answer_data = {
                "question_id": random.randint(1, 100),
                "selected_option_ids": [random.randint(1, 5)],
                "csrfmiddlewaretoken": "dummy_token"  # Would need real CSRF token
            }
            self.client.post(
                f"/practice/session/{self.session_id}/save-answer/",
                data=answer_data,
                name="/practice/session/[id]/save-answer"
            )
    
    @task(1)
    def submit_practice(self):
        """Submit completed practice session."""
        if self.session_id:
            self.client.post(
                f"/practice/session/{self.session_id}/submit/",
                data={"csrfmiddlewaretoken": "dummy_token"},
                name="/practice/session/[id]/submit"
            )
    
    @task(1)
    def view_results(self):
        """View practice results."""
        if self.session_id:
            self.client.get(f"/practice/results/{self.session_id}/", name="/practice/results/[id]")


class PaymentUser(HttpUser):
    """
    Simulates users going through payment flow.
    
    Behavior:
    - Browse test bank
    - Initiate checkout
    - Complete payment (simulated)
    """
    
    wait_time = between(3, 7)
    
    def on_start(self):
        """Login when user starts."""
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        self.client.post("/accounts/login/", data=login_data)
    
    @task(2)
    def browse_testbank(self):
        """Browse a test bank detail page."""
        self.client.get("/categories/", name="/categories/[category]/test-banks/[testbank]")
    
    @task(1)
    def initiate_checkout(self):
        """Initiate checkout process."""
        testbank_slug = "sample-testbank"
        self.client.get(f"/payments/checkout/{testbank_slug}/", name="/payments/checkout/[slug]")


class MixedTrafficUser(HttpUser):
    """
    Simulates mixed traffic combining all user types.
    
    This is useful for realistic load testing.
    """
    
    wait_time = between(1, 5)
    
    def on_start(self):
        """Randomly decide if user is authenticated."""
        self.is_authenticated = random.choice([True, False])
        if self.is_authenticated:
            login_data = {
                "username": "testuser",
                "password": "testpass123"
            }
            self.client.post("/accounts/login/", data=login_data)
    
    @task(5)
    def browse_homepage(self):
        """Browse homepage."""
        self.client.get("/")
    
    @task(3)
    def browse_categories(self):
        """Browse categories."""
        self.client.get("/categories/")
    
    @task(2)
    def view_dashboard(self):
        """View dashboard if authenticated."""
        if self.is_authenticated:
            self.client.get("/accounts/dashboard/")
    
    @task(1)
    def view_testbank(self):
        """View test bank detail."""
        self.client.get("/categories/", name="/categories/[category]/test-banks/[testbank]")

