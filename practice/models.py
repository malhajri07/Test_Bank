"""
Practice app models for user test sessions, access control, and answers.

This module defines models for:
- UserTestAccess: Tracks which users have purchased access to which test banks
- UserTestSession: Represents a practice attempt/session
- UserAnswer: Stores user's answers to individual questions
"""

from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from catalog.models import TestBank, Question, AnswerOption
from decimal import Decimal

User = get_user_model()


class UserTestAccess(models.Model):
    """
    UserTestAccess model representing user's purchased access to a test bank.
    
    This model tracks which users have purchased and have active access to which test banks.
    Access is granted when a user successfully purchases a test bank.
    
    Features:
    - Tracks purchase timestamp
    - Supports future subscription expiry via expires_at field
    - is_active flag allows deactivating access without deleting record
    """
    
    # ForeignKey to User - tracks which user has access
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='test_accesses',
        verbose_name='User',
        help_text='User who has access'
    )
    
    # ForeignKey to TestBank - tracks which test bank user has access to
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='user_accesses',
        verbose_name='Test Bank',
        help_text='Test bank user has access to'
    )
    
    # Timestamp when access was purchased/granted
    purchased_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Purchased At',
        help_text='When access was granted'
    )
    
    # Optional expiry date for subscription-based access
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Expires At',
        help_text='When access expires (null for lifetime access)'
    )
    
    # Active flag - allows deactivating access without deleting
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Whether access is currently active'
    )
    
    class Meta:
        """Meta options for UserTestAccess model."""
        verbose_name = 'User Test Access'
        verbose_name_plural = 'User Test Accesses'
        ordering = ['-purchased_at']
        # Ensure one access record per user-test_bank combination
        unique_together = ['user', 'test_bank']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['test_bank', 'is_active']),
        ]
    
    def __str__(self):
        """String representation of the access."""
        return f"{self.user.username} - {self.test_bank.title}"
    
    def is_valid(self):
        """
        Check if access is currently valid.
        
        Returns True if:
        - is_active is True
        - expires_at is None (lifetime access) OR expires_at is in the future
        """
        if not self.is_active:
            return False
        if self.expires_at is None:
            return True
        from django.utils import timezone
        return self.expires_at > timezone.now()


class UserTestSession(models.Model):
    """
    UserTestSession model representing a practice attempt/session.
    
    This model tracks each time a user practices a test bank:
    - When session started and completed
    - Score and performance metrics
    - Status (in_progress, completed)
    - Duration tracking
    
    Users can have multiple sessions for the same test bank to track progress over time.
    """
    
    # ForeignKey to User - tracks which user's session
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='test_sessions',
        verbose_name='User',
        help_text='User who is practicing'
    )
    
    # ForeignKey to TestBank - tracks which test bank is being practiced
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='user_sessions',
        verbose_name='Test Bank',
        help_text='Test bank being practiced'
    )
    
    # Session start timestamp
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Started At',
        help_text='When the practice session started'
    )
    
    # Session completion timestamp (null if not completed)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completed At',
        help_text='When the practice session was completed'
    )
    
    # Score as percentage (0-100)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Score',
        help_text='Score as percentage (0-100)'
    )
    
    # Total number of questions in this session
    total_questions = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Questions',
        help_text='Total number of questions answered'
    )
    
    # Number of correct answers
    correct_answers = models.PositiveIntegerField(
        default=0,
        verbose_name='Correct Answers',
        help_text='Number of correct answers'
    )
    
    # Session status choices
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name='Status',
        help_text='Current status of the session'
    )
    
    # Optional duration tracking in seconds
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Duration (seconds)',
        help_text='Total duration of the session in seconds'
    )
    
    # Store randomized question order as JSON list of question IDs
    question_order = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Question Order',
        help_text='Randomized order of question IDs for this session'
    )
    
    class Meta:
        """Meta options for UserTestSession model."""
        verbose_name = 'User Test Session'
        verbose_name_plural = 'User Test Sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'test_bank', 'status']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        """String representation of the session."""
        return f"{self.user.username} - {self.test_bank.title} - {self.started_at}"
    
    def calculate_score(self):
        """
        Calculate score percentage based on correct answers and total questions.
        
        Returns:
            Decimal: Score as percentage (0-100), or None if no questions answered
        """
        if self.total_questions == 0:
            return None
        
        # Calculate percentage: (correct / total) * 100
        score_percentage = (Decimal(self.correct_answers) / Decimal(self.total_questions)) * 100
        return score_percentage.quantize(Decimal('0.01'))  # Round to 2 decimal places
    
    def is_completed(self):
        """Check if session is completed."""
        return self.status == 'completed' and self.completed_at is not None
    
    def get_absolute_url(self):
        """Get URL for session results page."""
        return reverse('practice:results', kwargs={'session_id': self.pk})


class UserAnswer(models.Model):
    """
    UserAnswer model storing user's answers to individual questions.
    
    This model tracks:
    - Which question was answered
    - Which answer option(s) the user selected
    - Whether the answer was correct
    - When the answer was submitted
    
    Supports multiple answer options for MCQ multi questions via ManyToMany relationship.
    """
    
    # ForeignKey to UserTestSession - links answer to a specific practice session
    session = models.ForeignKey(
        UserTestSession,
        on_delete=models.CASCADE,
        related_name='user_answers',
        verbose_name='Session',
        help_text='Practice session this answer belongs to'
    )
    
    # ForeignKey to Question - tracks which question was answered
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='user_answers',
        verbose_name='Question',
        help_text='Question that was answered'
    )
    
    # ManyToMany to AnswerOption - supports multiple selections for MCQ multi
    # For MCQ single, only one option should be selected
    selected_options = models.ManyToManyField(
        AnswerOption,
        related_name='user_answers',
        verbose_name='Selected Options',
        help_text='Answer options selected by the user'
    )
    
    # Boolean flag indicating if the answer was correct
    is_correct = models.BooleanField(
        default=False,
        verbose_name='Is Correct',
        help_text='Whether the answer is correct'
    )
    
    # Timestamp when answer was submitted
    answered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Answered At',
        help_text='When the answer was submitted'
    )
    
    class Meta:
        """Meta options for UserAnswer model."""
        verbose_name = 'User Answer'
        verbose_name_plural = 'User Answers'
        ordering = ['answered_at']
        # Ensure one answer per question per session
        unique_together = ['session', 'question']
        indexes = [
            models.Index(fields=['session', 'question']),
        ]
    
    def __str__(self):
        """String representation of the answer."""
        return f"{self.session} - {self.question} - {'Correct' if self.is_correct else 'Incorrect'}"
    
    def check_correctness(self):
        """
        Check if the selected answer(s) are correct.
        
        Logic:
        - For MCQ single: Exactly one correct option must be selected
        - For MCQ multi: All correct options must be selected, no incorrect ones
        - For True/False: Selected option must be correct
        
        Returns:
            bool: True if answer is correct, False otherwise
        """
        selected = set(self.selected_options.all())
        correct_options = set(self.question.get_correct_answers())
        
        if self.question.question_type == 'mcq_single':
            # For single choice: must select exactly one option and it must be correct
            return len(selected) == 1 and selected == correct_options
        
        elif self.question.question_type == 'mcq_multi':
            # For multiple choice: must select all correct options and no incorrect ones
            return selected == correct_options
        
        elif self.question.question_type == 'true_false':
            # For True/False: must select the correct option
            return len(selected) == 1 and selected == correct_options
        
        return False
