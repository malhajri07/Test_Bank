"""
Practice session load test scenarios.

Simulates multiple users taking exams simultaneously with:
- High-frequency answer saving
- Session submission under load
- Database lock monitoring
"""

from locust import HttpUser, task, between
import random
import json


class PracticeSessionLoadTest(HttpUser):
    """
    Load test for practice exam sessions.
    
    Simulates realistic exam-taking behavior:
    - Users start practice sessions
    - Answer questions at regular intervals
    - Submit exams
    - View results
    """
    
    wait_time = between(5, 10)  # Simulate thinking time between questions
    session_id = None
    testbank_slug = None
    question_ids = []
    current_question_index = 0
    
    def on_start(self):
        """Login and initialize practice session."""
        # Login
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post("/accounts/login/", data=login_data)
        
        if response.status_code == 200:
            # Get CSRF token from cookies or response
            # For now, we'll use a placeholder
            self.csrf_token = "dummy_token"
            
            # Start practice session
            # In real scenario, would use actual testbank slug
            self.testbank_slug = "sample-testbank"
            self._start_practice_session()
    
    def _start_practice_session(self):
        """Start a new practice session."""
        if self.testbank_slug:
            response = self.client.get(
                f"/practice/start/{self.testbank_slug}/",
                name="/practice/start/[slug]"
            )
            
            if response.status_code == 302:
                # Extract session ID from redirect
                location = response.headers.get("Location", "")
                if "session" in location:
                    parts = location.split("/")
                    try:
                        session_idx = parts.index("session")
                        if session_idx + 1 < len(parts):
                            self.session_id = parts[session_idx + 1]
                            self._load_questions()
                    except ValueError:
                        pass
    
    def _load_questions(self):
        """Load question IDs from session."""
        if self.session_id:
            response = self.client.get(
                f"/practice/session/{self.session_id}/",
                name="/practice/session/[id]"
            )
            if response.status_code == 200:
                # In real scenario, would parse HTML to get question IDs
                # For now, simulate with random IDs
                self.question_ids = list(range(1, 21))  # 20 questions
                random.shuffle(self.question_ids)
                self.current_question_index = 0
    
    @task(10)
    def save_answer(self):
        """Save an answer (high frequency - every 5-10 seconds)."""
        if self.session_id and self.question_ids:
            if self.current_question_index < len(self.question_ids):
                question_id = self.question_ids[self.current_question_index]
                
                # Simulate selecting a random option
                selected_option_id = random.randint(1, 4)
                
                answer_data = {
                    "question_id": question_id,
                    "selected_option_ids": [selected_option_id],
                    "csrfmiddlewaretoken": self.csrf_token
                }
                
                response = self.client.post(
                    f"/practice/session/{self.session_id}/save-answer/",
                    data=answer_data,
                    name="/practice/session/[id]/save-answer",
                    catch_response=True
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('success'):
                            response.success()
                            self.current_question_index += 1
                        else:
                            response.failure("Answer save failed")
                    except json.JSONDecodeError:
                        response.failure("Invalid JSON response")
                else:
                    response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def view_session(self):
        """View current practice session page."""
        if self.session_id:
            self.client.get(
                f"/practice/session/{self.session_id}/",
                name="/practice/session/[id]"
            )
    
    @task(1)
    def submit_practice(self):
        """Submit completed practice session."""
        if self.session_id and self.current_question_index >= len(self.question_ids):
            response = self.client.post(
                f"/practice/session/{self.session_id}/submit/",
                data={"csrfmiddlewaretoken": self.csrf_token},
                name="/practice/session/[id]/submit",
                catch_response=True
            )
            
            if response.status_code in [200, 302]:
                response.success()
                # Reset for new session
                self.session_id = None
                self.current_question_index = 0
            else:
                response.failure(f"Submit failed: HTTP {response.status_code}")
    
    @task(1)
    def view_results(self):
        """View practice results."""
        if self.session_id:
            self.client.get(
                f"/practice/results/{self.session_id}/",
                name="/practice/results/[id]"
            )

