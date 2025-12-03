"""
Catalog app models for test banks, categories, questions, and answer options.

This module defines the core domain models:
- Category: Organizes test banks by level (School, College, Professional)
- TestBank: A purchasable product containing questions
- Question: Individual questions within a test bank
- AnswerOption: Answer choices for questions
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Category(models.Model):
    """
    Category model for organizing test banks.
    
    Categories represent different levels of education/certification:
    - School level: K-12 education
    - College level: Undergraduate/Graduate
    - Professional: Certifications (PMP, KPIs, etc.)
    
    Uses slug field for clean URL routing (e.g., /categories/school-level/)
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Category Name',
        help_text='Name of the category (e.g., School, College, Professional)'
    )
    
    # Slug for URL-friendly routing
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug',
        help_text='URL-friendly version of the name'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Detailed description of the category'
    )
    
    # Category image/icon
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name='Category Image',
        help_text='Image/icon for the category card'
    )
    
    # Optional JSON field for additional metadata (level details, tags, etc.)
    level_details = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name='Level Details',
        help_text='Additional metadata as JSON (tags, requirements, etc.)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for Category model."""
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        """String representation of the category."""
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get URL for category's test banks list page."""
        return reverse('catalog:testbank_list', kwargs={'category_slug': self.slug})


class SubCategory(models.Model):
    """
    SubCategory model for organizing test banks within a category.
    
    SubCategories represent specialized areas within a main category.
    For example, under "Vocational" category, we might have:
    - Information Technology & Computer Skills
    - Business, Management & Office Skills
    - Finance, Accounting & Banking
    etc.
    
    Uses slug field for clean URL routing.
    """
    
    name = models.CharField(
        max_length=200,
        verbose_name='SubCategory Name',
        help_text='Name of the subcategory'
    )
    
    # Slug for URL-friendly routing
    slug = models.SlugField(
        max_length=200,
        verbose_name='Slug',
        help_text='URL-friendly version of the name'
    )
    
    # ForeignKey to Category - each subcategory belongs to one category
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name='Category',
        help_text='Category this subcategory belongs to'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Detailed description of the subcategory'
    )
    
    # Order field for custom ordering within category
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Order of this subcategory within the category'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for SubCategory model."""
        verbose_name = 'SubCategory'
        verbose_name_plural = 'SubCategories'
        ordering = ['order', 'name']
        unique_together = [['category', 'slug']]  # Slug unique within category
        indexes = [
            models.Index(fields=['category', 'order']),
        ]
    
    def __str__(self):
        """String representation of the subcategory."""
        return f"{self.category.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get URL for subcategory's certifications list page."""
        return reverse('catalog:subcategory_list', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.slug
        })


class Certification(models.Model):
    """
    Certification model for organizing test banks within a subcategory.
    
    Certifications represent specific professional certifications or exams.
    For example, under "IT Fundamentals / Support" subcategory, we might have:
    - CompTIA IT Fundamentals (ITF+)
    - CompTIA A+
    - CompTIA Network+
    etc.
    
    Uses slug field for clean URL routing.
    """
    
    name = models.CharField(
        max_length=200,
        verbose_name='Certification Name',
        help_text='Name of the certification or exam'
    )
    
    # Slug for URL-friendly routing
    slug = models.SlugField(
        max_length=200,
        verbose_name='Slug',
        help_text='URL-friendly version of the name'
    )
    
    # ForeignKey to SubCategory - each certification belongs to one subcategory
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name='certifications',
        verbose_name='SubCategory',
        help_text='SubCategory this certification belongs to'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Description',
        help_text='Detailed description of the certification'
    )
    
    # Order field for custom ordering within subcategory
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Order of this certification within the subcategory'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for Certification model."""
        verbose_name = 'Certification'
        verbose_name_plural = 'Certifications'
        ordering = ['order', 'name']
        unique_together = [['subcategory', 'slug']]  # Slug unique within subcategory
        indexes = [
            models.Index(fields=['subcategory', 'order']),
        ]
    
    def __str__(self):
        """String representation of the certification."""
        return f"{self.subcategory.category.name} - {self.subcategory.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get URL for certification's test banks list page."""
        return reverse('catalog:certification_list', kwargs={
            'category_slug': self.subcategory.category.slug,
            'subcategory_slug': self.subcategory.slug,
            'certification_slug': self.slug
        })


class TestBank(models.Model):
    """
    TestBank model representing a purchasable test bank product.
    
    A TestBank is a collection of questions that users can purchase and practice.
    Each TestBank can belong to:
    - A Category (top level)
    - A SubCategory (within a category)
    - A Certification (within a subcategory)
    
    At least one of category, subcategory, or certification must be assigned.
    
    Users purchase access to a TestBank, which grants them the ability to:
    - Practice questions multiple times
    - Review results and explanations
    - Track their progress
    """
    
    # ForeignKey to Category - each test bank can belong to a category
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='test_banks',
        verbose_name='Category',
        help_text='Category this test bank belongs to',
        null=True,
        blank=True
    )
    
    # ForeignKey to SubCategory - optional, for hierarchical organization
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name='test_banks',
        verbose_name='SubCategory',
        help_text='SubCategory this test bank belongs to (optional)',
        null=True,
        blank=True
    )
    
    # ForeignKey to Certification - optional, for specific certification exams
    certification = models.ForeignKey(
        Certification,
        on_delete=models.CASCADE,
        related_name='test_banks',
        verbose_name='Certification',
        help_text='Certification this test bank belongs to (optional)',
        null=True,
        blank=True
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='Title',
        help_text='Title of the test bank'
    )
    
    # Slug for URL-friendly routing
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Slug',
        help_text='URL-friendly version of the title'
    )
    
    description = models.TextField(
        verbose_name='Description',
        help_text='Detailed description of the test bank content'
    )
    
    # Test bank image/thumbnail
    image = models.ImageField(
        upload_to='testbanks/',
        blank=True,
        null=True,
        verbose_name='Test Bank Image',
        help_text='Image/thumbnail for the test bank card'
    )
    
    # Difficulty level choices
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('advanced', 'Advanced'),
    ]
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='easy',
        verbose_name='Difficulty Level',
        help_text='Difficulty level of the test bank'
    )
    
    # Price for purchasing access (in USD or configured currency)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Price',
        help_text='Price to purchase access to this test bank'
    )
    
    # Active flag - only active test banks are shown to users
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Whether this test bank is active and visible to users'
    )
    
    # Rating fields - cached for performance
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name='Average Rating',
        help_text='Average rating (0.00 to 5.00)'
    )
    
    total_ratings = models.PositiveIntegerField(
        default=0,
        verbose_name='Total Ratings',
        help_text='Total number of ratings received'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for TestBank model."""
        verbose_name = 'Test Bank'
        verbose_name_plural = 'Test Banks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['subcategory', 'is_active']),
            models.Index(fields=['certification', 'is_active']),
            models.Index(fields=['slug']),
        ]
    
    def clean(self):
        """Validate that at least one level (category, subcategory, or certification) is assigned."""
        from django.core.exceptions import ValidationError
        if not self.category and not self.subcategory and not self.certification:
            raise ValidationError('Test bank must belong to at least one level: category, subcategory, or certification.')
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided and validate."""
        if not self.slug:
            self.slug = slugify(self.title)
        # Auto-set category from subcategory or certification if not set
        if not self.category:
            if self.certification:
                self.category = self.certification.subcategory.category
            elif self.subcategory:
                self.category = self.subcategory.category
        self.full_clean()  # Run validation
        super().save(*args, **kwargs)
    
    def __str__(self):
        """String representation of the test bank."""
        return self.title
    
    
    def get_absolute_url(self):
        """Get URL for test bank detail page."""
        return reverse('catalog:testbank_detail', kwargs={'slug': self.slug})
    
    def get_question_count(self):
        """Get total number of active questions in this test bank."""
        return self.questions.filter(is_active=True).count()
    
    def get_user_count(self):
        """Get total number of users who have selected/purchased this test bank."""
        return self.user_accesses.filter(is_active=True).count()
    
    def update_rating(self):
        """Update average rating and total ratings count from user ratings."""
        ratings = self.ratings.all()
        if ratings.exists():
            self.total_ratings = ratings.count()
            self.average_rating = ratings.aggregate(
                avg=models.Avg('rating')
            )['avg'] or 0.00
        else:
            self.total_ratings = 0
            self.average_rating = 0.00
        self.save(update_fields=['average_rating', 'total_ratings'])


class TestBankRating(models.Model):
    """
    TestBankRating model for user ratings of test banks.
    
    Users can rate test banks from 1 to 5 stars.
    Each user can only rate a test bank once (enforced by unique_together).
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='test_bank_ratings',
        verbose_name='User',
        help_text='User who gave the rating'
    )
    
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Test Bank',
        help_text='Test bank being rated'
    )
    
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Rating',
        help_text='Rating from 1 to 5 stars'
    )
    
    review = models.TextField(
        blank=True,
        verbose_name='Review',
        help_text='Optional review text'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for TestBankRating model."""
        verbose_name = 'Test Bank Rating'
        verbose_name_plural = 'Test Bank Ratings'
        unique_together = ['user', 'test_bank']
        ordering = ['-created_at']
    
    def __str__(self):
        """String representation of the rating."""
        return f'{self.user.username} - {self.test_bank.title} - {self.rating} stars'
    
    def save(self, *args, **kwargs):
        """Save rating and update test bank's cached rating fields."""
        super().save(*args, **kwargs)
        self.test_bank.update_rating()
    
    def delete(self, *args, **kwargs):
        """Delete rating and update test bank's cached rating fields."""
        test_bank = self.test_bank
        super().delete(*args, **kwargs)
        test_bank.update_rating()


class Question(models.Model):
    """
    Question model representing individual questions within a test bank.
    
    Questions can be of different types:
    - MCQ single: Multiple choice with one correct answer
    - MCQ multi: Multiple choice with multiple correct answers
    - True/False: Boolean question
    
    Each question has answer options (AnswerOption) and an explanation shown after answering.
    """
    
    # ForeignKey to TestBank - each question belongs to one test bank
    test_bank = models.ForeignKey(
        TestBank,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Test Bank',
        help_text='Test bank this question belongs to'
    )
    
    question_text = models.TextField(
        verbose_name='Question Text',
        help_text='The question content'
    )
    
    # Question type choices
    QUESTION_TYPE_CHOICES = [
        ('mcq_single', 'Multiple Choice (Single Answer)'),
        ('mcq_multi', 'Multiple Choice (Multiple Answers)'),
        ('true_false', 'True/False'),
    ]
    
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='mcq_single',
        verbose_name='Question Type',
        help_text='Type of question'
    )
    
    # Explanation shown to user after answering
    explanation = models.TextField(
        blank=True,
        verbose_name='Explanation',
        help_text='Explanation shown after user answers the question'
    )
    
    # Active flag - only active questions are shown in practice sessions
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active',
        help_text='Whether this question is active'
    )
    
    # Order field for custom ordering of questions
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Order of this question within the test bank'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        """Meta options for Question model."""
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['test_bank', 'is_active']),
        ]
    
    def __str__(self):
        """String representation of the question."""
        return f"{self.test_bank.title} - Question {self.order}"
    
    def get_correct_answers(self):
        """Get all correct answer options for this question."""
        return self.answer_options.filter(is_correct=True)


class AnswerOption(models.Model):
    """
    AnswerOption model representing answer choices for questions.
    
    Each question can have multiple answer options.
    For MCQ single questions, exactly one option should be marked as correct.
    For MCQ multi questions, multiple options can be correct.
    For True/False questions, typically two options (True/False).
    
    The order field allows custom ordering of options.
    """
    
    # ForeignKey to Question - each answer option belongs to one question
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answer_options',
        verbose_name='Question',
        help_text='Question this answer option belongs to'
    )
    
    option_text = models.CharField(
        max_length=500,
        verbose_name='Option Text',
        help_text='The text of this answer option'
    )
    
    # Boolean flag indicating if this option is correct
    is_correct = models.BooleanField(
        default=False,
        verbose_name='Is Correct',
        help_text='Whether this answer option is correct'
    )
    
    # Order field for custom ordering of options
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order',
        help_text='Order of this option within the question'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    class Meta:
        """Meta options for AnswerOption model."""
        verbose_name = 'Answer Option'
        verbose_name_plural = 'Answer Options'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        """String representation of the answer option."""
        return f"{self.question} - Option {self.order}: {self.option_text[:50]}"
